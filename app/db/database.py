import asyncio
import logging
import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)
_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool

    for attempt in range(5):
        try:
            _pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            await _run_migrations()
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt == 4:
                logger.error("Final database connection attempt failed")
                raise
            await asyncio.sleep(2)


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised. Was init_db() called?")
    return _pool


async def _run_migrations() -> None:
    migrations = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email       TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'customer',
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS user_addresses (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            label       TEXT NOT NULL, -- e.g. 'Home', 'Work'
            address     TEXT NOT NULL,
            is_default  BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_addresses_user_id ON user_addresses(user_id);
        """,
    ]
    async with get_pool().acquire() as conn:
        for sql in migrations:
            await conn.execute(sql)
