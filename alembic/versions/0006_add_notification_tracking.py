"""Record successful Telegram notifications."""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("notified_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("notified_at")
