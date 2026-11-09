"""真实注册、登录和普通用户权限边界。"""

import os
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from yuxi.storage.postgres.models_business import Department, OperationLog, User


@pytest.mark.asyncio
@pytest.mark.integration
async def test_public_registration_login_and_permissions():
    uid = "regtest_" + uuid4().hex[:10]
    password = "Test!" + uuid4().hex
    engine = create_async_engine(os.environ["POSTGRES_URL"])
    try:
        async with httpx.AsyncClient(base_url=os.getenv("TEST_BASE_URL", "http://localhost:5050")) as client:
            payload = {"uid": uid, "password": password}
            denied = await client.post("/api/auth/register", json={**payload, "role": "superadmin"})
            assert denied.status_code == 422
            created = await client.post("/api/auth/register", json=payload)
            assert created.status_code == 201, created.text
            assert created.json()["role"] == "user"
            assert created.json()["department_id"] is not None
            duplicate = await client.post("/api/auth/register", json=payload)
            assert duplicate.status_code == 409
            login = await client.post("/api/auth/token", data={"username": uid, "password": password})
            assert login.status_code == 200
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            me = await client.get("/api/auth/me", headers=headers)
            assert me.status_code == 200, me.text
            assert me.json()["role"] == "user"
            admin = await client.post("/api/auth/users", json={"username": uid + "x", "password": password}, headers=headers)
            assert admin.status_code == 403
        factory = async_sessionmaker(engine)
        async with factory() as db:
            user = (await db.execute(select(User).where(User.uid == uid))).scalar_one()
            assert user.password_hash != password
            assert user.role == "user" and user.department_id is not None
            department = (await db.execute(select(Department).where(Department.id == user.department_id))).scalar_one()
            assert department.name == f"个人空间-{uid}"
    finally:
        # 仅清理本用例随机生成的账号，不触及既有用户。
        async with async_sessionmaker(engine)() as db:
            department_id = (await db.execute(select(User.department_id).where(User.uid == uid))).scalar_one_or_none()
            await db.execute(delete(OperationLog).where(OperationLog.user_id.in_(select(User.id).where(User.uid == uid))))
            await db.execute(delete(User).where(User.uid == uid))
            if department_id is not None:
                await db.execute(delete(Department).where(Department.id == department_id))
            await db.commit()
        await engine.dispose()
