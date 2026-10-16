"""Track whether a job has been reviewed."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "jobs",
        sa.Column("seen", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("seen")
