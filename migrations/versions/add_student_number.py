"""add student_number to users

Revision ID: add_student_number
Revises: 
Create Date: 2026-02-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_student_number'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add student_number column to users table
    op.add_column('users', sa.Column('student_number', sa.String(length=8), nullable=True))
    op.add_column('users', sa.Column('id_number', sa.String(length=13), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('profile_picture_data', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('profile_picture_type', sa.String(length=50), nullable=True))
    
    # Create unique constraints
    op.create_unique_constraint('uq_users_student_number', 'users', ['student_number'])
    op.create_unique_constraint('uq_users_id_number', 'users', ['id_number'])
    
    # If existing data exists, you may need to handle nulls first or set defaults
    # For now, making nullable=True to allow migration


def downgrade():
    op.drop_column('users', 'profile_picture_type')
    op.drop_column('users', 'profile_picture_data')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'id_number')
    op.drop_column('users', 'student_number')