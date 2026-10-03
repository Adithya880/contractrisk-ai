"""
BERT Risk Mapper for Phase 7.1.
Maps the 41 BERT clause types to baseline risk weights and primary risk categories,
applying consistent softmax confidence scaling.
"""

from typing import Dict, Tuple
from src.risk_analysis.models import RiskCategory

# Exact mapping of 41 BERT clause categories to (Base Risk Weight 0-100, RiskCategory)
BERT_CLAUSE_RISK_MAP: Dict[str, Tuple[float, RiskCategory]] = {
    "Uncapped Liability": (95.0, RiskCategory.LIABILITY),
    "Termination For Convenience": (85.0, RiskCategory.TERMINATION),
    "Liquidated Damages": (85.0, RiskCategory.LIABILITY),
    "Non-Compete": (80.0, RiskCategory.NON_COMPETE),
    "Exclusivity": (80.0, RiskCategory.OTHER),
    "Cap On Liability": (75.0, RiskCategory.LIABILITY),
    "Ip Ownership Assignment": (75.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Joint Ip Ownership": (70.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Audit Rights": (70.0, RiskCategory.AUDIT_RIGHTS),
    "Most Favored Nation": (70.0, RiskCategory.PAYMENT_TERMS),
    "Covenant Not To Sue": (70.0, RiskCategory.DISPUTE_RESOLUTION),
    "No-Solicit Of Customers": (65.0, RiskCategory.NON_COMPETE),
    "No-Solicit Of Employees": (65.0, RiskCategory.NON_COMPETE),
    "Change Of Control": (65.0, RiskCategory.MODIFICATION),
    "Irrevocable Or Perpetual License": (65.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Price Restrictions": (60.0, RiskCategory.PAYMENT_TERMS),
    "Revenue/Profit Sharing": (60.0, RiskCategory.PAYMENT_TERMS),
    "Minimum Commitment": (60.0, RiskCategory.PAYMENT_TERMS),
    "Unlimited/All-You-Can-Eat-License": (60.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Notice Period To Terminate Renewal": (55.0, RiskCategory.RENEWAL),
    "Renewal Term": (55.0, RiskCategory.RENEWAL),
    "Post-Termination Services": (50.0, RiskCategory.TERMINATION),
    "Rofr/Rofo/Rofn": (50.0, RiskCategory.OTHER),
    "Source Code Escrow": (50.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Non-Disparagement": (45.0, RiskCategory.CONFIDENTIALITY),
    "Competitive Restriction Exception": (45.0, RiskCategory.NON_COMPETE),
    "Anti-Assignment": (40.0, RiskCategory.MODIFICATION),
    "Non-Transferable License": (40.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Volume Restriction": (40.0, RiskCategory.PAYMENT_TERMS),
    "Warranty Duration": (40.0, RiskCategory.WARRANTY),
    "Insurance": (35.0, RiskCategory.LIABILITY),
    "Affiliate License-Licensee": (30.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Affiliate License-Licensor": (30.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Third Party Beneficiary": (30.0, RiskCategory.OTHER),
    "License Grant": (25.0, RiskCategory.INTELLECTUAL_PROPERTY),
    "Governing Law": (20.0, RiskCategory.GOVERNING_LAW),
    "Expiration Date": (15.0, RiskCategory.TERMINATION),
    "Effective Date": (10.0, RiskCategory.OTHER),
    "Agreement Date": (10.0, RiskCategory.OTHER),
    "Parties": (10.0, RiskCategory.OTHER),
    "Document Name": (5.0, RiskCategory.OTHER),
    "Other": (0.0, RiskCategory.OTHER),
}

DEFAULT_BASE_RISK_WEIGHT = 0.0
DEFAULT_RISK_CATEGORY = RiskCategory.OTHER


class BERTRiskMapper:
    """Mapper converting BERT clause types into scaled risk component scores."""

    def __init__(self, clause_risk_map: Dict[str, Tuple[float, RiskCategory]] = None):
        """Initialize mapper with clause risk mapping."""
        self.risk_map = clause_risk_map if clause_risk_map is not None else BERT_CLAUSE_RISK_MAP

    def get_clause_risk_info(self, clause_type: str) -> Tuple[float, RiskCategory]:
        """Look up base risk weight and primary category for a given clause type."""
        normalized_type = clause_type.strip()
        if normalized_type in self.risk_map:
            return self.risk_map[normalized_type]

        # Case-insensitive search fallback
        for key, val in self.risk_map.items():
            if key.lower() == normalized_type.lower():
                return val

        return (DEFAULT_BASE_RISK_WEIGHT, DEFAULT_RISK_CATEGORY)

    def calculate_bert_component_score(self, clause_type: str, confidence: float) -> float:
        """
        Compute confidence-scaled BERT component score (0.0 to 100.0).

        Args:
            clause_type: Predicted BERT clause label string.
            confidence: Softmax prediction probability (0.0 to 1.0).

        Returns:
            Scaled float score bounded between 0.0 and 100.0.
        """
        base_weight, _ = self.get_clause_risk_info(clause_type)
        clamped_confidence = max(0.0, min(1.0, float(confidence)))
        scaled_score = base_weight * clamped_confidence
        return round(max(0.0, min(100.0, scaled_score)), 2)
