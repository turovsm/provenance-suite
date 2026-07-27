import pytest
from fakeredis import FakeAsyncRedis

from src.infrastructure.crypto.token_manager import RedisTokenSessionStore


@pytest.fixture()
async def store():
    redis = FakeAsyncRedis(decode_responses=True)
    yield RedisTokenSessionStore(redis)
    await redis.flushall()
    await redis.aclose()


async def test_register_and_validate_refresh_token(store: RedisTokenSessionStore) -> None:
    await store.register_refresh_token(user_id="u1", family_id="fam", jti="j1")
    assert await store.is_refresh_token_valid("fam", "j1") is True


async def test_unknown_token_is_invalid(store: RedisTokenSessionStore) -> None:
    assert await store.is_refresh_token_valid("fam", "missing") is False


async def test_revoke_single_token_leaves_siblings(store: RedisTokenSessionStore) -> None:
    await store.register_refresh_token(user_id="u1", family_id="fam", jti="old")
    await store.register_refresh_token(user_id="u1", family_id="fam", jti="new")

    await store.revoke_refresh_token("fam", "old")

    assert await store.is_refresh_token_valid("fam", "old") is False
    assert await store.is_refresh_token_valid("fam", "new") is True


async def test_invalidate_family_kills_all_members_only(store: RedisTokenSessionStore) -> None:
    await store.register_refresh_token(user_id="u1", family_id="famA", jti="j1")
    await store.register_refresh_token(user_id="u1", family_id="famA", jti="j2")
    await store.register_refresh_token(user_id="u2", family_id="famB", jti="j3")

    await store.invalidate_token_family("famA")

    assert await store.is_refresh_token_valid("famA", "j1") is False
    assert await store.is_refresh_token_valid("famA", "j2") is False
    assert await store.is_refresh_token_valid("famB", "j3") is True


async def test_refresh_token_has_expiry(store: RedisTokenSessionStore) -> None:
    await store.register_refresh_token(user_id="u1", family_id="fam", jti="j1", ttl_days=1)
    ttl = await store._redis.ttl("token:refresh:fam:j1")
    assert 0 < ttl <= 86400


async def test_access_token_blacklist(store: RedisTokenSessionStore) -> None:
    assert await store.is_access_token_blacklisted("a1") is False
    await store.blacklist_access_token("a1", ttl_seconds=60)
    assert await store.is_access_token_blacklisted("a1") is True
    ttl = await store._redis.ttl("token:blacklist:a1")
    assert 0 < ttl <= 60
