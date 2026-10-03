"""
ContractRisk AI - Phase 5 Clause Segmentation Package
"""

from src.clause_segmentation.hierarchy import HierarchyTracker
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.clause_segmentation.patterns import HeaderMatch, detect_clause_header
from src.clause_segmentation.segmenter import ClauseSegmenter

__all__ = [
    "ClauseSegmenter",
    "SegmentedClause",
    "SegmentationResult",
    "HeaderMatch",
    "detect_clause_header",
    "HierarchyTracker",
]
