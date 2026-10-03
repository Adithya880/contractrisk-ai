"""
Hierarchy Tracking Module for Contract Risk AI

Resolves structural hierarchy levels (1-based depth) and maintains a stack to track
parent clause numbers across nested contract sections.
"""

from typing import Optional, Tuple


class HierarchyTracker:
    """
    Tracks section hierarchy state during document processing to assign
    hierarchy levels (e.g., 1 for Top Section, 2 for Subclause) and parent clause numbers.
    """

    def __init__(self):
        # Stack storing tuples of (clause_number, hierarchy_level)
        self._stack: list[Tuple[str, int]] = []
        self._last_numeric_clause: Optional[str] = None

    def reset(self) -> None:
        """Resets hierarchy tracking state."""
        self._stack.clear()
        self._last_numeric_clause = None

    def determine_hierarchy(
        self, clause_number: Optional[str], pattern_type: str
    ) -> Tuple[int, Optional[str]]:
        """
        Calculates the 1-based hierarchy level and parent clause number for a given clause.

        Args:
            clause_number: Extracted clause number string (e.g. '1.1', 'ARTICLE I', '(a)', or None).
            pattern_type: Pattern classification ('article', 'section', 'decimal', 'lettered', 'uppercase_heading').

        Returns:
            Tuple of (hierarchy_level: int, parent_clause_number: Optional[str])
        """
        if not clause_number:
            # Unnumbered clause or uppercase heading
            parent = self._get_current_parent(target_level=1)
            return 1, parent

        # 1. ARTICLES and SECTIONS (e.g. ARTICLE I, SECTION 1)
        if pattern_type in ("article", "section"):
            raw_num = clause_number.replace("ARTICLE", "").replace("SECTION", "").strip()
            # If section contains dots like SECTION 2.1
            if "." in raw_num:
                parts = raw_num.split(".")
                level = len(parts)
                parent = self._find_parent_for_level(level)
                self._update_stack(clause_number, level)
                return level, parent
            else:
                self._update_stack(clause_number, 1)
                return 1, None

        # 2. DECIMAL NUMBERING (e.g., "1.", "1.1", "1.1.1", "2.3.4")
        if pattern_type == "decimal":
            clean_num = clause_number.rstrip(".")
            parts = clean_num.split(".")
            level = len(parts)
            parent = self._find_parent_for_level(level)
            self._update_stack(clause_number, level)
            self._last_numeric_clause = clause_number
            return level, parent

        # 3. LETTERED / ROMAN NUMERAL SUBCLAUSES (e.g., "(a)", "(b)", "(i)")
        if pattern_type == "lettered":
            # Parent is the most recent active numeric clause (e.g. "1.1")
            parent = self._last_numeric_clause or self._get_current_parent(target_level=2)
            parent_level = self._get_level_for_number(parent) if parent else 1
            level = parent_level + 1
            return level, parent

        # Default fallback
        return 1, None

    def _update_stack(self, clause_number: str, level: int) -> None:
        """Pops stack elements with level >= current level, then pushes current clause."""
        while self._stack and self._stack[-1][1] >= level:
            self._stack.pop()
        self._stack.append((clause_number, level))

    def _find_parent_for_level(self, level: int) -> Optional[str]:
        """Finds closest ancestor in stack with level < target level."""
        for num, lvl in reversed(self._stack):
            if lvl < level:
                return num
        return None

    def _get_current_parent(self, target_level: int) -> Optional[str]:
        """Returns top of stack if level < target_level."""
        if self._stack and self._stack[-1][1] < target_level:
            return self._stack[-1][0]
        return None

    def _get_level_for_number(self, clause_number: str) -> int:
        """Lookup level for a recorded clause number."""
        for num, lvl in reversed(self._stack):
            if num == clause_number:
                return lvl
        return 1
