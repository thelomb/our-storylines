"""empty message

Revision ID: 9079d910b3f5
Revises: 8c1279214849
Create Date: 2019-03-12 10:04:56.339050

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9079d910b3f5'
down_revision = '8c1279214849'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('geo_point', sa.Column('itinerary_end_id', sa.Integer(), nullable=True))
    op.add_column('geo_point', sa.Column('itinerary_start_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'geo_point', 'itinerary', ['itinerary_end_id'], ['id'])
    op.create_foreign_key(None, 'geo_point', 'itinerary', ['itinerary_start_id'], ['id'])
    op.drop_constraint('itinerary_ibfk_1', 'itinerary', type_='foreignkey')
    op.drop_constraint('itinerary_ibfk_2', 'itinerary', type_='foreignkey')
    op.drop_column('itinerary', 'starting_point')
    op.drop_column('itinerary', 'end_point')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('itinerary', sa.Column('end_point', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('itinerary', sa.Column('starting_point', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('itinerary_ibfk_2', 'itinerary', 'geo_point', ['end_point'], ['id'])
    op.create_foreign_key('itinerary_ibfk_1', 'itinerary', 'geo_point', ['starting_point'], ['id'])
    op.drop_constraint(None, 'geo_point', type_='foreignkey')
    op.drop_constraint(None, 'geo_point', type_='foreignkey')
    op.drop_column('geo_point', 'itinerary_start_id')
    op.drop_column('geo_point', 'itinerary_end_id')
    # ### end Alembic commands ###