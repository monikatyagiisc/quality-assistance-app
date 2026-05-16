import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv


def get_alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    load_dotenv(backend_root / ".env")
    return Config(str(backend_root / "alembic.ini"))


def upgrade_head() -> None:
    command.upgrade(get_alembic_config(), "head")


async def run_migrations() -> None:
    await asyncio.to_thread(upgrade_head)
