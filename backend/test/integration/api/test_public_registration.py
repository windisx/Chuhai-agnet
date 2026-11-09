"""真实注册、登录和超级管理员权限。"""

import os
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock

from yuxi.services.registration_service import promote_self_registered_users
from yuxi.repositories.user_repository import UserRepository
from yuxi.storage.postgres.models_business import Department, OperationLog, User


@pytest.mark.asyncio
@pytest.mark.integration
async def test_public_registration_login_and_permissions():
    uid = "regtest_" + uuid4().hex[:10]
    password = "Test!" + uuid4().hex
    engine = create_async_engine(os.environ["POSTGRES_URL"])
    uploaded = None
    try:
        async with httpx.AsyncClient(base_url=os.getenv("TEST_BASE_URL", "http://localhost:5050")) as client:
            payload = {"uid": uid, "password": password}
            denied = await client.post("/api/auth/register", json={**payload, "role": "superadmin"})
            assert denied.status_code == 422
            created = await client.post("/api/auth/register", json=payload)
            assert created.status_code == 201, created.text
            assert created.json()["role"] == "superadmin"
            assert created.json()["department_id"] is not None
            duplicate = await client.post("/api/auth/register", json=payload)
            assert duplicate.status_code == 409
            login = await client.post("/api/auth/token", data={"username": uid, "password": password})
            assert login.status_code == 200
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            me = await client.get("/api/auth/me", headers=headers)
            assert me.status_code == 200, me.text
            assert me.json()["role"] == "superadmin"
            knowledge = await client.get("/api/knowledge/databases", headers=headers)
            assert knowledge.status_code == 200, knowledge.text
            upload = await client.post("/api/knowledge/files/upload", files={"file": (uid + ".txt", uid.encode(), "text/plain")}, headers=headers)
            assert upload.status_code == 200, upload.text
            uploaded = upload.json()
            denied = await client.get("/api/departments/" + str(created.json()["department_id"]), headers=headers)
            assert denied.status_code == 200, denied.text
        factory = async_sessionmaker(engine)
        async with factory() as db:
            user = (await db.execute(select(User).where(User.uid == uid))).scalar_one()
            assert user.password_hash != password
            assert user.role == "superadmin" and user.department_id is not None
            department = (await db.execute(select(Department).where(Department.id == user.department_id))).scalar_one()
            assert department.name == f"个人空间-{uid}"
    finally:
        if uploaded:
            from yuxi.storage.minio.client import get_minio_client

            assert await get_minio_client().adelete_file(uploaded['bucket_name'], uploaded['object_name'])
        # 仅清理本用例随机生成的账号，不触及既有用户。
        async with async_sessionmaker(engine)() as db:
            department_id = (await db.execute(select(User.department_id).where(User.uid == uid))).scalar_one_or_none()
            await db.execute(delete(OperationLog).where(OperationLog.user_id.in_(select(User.id).where(User.uid == uid))))
            await db.execute(delete(User).where(User.uid == uid))
            if department_id is not None:
                await db.execute(delete(Department).where(Department.id == department_id))
            await db.commit()
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_legacy_registration_upgrade_scope_rollback_and_repeat(monkeypatch):
    """真实PG验证升级筛选、审计失败回滚与重复执行。"""
    engine = create_async_engine(os.environ["POSTGRES_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = uuid4().hex[:8]
    names = [f"upg_{suffix}_{kind}" for kind in ("eligible", "manual", "moved", "deleted", "audit", "admin", "manualadmin")]
    departments = []

    class ScopedRepository(UserRepository):
        """执行真实候选查询，仅允许测试服务修改本用例账号。"""

        async def list_legacy_self_registered_users(self):
            candidates = await super().list_legacy_self_registered_users()
            return [user for user in candidates if user.uid in names]

    monkeypatch.setattr("yuxi.services.registration_service.UserRepository", ScopedRepository)
    try:
        async with factory() as db:
            for uid in names:
                kind = uid.rsplit("_", 1)[1]
                department = Department(
                    name=("已迁移-" if kind == "moved" else "个人空间-") + uid,
                    description="自助注册账号的独立空间",
                )
                db.add(department)
                await db.flush()
                departments.append(department.id)
                user = User(
                    uid=uid, username=uid, password_hash="unused-test-hash",
                    role="admin" if kind in ("admin", "manualadmin") else "user",
                    department_id=department.id, is_deleted=1 if kind == "deleted" else 0,
                )
                db.add(user)
                await db.flush()
                if kind not in ("manual", "manualadmin"):
                    db.add(OperationLog(
                        user_id=user.id, operation="用户注册",
                        details=("其他注册来源" if kind == "audit" else "访客注册个人空间管理员账户" if kind == "admin" else "访客注册普通用户账户"),
                    ))
            await db.commit()

        async with factory() as db:
            with monkeypatch.context() as patcher:
                patcher.setattr("yuxi.services.registration_service.log_operation", AsyncMock(side_effect=RuntimeError("audit failure")))
                with pytest.raises(RuntimeError, match="audit failure"):
                    await promote_self_registered_users(db)
            roles = dict((await db.execute(select(User.uid, User.role).where(User.uid.in_(names)))).all())
            assert roles[names[0]] == "user"
            assert await promote_self_registered_users(db) == 2
            assert await promote_self_registered_users(db) == 0
            roles = dict((await db.execute(select(User.uid, User.role).where(User.uid.in_(names)))).all())
            assert roles == {uid: "superadmin" if uid in (names[0], names[-2]) else "admin" if uid == names[-1] else "user" for uid in names}
    finally:
        async with factory() as db:
            await db.execute(delete(OperationLog).where(OperationLog.user_id.in_(select(User.id).where(User.uid.in_(names)))))
            await db.execute(delete(User).where(User.uid.in_(names)))
            if departments:
                await db.execute(delete(Department).where(Department.id.in_(departments)))
            await db.commit()
        await engine.dispose()
