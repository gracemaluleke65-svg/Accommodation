"""Add Base64 image storage

Revision ID: 001
Revises: 
Create Date: 2026-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create accommodation_images table
    op.create_table('accommodation_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('accommodation_id', sa.Integer(), nullable=False),
        sa.Column('image_data', sa.Text(), nullable=False),
        sa.Column('image_type', sa.String(length=50), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['accommodation_id'], ['accommodations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add profile picture columns to users table (if not exists)
    try:
        op.add_column('users', sa.Column('profile_picture_data', sa.Text(), nullable=True))
        op.add_column('users', sa.Column('profile_picture_type', sa.String(length=50), nullable=True))
    except:
        pass  # Columns may already exist
    
    # Drop old images column from accommodations (data will be lost - expected)
    try:
        op.drop_column('accommodations', 'images')
    except:
        pass  # Column may not exist


def downgrade():
    op.drop_table('accommodation_images')
    try:
        op.drop_column('users', 'profile_picture_data')
        op.drop_column('users', 'profile_picture_type')
    except:
        pass
    try:
        op.add_column('accommodations', sa.Column('images', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    except:
        pass
