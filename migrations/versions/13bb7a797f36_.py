"""empty message

Revision ID: 13bb7a797f36
Revises: 197860721a90
Create Date: 2019-03-25 14:27:50.668809

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13bb7a797f36'
down_revision = '197860721a90'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('itinerary', sa.Column('story_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'itinerary', 'story', ['story_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'itinerary', type_='foreignkey')
    op.drop_column('itinerary', 'story_id')
    # ### end Alembic commands ###