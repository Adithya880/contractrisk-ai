"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-03 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('document_type', sa.String(length=16), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('clause_count', sa.Integer(), nullable=False),
        sa.Column('processing_status', sa.String(length=32), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_document_id'), 'documents', ['document_id'], unique=True)

    # 2. clauses table
    op.create_table(
        'clauses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('clause_id', sa.String(length=128), nullable=False),
        sa.Column('clause_number', sa.String(length=32), nullable=True),
        sa.Column('clause_title', sa.String(length=255), nullable=True),
        sa.Column('clause_text', sa.Text(), nullable=False),
        sa.Column('source_pages', sa.JSON(), nullable=True),
        sa.Column('source_element_ids', sa.JSON(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'clause_id', name='uq_document_clause_id')
    )
    op.create_index(op.f('ix_clauses_clause_id'), 'clauses', ['clause_id'], unique=False)
    op.create_index(op.f('ix_clauses_document_id'), 'clauses', ['document_id'], unique=False)

    # 3. risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('clause_db_id', sa.Integer(), nullable=False),
        sa.Column('risk_category', sa.String(length=64), nullable=False),
        sa.Column('risk_level', sa.String(length=16), nullable=False),
        sa.Column('final_score', sa.Float(), nullable=False),
        sa.Column('bert_score', sa.Float(), nullable=False),
        sa.Column('rule_score', sa.Float(), nullable=False),
        sa.Column('rag_score', sa.Float(), nullable=False),
        sa.Column('llm_score', sa.Float(), nullable=False),
        sa.Column('bert_clause_type', sa.String(length=64), nullable=False),
        sa.Column('bert_confidence', sa.Float(), nullable=False),
        sa.Column('risk_explanation', sa.Text(), nullable=False),
        sa.Column('uncertainty', sa.Text(), nullable=True),
        sa.Column('key_risk_factors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['clause_db_id'], ['clauses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clause_db_id')
    )
    op.create_index(op.f('ix_risk_assessments_clause_db_id'), 'risk_assessments', ['clause_db_id'], unique=True)

    # 4. rule_matches table
    op.create_table(
        'rule_matches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('risk_assessment_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.String(length=128), nullable=False),
        sa.Column('rule_name', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False),
        sa.Column('matched_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['risk_assessment_id'], ['risk_assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rule_matches_risk_assessment_id'), 'rule_matches', ['risk_assessment_id'], unique=False)

    # 5. evidence_citations table
    op.create_table(
        'evidence_citations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('risk_assessment_id', sa.Integer(), nullable=False),
        sa.Column('source_clause_id', sa.String(length=128), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('citation_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['risk_assessment_id'], ['risk_assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_citations_risk_assessment_id'), 'evidence_citations', ['risk_assessment_id'], unique=False)

    # 6. future_scenarios table
    op.create_table(
        'future_scenarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('risk_assessment_id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.String(length=128), nullable=True),
        sa.Column('clause_id', sa.String(length=128), nullable=False),
        sa.Column('scenario_title', sa.String(length=255), nullable=False),
        sa.Column('trigger_condition', sa.Text(), nullable=False),
        sa.Column('scenario_description', sa.Text(), nullable=False),
        sa.Column('possible_consequence', sa.Text(), nullable=False),
        sa.Column('assumptions', sa.JSON(), nullable=True),
        sa.Column('uncertainty', sa.Text(), nullable=False),
        sa.Column('fallback_active', sa.Boolean(), nullable=False),
        sa.Column('disclaimer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['risk_assessment_id'], ['risk_assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('risk_assessment_id')
    )
    op.create_index(op.f('ix_future_scenarios_risk_assessment_id'), 'future_scenarios', ['risk_assessment_id'], unique=True)

    # 7. contract_summaries table
    op.create_table(
        'contract_summaries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=16), nullable=False),
        sa.Column('high_risk_count', sa.Integer(), nullable=False),
        sa.Column('medium_risk_count', sa.Integer(), nullable=False),
        sa.Column('low_risk_count', sa.Integer(), nullable=False),
        sa.Column('clause_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contract_summaries_document_id'), 'contract_summaries', ['document_id'], unique=False)

    # 8. analysis_runs table
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_version', sa.String(length=32), nullable=False),
        sa.Column('model_info', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_runs_document_id'), 'analysis_runs', ['document_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_run_id'), 'analysis_runs', ['run_id'], unique=True)


def downgrade() -> None:
    op.drop_table('analysis_runs')
    op.drop_table('contract_summaries')
    op.drop_table('future_scenarios')
    op.drop_table('evidence_citations')
    op.drop_table('rule_matches')
    op.drop_table('risk_assessments')
    op.drop_table('clauses')
    op.drop_table('documents')
