"""Increase password field size

Revision ID: 962dcb8e2f1c
Revises: d313ad0fd2dc
Create Date: 2025-01-22 13:33:48.058467

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '962dcb8e2f1c'
down_revision = 'd313ad0fd2dc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=150),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=150),
               type_=sa.String(length=512),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.String(length=512),
               type_=mysql.VARCHAR(length=150),
               existing_nullable=False)
        batch_op.alter_column('username',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=150),
               existing_nullable=False)

    # ### end Alembic commands ###
