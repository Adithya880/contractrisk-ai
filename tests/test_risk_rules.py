"""
Unit tests for RuleEngine and pattern matching in Phase 7.1.
"""

import pytest
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.models import RiskCategory


@pytest.fixture
def engine():
    return RuleEngine()


def test_rule_engine_init(engine):
    assert len(engine.compiled_rules) > 10


def test_unlimited_liability_match(engine):
    clause = "Under no circumstances shall Vendor have any unlimited liability for breaches of contract."
    matches = engine.analyze_clause(clause)
    assert len(matches) >= 1
    match_ids = [m.rule_id for m in matches]
    assert "RULE_LIAB_UNLIMITED" in match_ids
    matched_rule = next(m for m in matches if m.rule_id == "RULE_LIAB_UNLIMITED")
    assert matched_rule.severity_weight == 95.0
    assert matched_rule.risk_category == RiskCategory.LIABILITY


def test_broad_indemnification_match(engine):
    clause = "Customer agrees to defend, indemnify and hold harmless Licensor from all claims, damages, and costs."
    matches = engine.analyze_clause(clause)
    assert len(matches) >= 1
    match_ids = [m.rule_id for m in matches]
    assert "RULE_INDEM_BROAD" in match_ids or "RULE_INDEM_UNILATERAL" in match_ids


def test_termination_convenience_match(engine):
    clause = "Either party may terminate this agreement for convenience upon 30 days prior written notice."
    matches = engine.analyze_clause(clause)
    assert any(m.rule_id == "RULE_TERM_CONVENIENCE_UNILATERAL" for m in matches)


def test_unilateral_modification_match(engine):
    clause = "Company reserves the right to modify terms at any time in its sole discretion without prior notice."
    matches = engine.analyze_clause(clause)
    assert any(m.rule_id == "RULE_MOD_UNILATERAL" for m in matches)


def test_empty_clause_returns_no_matches(engine):
    assert engine.analyze_clause("") == []
    assert engine.analyze_clause("   ") == []


def test_no_false_positive_benign_text(engine):
    clause = "This Agreement shall be effective on January 1, 2026."
    matches = engine.analyze_clause(clause)
    assert len(matches) == 0
