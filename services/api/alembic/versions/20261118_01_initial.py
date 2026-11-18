"""initial CareQA operational schema

Revision ID: 20261118_01
Revises:
Create Date: 2026-11-18
"""
from alembic import op

from app.database import Base
import app.models  # noqa: F401

revision = "20261118_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)


