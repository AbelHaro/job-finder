"""Use a persisted match score to track ranking progress."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("match_score", sa.Float(), nullable=True))
        batch_op.create_check_constraint(
            "ck_jobs_match_score", "match_score >= 0 AND match_score <= 1"
        )
        batch_op.drop_column("seen")


def downgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(
            sa.Column("seen", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.drop_constraint("ck_jobs_match_score", type_="check")
        batch_op.drop_column("match_score")
