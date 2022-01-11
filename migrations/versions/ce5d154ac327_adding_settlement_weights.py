"""adding settlement weights

Revision ID: ce5d154ac327
Revises: 4dcc08f4c3e1
Create Date: 2022-01-11 14:54:45.840180

"""
from alembic import op
import sqlalchemy as sa
from flaskapp import fetch_data


# revision identifiers, used by Alembic.
revision = 'ce5d154ac327'
down_revision = '4dcc08f4c3e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    settlement_weights = op.create_table('settlement_weights',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transit_mode', sa.String(), nullable=True),
    sa.Column('settlement_type', sa.String(), nullable=True),
    sa.Column('settlement_weight', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###

    op.bulk_insert(settlement_weights, fetch_data.fetch_weights("CSVfiles/weights.csv"))


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('settlement_weights')
    # ### end Alembic commands ###