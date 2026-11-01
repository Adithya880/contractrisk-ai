"""
Unit tests for BERTClausePredictor inference wrapper.
"""

import pytest
from src.models.bert_predictor import get_bert_predictor, BERTClausePredictor


@pytest.fixture(scope="module")
def predictor():
    return get_bert_predictor()


def test_bert_predictor_initialization(predictor):
    assert isinstance(predictor, BERTClausePredictor)
    assert predictor.num_labels == 41
    assert len(predictor.id2label) == 41


def test_bert_predict_single_clause(predictor):
    text = "This Agreement shall be governed by and construed in accordance with the laws of the State of New York."
    label, confidence = predictor.predict_clause(text)
    assert isinstance(label, str)
    assert label == "Governing Law"
    assert 0.0 <= confidence <= 1.0


def test_bert_predict_batch_clauses(predictor):
    clauses = [
        "In no event shall either party be liable for indirect, incidental, or consequential damages.",
        "Either party may terminate this agreement at any time upon thirty days written notice.",
        "The Executive shall not engage in any competitive business activity for a period of one year."
    ]
    results = predictor.predict_clauses_batch(clauses, batch_size=2)
    assert len(results) == 3
    for label, conf in results:
        assert isinstance(label, str)
        assert 0.0 <= conf <= 1.0
        assert label in predictor.label2id


def test_bert_predict_empty_clause(predictor):
    label, confidence = predictor.predict_clause("")
    assert label == "Other"
    assert confidence == 0.0

    label_ws, conf_ws = predictor.predict_clause("   ")
    assert label_ws == "Other"
    assert conf_ws == 0.0
