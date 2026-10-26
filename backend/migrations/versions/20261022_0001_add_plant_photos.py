"""Add plant photo metadata while preserving existing plant records.

Revision ID: 20261022_0001
Revises:
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261022_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(inspect(bind).get_table_names())

    # Existing installations already have plants. Create it for a fresh database.
    if "plants" not in existing_tables:
        op.create_table(
            "plants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("species", sa.String(length=150), nullable=False),
            sa.Column("location", sa.String(length=100), nullable=False),
            sa.Column("date_acquired", sa.Date(), nullable=False),
        )

    if "plant_photos" not in existing_tables:
        op.create_table(
            "plant_photos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("plant_id", sa.Integer(), nullable=False),
            sa.Column("storage_key", sa.String(length=80), nullable=False, unique=True),
            sa.Column("content_type", sa.String(length=32), nullable=False),
            sa.Column("date_taken", sa.Date(), nullable=False),
            sa.Column("caption", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["plant_id"], ["plants.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_plant_photos_plant_id", "plant_photos", ["plant_id"])


def downgrade() -> None:
    op.drop_index("ix_plant_photos_plant_id", table_name="plant_photos")
    op.drop_table("plant_photos")
    # Do not drop plants here: this baseline supports already-populated databases.
