"""Add Base64 image storage

Revision ID: 001
Revises: 
Create Date: 2026-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS to avoid errors
    conn = op.get_bind()
    
    # Create accommodation_images table if not exists
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS accommodation_images (
            id SERIAL PRIMARY KEY,
            accommodation_id INTEGER REFERENCES accommodations(id) ON DELETE CASCADE,
            image_data TEXT NOT NULL,
            image_type VARCHAR(50) NOT NULL,
            filename VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    # Add columns to users table if not exist
    try:
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS profile_picture_data TEXT,
            ADD COLUMN IF NOT EXISTS profile_picture_type VARCHAR(50)
        """))
    except:
        pass
    
    # Drop old images column if exists
    try:
        conn.execute(text("""
            ALTER TABLE accommodations 
            DROP COLUMN IF EXISTS images
        """))
    except:
        pass


def downgrade():
    conn = op.get_bind()
    
    # Drop table if exists
    conn.execute(text("DROP TABLE IF EXISTS accommodation_images"))
    
    # Drop columns if exist
    try:
        conn.execute(text("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS profile_picture_data,
            DROP COLUMN IF EXISTS profile_picture_type
        """))
    except:
        pass
    
    # Recreate old column if needed
    try:
        conn.execute(text("""
            ALTER TABLE accommodations 
            ADD COLUMN IF NOT EXISTS images JSON
        """))
    except:
        pass
