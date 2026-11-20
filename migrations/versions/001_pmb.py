from alembic import op
from migration_sql import UP, DOWN

revision = "001_pmb"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    for statement in UP:
        op.execute(statement)

def downgrade():
    for statement in DOWN:
        op.execute(statement)
