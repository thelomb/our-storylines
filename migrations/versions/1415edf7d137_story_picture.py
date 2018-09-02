"""story picture

Revision ID: 1415edf7d137
Revises: f6b11377d5cf
Create Date: 2018-08-31 22:19:58.662552

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1415edf7d137'
down_revision = 'f6b11377d5cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('story', sa.Column('image_filename', sa.String(), nullable=True))
    op.add_column('story', sa.Column('image_url', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('story', 'image_url')
    op.drop_column('story', 'image_filename')
    # ### end Alembic commands ###
