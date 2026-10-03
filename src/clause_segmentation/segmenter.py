"""
Main Clause Segmenter Module for ContractRisk AI

Transforms Phase 4 ExtractedDocument instances into structured SegmentedClause objects,
grouping structural elements, detecting legal headers, maintaining hierarchy,
and preserving complete document provenance.
"""

from typing import List, Optional
from src.clause_segmentation.hierarchy import HierarchyTracker
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.clause_segmentation.patterns import HeaderMatch, detect_clause_header
from src.document_processing.models import DocumentElement, ElementType, ExtractedDocument


class ClauseSegmenter:
    """
    Hybrid rule-based segmenter for converting contract document elements into clauses.
    """

    def __init__(self):
        self._hierarchy_tracker = HierarchyTracker()

    def segment(self, document: ExtractedDocument) -> SegmentationResult:
        """
        Segments an ExtractedDocument into an ordered list of SegmentedClause objects.

        Args:
            document: ExtractedDocument produced by Phase 4 DocumentLoader.

        Returns:
            SegmentationResult containing metadata, segmented clauses, and coverage statistics.
        """
        self._hierarchy_tracker.reset()

        if not document.elements:
            return SegmentationResult(
                document_id=document.document_id,
                source_filename=document.source_filename,
                clauses=[],
                total_clauses=0,
                source_character_count=0,
                segmented_character_count=0,
                text_coverage_ratio=1.0,
                unsegmented_elements_count=0,
            )

        # Pre-process elements: identify header/footer repetition noise conservatively
        filtered_elements = self._filter_repetition_noise(document.elements)

        # Expand multi-line/multi-paragraph elements into atomic paragraph units
        atomic_units = self._expand_element_units(filtered_elements)

        clause_blocks: list[dict] = []
        current_block: Optional[dict] = None

        for unit in atomic_units:
            text = unit["text"].strip()
            if not text:
                continue

            header_match = detect_clause_header(text)

            if header_match:
                # If active block exists, finalize it
                if current_block and current_block["text_parts"]:
                    clause_blocks.append(current_block)

                # Determine hierarchy level & parent clause
                level, parent_num = self._hierarchy_tracker.determine_hierarchy(
                    header_match.clause_number, header_match.pattern_type
                )

                pages = [unit["page_number"]] if unit["page_number"] else []

                current_block = {
                    "clause_number": header_match.clause_number,
                    "clause_heading": header_match.clause_heading,
                    "text_parts": [text],  # Preserve exact original text intact
                    "pages": set(pages),
                    "element_ids": [unit["element_id"]],
                    "parent_clause_number": parent_num,
                    "hierarchy_level": level,
                }
            else:
                # Continuation text belonging to the current block
                if current_block is None:
                    # Unnumbered initial block or unnumbered document paragraph
                    level, parent_num = self._hierarchy_tracker.determine_hierarchy(None, "unbound")
                    pages = [unit["page_number"]] if unit["page_number"] else []
                    current_block = {
                        "clause_number": None,
                        "clause_heading": None,
                        "text_parts": [text],
                        "pages": set(pages),
                        "element_ids": [unit["element_id"]],
                        "parent_clause_number": parent_num,
                        "hierarchy_level": level,
                    }
                else:
                    # Append continuation paragraph/table text to active clause
                    current_block["text_parts"].append(text)
                    if unit["page_number"]:
                        current_block["pages"].add(unit["page_number"])
                    if unit["element_id"] not in current_block["element_ids"]:
                        current_block["element_ids"].append(unit["element_id"])

        # Finalize last active block
        if current_block and current_block["text_parts"]:
            clause_blocks.append(current_block)

        # Convert blocks into strongly-typed SegmentedClause models
        segmented_clauses: list[SegmentedClause] = []
        for idx, block in enumerate(clause_blocks, start=1):
            full_clause_text = "\n\n".join(block["text_parts"]).strip()

            sorted_pages = sorted(list(block["pages"])) if block["pages"] else []
            start_page = sorted_pages[0] if sorted_pages else None
            end_page = sorted_pages[-1] if sorted_pages else None

            clause_id = f"{document.document_id}:clause:{idx:03d}"
            words = full_clause_text.split()

            clause = SegmentedClause(
                clause_id=clause_id,
                document_id=document.document_id,
                clause_number=block["clause_number"],
                clause_heading=block["clause_heading"],
                clause_text=full_clause_text,
                source_type=document.source_type,
                source_pages=sorted_pages,
                start_page=start_page,
                end_page=end_page,
                source_element_ids=block["element_ids"],
                parent_clause_number=block["parent_clause_number"],
                hierarchy_level=block["hierarchy_level"],
                character_count=len(full_clause_text),
                word_count=len(words),
            )
            segmented_clauses.append(clause)

        # Calculate Validation & Coverage Statistics
        source_char_count = sum(len(e.text) for e in document.elements if e.text)
        segmented_char_count = sum(c.character_count for c in segmented_clauses)
        coverage_ratio = (
            round(segmented_char_count / max(source_char_count, 1), 4)
            if source_char_count > 0
            else 1.0
        )

        return SegmentationResult(
            document_id=document.document_id,
            source_filename=document.source_filename,
            clauses=segmented_clauses,
            total_clauses=len(segmented_clauses),
            source_character_count=source_char_count,
            segmented_character_count=segmented_char_count,
            text_coverage_ratio=coverage_ratio,
            unsegmented_elements_count=len(document.elements) - sum(len(c.source_element_ids) for c in segmented_clauses),
        )

    def _expand_element_units(self, elements: List[DocumentElement]) -> List[dict]:
        """
        Expands multi-paragraph/multi-line elements into atomic paragraph units,
        preserving page numbers and element IDs.
        """
        units: list[dict] = []
        for elem in elements:
            raw_text = elem.text.strip()
            if not raw_text:
                continue

            paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
            for p in paragraphs:
                units.append({
                    "text": p,
                    "page_number": elem.page_number,
                    "element_id": elem.element_id,
                })
        return units

    def _filter_repetition_noise(
        self, elements: List[DocumentElement]
    ) -> List[DocumentElement]:
        """
        Conservatively filters exact repeating header/footer text (e.g. "Page X of Y")
        occurring on 3+ distinct pages, ensuring core contract text is never discarded.
        """
        page_texts: dict[str, set[int]] = {}
        for elem in elements:
            t = elem.text.strip()
            if t and elem.page_number:
                if t not in page_texts:
                    page_texts[t] = set()
                page_texts[t].add(elem.page_number)

        repetition_patterns = set()
        for t, pages in page_texts.items():
            if len(pages) >= 3 and len(t) <= 30 and ("Page" in t or "page" in t or "CONFIDENTIAL" in t):
                repetition_patterns.add(t)

        if not repetition_patterns:
            return elements

        return [e for e in elements if e.text.strip() not in repetition_patterns]
