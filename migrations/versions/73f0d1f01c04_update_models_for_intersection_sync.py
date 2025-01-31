"""Update models for intersection sync

Revision ID: 73f0d1f01c04
Revises: 8461d5182465
Create Date: 2025-01-08 14:51:30.057213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73f0d1f01c04'
down_revision = '8461d5182465'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lane_parameter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lane', sa.Integer(), nullable=False),
    sa.Column('straight', sa.Boolean(), nullable=True),
    sa.Column('turn', sa.Boolean(), nullable=True),
    sa.Column('turn_direction', sa.String(length=10), nullable=True),
    sa.Column('camera_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['camera_id'], ['camera.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('measurement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('lane', sa.Integer(), nullable=False),
    sa.Column('vehicles_class_a', sa.Integer(), nullable=True),
    sa.Column('vehicles_class_b', sa.Integer(), nullable=True),
    sa.Column('vehicles_class_c', sa.Integer(), nullable=True),
    sa.Column('average_speed', sa.Float(), nullable=True),
    sa.Column('headway', sa.Float(), nullable=True),
    sa.Column('camera_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['camera_id'], ['camera.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('flow')
    with op.batch_alter_table('camera', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cam_id', sa.String(length=50), nullable=False))
        batch_op.drop_column('code')

    with op.batch_alter_table('intersection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('address', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('province', sa.String(length=50), nullable=False))
        batch_op.add_column(sa.Column('canton', sa.String(length=50), nullable=False))
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.drop_column('code')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('intersection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code', sa.VARCHAR(length=50), nullable=False))
        batch_op.drop_column('user_id')
        batch_op.drop_column('canton')
        batch_op.drop_column('province')
        batch_op.drop_column('address')
        batch_op.drop_column('name')

    with op.batch_alter_table('camera', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code', sa.VARCHAR(length=50), nullable=False))
        batch_op.drop_column('cam_id')

    op.create_table('flow',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('lane', sa.INTEGER(), nullable=False),
    sa.Column('flow_value', sa.FLOAT(), nullable=False),
    sa.Column('camera_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['camera_id'], ['camera.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('measurement')
    op.drop_table('lane_parameter')
    # ### end Alembic commands ###
