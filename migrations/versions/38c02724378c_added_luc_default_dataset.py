"""added LUC default dataset

Revision ID: 38c02724378c
Revises: a56bba9775d0
Create Date: 2022-03-02 21:00:54.927731

"""
from alembic import op
import sqlalchemy as sa
from ggia_app import fetch_data


# revision identifiers, used by Alembic.
revision = '38c02724378c'
down_revision = 'a56bba9775d0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    land_use_default_dataset = op.create_table('land_use_change_default_dataset',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('land_conversion', sa.String(), nullable=True),
    sa.Column('factor_name', sa.String(), nullable=True),
    sa.Column('factor_value', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
    op.bulk_insert(land_use_default_dataset, fetch_data.fetch_land_use_change_factors("CSVfiles/land-use-change-default-dataset.csv"))


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('land_use_change_default_dataset')
    # ### end Alembic commands ###