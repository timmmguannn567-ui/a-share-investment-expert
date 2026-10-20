"""Initial MVP schema.

Revision ID: 20261020_0001
Revises:
"""
from typing import Sequence, Union

from alembic import op

from app.database import Base
from app import models  # noqa: F401

revision: str = "20261020_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # Deliberately non-destructive in a personal finance tool. Remove tables manually only after backup.
    pass

