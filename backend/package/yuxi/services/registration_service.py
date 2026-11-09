"""访客注册个人空间管理员的事务边界。"""

import asyncio
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from yuxi.repositories.department_repository import DepartmentRepository
from yuxi.repositories.user_repository import UserRepository
from yuxi.services.operation_log_service import log_operation
from yuxi.storage.redis import get_async_redis_client
from yuxi.storage.postgres.models_business import User
from yuxi.utils.auth_utils import AuthUtils


@dataclass
class RegistrationError(Exception):
    """注册失败及可向访客展示的原因。"""

    message: str
    status_code: int
    retry_after: int | None = None


async def register_public_user(db: AsyncSession, *, uid: str, password: str, client_ip: str) -> User:
    """限速后原子创建独立个人部门与管理员，冲突时回滚。"""
    redis = await get_async_redis_client()
    # 使用连接来源限速，不信任访客自带的X-Forwarded-For。
    count, ttl = await redis.eval(
        "local n=redis.call('INCR',KEYS[1]); "
        "if n==1 then redis.call('EXPIRE',KEYS[1],600) end; "
        "return {n,redis.call('TTL',KEYS[1])}",
        1,
        f"chuhai:registration:{client_ip}",
    )
    if count > 5:
        raise RegistrationError("注册操作过于频繁，请稍后重试", 429, max(1, ttl))

    repo = UserRepository(db)
    if await repo.is_first_run():
        raise RegistrationError("系统尚未初始化，请先由管理员完成初始化", 409)

    password_hash = await asyncio.to_thread(AuthUtils.hash_password, password)
    try:
        department = await DepartmentRepository(db).create(
            {"name": f"个人空间-{uid}", "description": "自助注册账号的独立空间"}
        )
        user = await repo.create(
            {
                "uid": uid,
                "username": uid,
                "password_hash": password_hash,
                "role": "admin",
                "department_id": department.id,
                "phone_number": None,
            }
        )
        await log_operation(db, user.id, "用户注册", "访客注册个人空间管理员账户")
        await db.commit()
        return user
    except IntegrityError as exc:
        await db.rollback()
        raise RegistrationError("该账号已被使用，请更换账号", 409) from exc
    except Exception:
        await db.rollback()
        raise


async def promote_self_registered_users(db: AsyncSession) -> int:
    """仅升级带旧版注册审计且匹配独立空间的普通账号。"""
    repo = UserRepository(db)
    try:
        users = await repo.list_legacy_self_registered_users()
        for user in users:
            user.role = "admin"
            await repo.save(user)
            await log_operation(db, user.id, "注册账号权限升级", "按用户要求升级为个人空间管理员")
        await db.commit()
        return len(users)
    except Exception:
        await db.rollback()
        raise
