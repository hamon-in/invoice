"""head

Revision ID: 0.3.1-alpha
Revises: 0.2.1-alpha
Create Date: 2017-07-13 17:28:19.599872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0.3.1-alpha'
down_revision = '0.2.1-alpha'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('invoices', sa.Column('disp_number', sa.Integer()))
    op.execute("update invoices set disp_number=id")


def downgrade():
    op.drop_column('invoices', 'disp_number')

