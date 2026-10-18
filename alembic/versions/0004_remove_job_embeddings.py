"""Remove embedding storage from jobs."""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("embedding")
        batch_op.drop_column("embedding_model")


def downgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("embedding", sa.JSON(none_as_null=True), nullable=True))
        batch_op.add_column(sa.Column("embedding_model", sa.Text(), nullable=True))
