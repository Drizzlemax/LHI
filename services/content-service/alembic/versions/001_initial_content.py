"""Initial content schema

Revision ID: 001_initial_content
Revises: 
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_content'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contents table
    op.create_table(
        'contents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('education_level', sa.String(length=20), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('storage_key', sa.String(length=500), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('is_premium', sa.Boolean(), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('license_type', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.String(length=2000), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('extraction_status', sa.String(length=50), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('preview_url', sa.String(length=1000), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contents_title', 'contents', ['title'], unique=False)
    op.create_index('ix_contents_category', 'contents', ['category'], unique=False)
    op.create_index('ix_contents_content_type', 'contents', ['content_type'], unique=False)
    op.create_index('ix_contents_status', 'contents', ['status'], unique=False)
    op.create_index('ix_contents_education_level', 'contents', ['education_level'], unique=False)
    op.create_index('ix_contents_owner_id', 'contents', ['owner_id'], unique=False)
    op.create_index('ix_contents_language', 'contents', ['language'], unique=False)
    op.create_index('ix_contents_is_public', 'contents', ['is_public'], unique=False)

    # Create content_metadata table
    op.create_table(
        'content_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('authors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('author_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('editors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('translators', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('illustrators', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('isbn', sa.String(length=20), nullable=True),
        sa.Column('issn', sa.String(length=20), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('subjects', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('license_url', sa.String(length=500), nullable=True),
        sa.Column('rights_holder', sa.String(length=255), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id')
    )
    op.create_index('ix_content_metadata_content_id', 'content_metadata', ['content_id'], unique=True)

    # Create content_vectors table
    op.create_table(
        'content_vectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=True),
        sa.Column('vector', postgresql.JSONB(astext=sa.Text()), nullable=True),
        sa.Column('vector_dimensions', sa.Integer(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_vectors_content_id', 'content_vectors', ['content_id'], unique=False)

    # Create content_versions table
    op.create_table(
        'content_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('storage_key', sa.String(length=500), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('change_type', sa.String(length=20), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_versions_content_id', 'content_versions', ['content_id'], unique=False)

    # Create media_assets table
    op.create_table(
        'media_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('storage_key', sa.String(length=500), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_media_assets_content_id', 'media_assets', ['content_id'], unique=False)
    op.create_index('ix_media_assets_asset_type', 'media_assets', ['asset_type'], unique=False)

    # Create collections table
    op.create_table(
        'collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image_url', sa.String(length=1000), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collections_name', 'collections', ['name'], unique=False)
    op.create_index('ix_collections_owner_id', 'collections', ['owner_id'], unique=False)

    # Create content_collections table (junction)
    op.create_table(
        'content_collections',
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint(['collection_id', 'content_id'])
    )

    # Create learning_paths table
    op.create_table(
        'learning_paths',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image_url', sa.String(length=1000), nullable=True),
        sa.Column('target_education_level', sa.String(length=20), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_paths_title', 'learning_paths', ['title'], unique=False)
    op.create_index('ix_learning_paths_owner_id', 'learning_paths', ['owner_id'], unique=False)

    # Create learning_path_contents table (junction)
    op.create_table(
        'learning_path_contents',
        sa.Column('learning_path_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('min_passing_score', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint(['learning_path_id', 'content_id'])
    )

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_tags_name', 'tags', ['name'], unique=True)


def downgrade() -> None:
    op.drop_table('tags')
    op.drop_table('learning_path_contents')
    op.drop_table('learning_paths')
    op.drop_table('content_collections')
    op.drop_table('collections')
    op.drop_table('media_assets')
    op.drop_table('content_versions')
    op.drop_table('content_vectors')
    op.drop_table('content_metadata')
    op.drop_table('contents')
