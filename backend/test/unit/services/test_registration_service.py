"""注册权限与事务失败的行为测试。"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from server.routers.auth_router import PublicRegistration
from yuxi.services.registration_service import RegistrationError, promote_self_registered_users, register_public_user


@pytest.mark.parametrize("extra", [{"role": "admin"}, {"department_id": 1}, {"phone_number": "13800000000"}])
def test_registration_rejects_privileged_or_unverified_fields(extra):
    with pytest.raises(ValidationError):
        PublicRegistration.model_validate({"uid": "visitor", "password": "password123", **extra})


@pytest.mark.parametrize("uid,password", [("13800000000", "password123"), ("okuser", "short"), ("ab", "password123")])
def test_registration_rejects_invalid_identity(uid, password):
    with pytest.raises(ValidationError):
        PublicRegistration(uid=uid, password=password)


@pytest.mark.asyncio
async def test_registration_fixes_role_and_commits_audit_with_user():
    db, redis, repo = AsyncMock(), AsyncMock(), AsyncMock()
    redis.eval.return_value = [1, 600]
    repo.is_first_run.return_value = False
    with (
        patch("yuxi.services.registration_service.get_async_redis_client", return_value=redis),
        patch("yuxi.services.registration_service.UserRepository", return_value=repo),
        patch("yuxi.services.registration_service.DepartmentRepository") as departments,
        patch("yuxi.services.registration_service.AuthUtils.hash_password", return_value="hashed"),
        patch("yuxi.services.registration_service.log_operation", new_callable=AsyncMock) as log,
    ):
        departments.return_value.create = AsyncMock(return_value=SimpleNamespace(id=123))
        user = await register_public_user(db, uid="visitor", password="password123", client_ip="test")
    values = repo.create.call_args.args[0]
    assert values == {
        "uid": "visitor", "username": "visitor", "password_hash": "hashed",
        "role": "superadmin", "department_id": 123, "phone_number": None,
    }
    assert user is repo.create.return_value
    log.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_registration_conflict_rolls_back_without_success():
    db, redis, repo = AsyncMock(), AsyncMock(), AsyncMock()
    redis.eval.return_value = [1, 600]
    repo.is_first_run.return_value = False
    repo.create.side_effect = IntegrityError("insert", {}, Exception())
    with (
        patch("yuxi.services.registration_service.get_async_redis_client", return_value=redis),
        patch("yuxi.services.registration_service.UserRepository", return_value=repo),
        patch("yuxi.services.registration_service.AuthUtils.hash_password", return_value="hashed"),
        patch("yuxi.services.registration_service.DepartmentRepository") as departments,
    ):
        departments.return_value.create = AsyncMock(return_value=SimpleNamespace(id=123))
        with pytest.raises(RegistrationError) as exc:
            await register_public_user(db, uid="visitor", password="password123", client_ip="test")
    assert exc.value.status_code == 409
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("count,first_run,status", [(6, False, 429), (1, True, 409)])
async def test_registration_refuses_rate_limit_and_uninitialized_system(count, first_run, status):
    db, redis, repo = AsyncMock(), AsyncMock(), AsyncMock()
    redis.eval.return_value = [count, 600]
    repo.is_first_run.return_value = first_run
    with (
        patch("yuxi.services.registration_service.get_async_redis_client", return_value=redis),
        patch("yuxi.services.registration_service.UserRepository", return_value=repo),
    ):
        with pytest.raises(RegistrationError) as exc:
            await register_public_user(db, uid="visitor", password="password123", client_ip="test")
    assert exc.value.status_code == status
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_registration_upgrade_only_processes_repository_candidates():
    db, repo = AsyncMock(), AsyncMock()
    user = SimpleNamespace(id=42, role="user")
    repo.list_legacy_self_registered_users.return_value = [user]
    with (
        patch("yuxi.services.registration_service.UserRepository", return_value=repo),
        patch("yuxi.services.registration_service.log_operation", new_callable=AsyncMock) as log,
    ):
        assert await promote_self_registered_users(db) == 1
    assert user.role == "superadmin"
    repo.save.assert_awaited_once_with(user)
    log.assert_awaited_once()
    db.commit.assert_awaited_once()
