"""
Unit Test Suite for Clause Hierarchy Tracker Module
"""

import pytest
from src.clause_segmentation.hierarchy import HierarchyTracker


def test_top_level_section():
    tracker = HierarchyTracker()
    level, parent = tracker.determine_hierarchy("1.", "decimal")
    assert level == 1
    assert parent is None


def test_nested_decimal_numbering():
    tracker = HierarchyTracker()

    l1, p1 = tracker.determine_hierarchy("1.", "decimal")
    assert l1 == 1 and p1 is None

    l2, p2 = tracker.determine_hierarchy("1.1", "decimal")
    assert l2 == 2 and p2 == "1."

    l3, p3 = tracker.determine_hierarchy("1.1.1", "decimal")
    assert l3 == 3 and p3 == "1.1"

    l4, p4 = tracker.determine_hierarchy("1.2", "decimal")
    assert l4 == 2 and p4 == "1."


def test_lettered_subclause_hierarchy():
    tracker = HierarchyTracker()

    tracker.determine_hierarchy("2.", "decimal")
    tracker.determine_hierarchy("2.1", "decimal")
    l_let, p_let = tracker.determine_hierarchy("(a)", "lettered")

    assert l_let == 3
    assert p_let == "2.1"
