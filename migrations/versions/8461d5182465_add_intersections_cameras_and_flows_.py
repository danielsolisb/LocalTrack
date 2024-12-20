"""Add intersections, cameras, and flows models

Revision ID: 8461d5182465
Revises: cc8196c00d26
Create Date: 2024-12-16 23:11:20.471337

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8461d5182465'
down_revision = 'cc8196c00d26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('intersection',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('coordinates', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('camera',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('ip_address', sa.String(length=50), nullable=False),
    sa.Column('street', sa.String(length=100), nullable=False),
    sa.Column('lanes', sa.Integer(), nullable=False),
    sa.Column('direction', sa.String(length=50), nullable=False),
    sa.Column('intersection_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['intersection_id'], ['intersection.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('flow',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lane', sa.Integer(), nullable=False),
    sa.Column('flow_value', sa.Float(), nullable=False),
    sa.Column('camera_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['camera_id'], ['camera.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('flow')
    op.drop_table('camera')
    op.drop_table('intersection')
    # ### end Alembic commands ###
