"""initial_migration

Revision ID: ea8d3d22f581
Revises: 
Create Date: 2026-08-10 14:40:00.134685

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ea8d3d22f581'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # calls
    op.create_table(
        'calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('call_id', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('audio_path', sa.String(length=1024), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('speaker_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calls_call_id'), 'calls', ['call_id'], unique=True)
    
    # transcript_segments
    op.create_table(
        'transcript_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('call_id', sa.String(length=255), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('speaker_id', sa.String(length=100), nullable=False),
        sa.Column('speaker_role', sa.String(length=100), nullable=True),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['call_id'], ['calls.call_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transcript_segments_call_id', 'transcript_segments', ['call_id'], unique=False)
    op.create_index('ix_transcript_segments_start_time', 'transcript_segments', ['start_time'], unique=False)

    # insights
    op.create_table(
        'insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('call_id', sa.String(length=255), nullable=False),
        sa.Column('parameter', sa.String(length=255), nullable=False),
        sa.Column('result', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['call_id'], ['calls.call_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('call_id', 'parameter', name='uq_insight_call_parameter')
    )

    # insight_evidence
    op.create_table(
        'insight_evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('insight_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.String(length=50), nullable=True),
        sa.Column('speaker', sa.String(length=100), nullable=True),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['insight_id'], ['insights.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['transcript_segments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # workflow_runs
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(length=255), nullable=False),
        sa.Column('call_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_type', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_runs_call_id'), 'workflow_runs', ['call_id'], unique=False)
    op.create_index(op.f('ix_workflow_runs_status'), 'workflow_runs', ['status'], unique=False)
    op.create_index(op.f('ix_workflow_runs_workflow_id'), 'workflow_runs', ['workflow_id'], unique=True)

    # batch_runs
    op.create_table(
        'batch_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('call_id', sa.String(length=255), nullable=False),
        sa.Column('batch_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('call_id', 'batch_id', name='uq_batch_run_call_batch')
    )
    op.create_index(op.f('ix_batch_runs_call_id'), 'batch_runs', ['call_id'], unique=False)
    op.create_index(op.f('ix_batch_runs_batch_id'), 'batch_runs', ['batch_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_batch_runs_batch_id'), table_name='batch_runs')
    op.drop_index(op.f('ix_batch_runs_call_id'), table_name='batch_runs')
    op.drop_table('batch_runs')
    op.drop_index(op.f('ix_workflow_runs_workflow_id'), table_name='workflow_runs')
    op.drop_index(op.f('ix_workflow_runs_status'), table_name='workflow_runs')
    op.drop_index(op.f('ix_workflow_runs_call_id'), table_name='workflow_runs')
    op.drop_table('workflow_runs')
    op.drop_table('insight_evidence')
    op.drop_table('insights')
    op.drop_index('ix_transcript_segments_start_time', table_name='transcript_segments')
    op.drop_index('ix_transcript_segments_call_id', table_name='transcript_segments')
    op.drop_table('transcript_segments')
    op.drop_index(op.f('ix_calls_call_id'), table_name='calls')
    op.drop_table('calls')
