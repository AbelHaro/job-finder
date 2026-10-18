"""Track generated CVs so completed jobs are not regenerated."""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("cv_generated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("jobs", sa.Column("cv_generated_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("cv_path", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("cv_path")
        batch_op.drop_column("cv_generated_at")
        batch_op.drop_column("cv_generated")
