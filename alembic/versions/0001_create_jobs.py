"""Create jobs in SQLite."""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("posted", sa.Date(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("embedding_model", sa.Text(), nullable=True),
        sa.UniqueConstraint("url", name="uq_jobs_url"),
    )


def downgrade():
    op.drop_table("jobs")
