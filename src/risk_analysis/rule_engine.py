"""
Rule Engine for deterministic regex risk detection in contract clauses.
Scans clause text against compiled risk patterns and returns structured match details.
"""

import re
from typing import List, Dict, Any, Optional
from src.risk_analysis.models import RiskRuleMatch, RiskCategory
from src.risk_analysis.rules import RISK_RULES


class RuleEngine:
    """Regex pattern matcher for detecting contract risk indicators."""

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        """Initialize RuleEngine with compiled regex rules."""
        raw_rules = custom_rules if custom_rules is not None else RISK_RULES
        self.compiled_rules = []
        for r in raw_rules:
            pattern_str = r["pattern"]
            compiled = re.compile(pattern_str, re.IGNORECASE)
            self.compiled_rules.append({
                "rule_id": r["rule_id"],
                "risk_category": r["risk_category"],
                "compiled_pattern": compiled,
                "pattern_str": pattern_str,
                "description": r["description"],
                "severity_weight": float(r["severity_weight"])
            })

    def analyze_clause(self, clause_text: str) -> List[RiskRuleMatch]:
        """
        Scan clause text against all compiled risk rules.

        Args:
            clause_text: Full text of the contractual clause.

        Returns:
            List of RiskRuleMatch objects for all triggered rules.
        """
        if not clause_text or not clause_text.strip():
            return []

        # Standalone short uppercase headings (e.g. 'LIMITATION OF LIABILITY') contain no operative terms
        words = clause_text.split()
        if len(words) <= 4 and clause_text.isupper() and not any(p in clause_text for p in [".", ";", ":"]):
            return []

        matches: List[RiskRuleMatch] = []
        seen_rule_ids = set()

        for rule in self.compiled_rules:
            pattern = rule["compiled_pattern"]
            match_obj = pattern.search(clause_text)
            if match_obj:
                rule_id = rule["rule_id"]
                if rule_id in seen_rule_ids:
                    continue

                # Negative preservation check: If clause preserves warranties/remedies rather than disclaiming them
                if rule_id == "RULE_WARRANTY_DISCLAIMER":
                    preservation_match = re.search(
                        r"\b(nothing\s+in.*shall\s+prejudice|shall\s+not\s+prejudice|without\s+prejudice\s+to|preserv(e|ing)\s+(any\s+)?(condition,?\s*warranty|legal\s+remedy))\b",
                        clause_text,
                        re.IGNORECASE
                    )
                    if preservation_match:
                        continue

                seen_rule_ids.add(rule_id)

                matched_str = match_obj.group(0)
                matches.append(RiskRuleMatch(
                    rule_id=rule_id,
                    risk_category=rule["risk_category"],
                    pattern=rule["pattern_str"],
                    description=rule["description"],
                    severity_weight=rule["severity_weight"],
                    matched_text=matched_str
                ))

        return matches
