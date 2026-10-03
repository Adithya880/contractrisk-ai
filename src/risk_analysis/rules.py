"""
Rule definitions and regex patterns for Phase 7.1 Risk Detection.
Contains predefined rules mapped across 16 legal risk domains.
"""

from typing import List, Dict, Any
from src.risk_analysis.models import RiskCategory

RISK_RULES: List[Dict[str, Any]] = [
    # --- LIABILITY ---
    {
        "rule_id": "RULE_LIAB_UNLIMITED",
        "risk_category": RiskCategory.LIABILITY,
        "pattern": r"\b(unlimited\s+liability|without\s+(any\s+)?limitation|shall\s+not\s+be\s+limited|no\s+limitation\s+on\s+liability|no\s+cap\s+on\s+liability|(be\s+)?subject\s+to\s+any\s+cap|subject\s+to\s+no\s+cap)\b",
        "description": "Clause creates or imposes unlimited liability",
        "severity_weight": 95.0,
    },
    {
        "rule_id": "RULE_LIAB_CONSEQUENTIAL_INCLUDE",
        "risk_category": RiskCategory.LIABILITY,
        "pattern": r"\b(liable\s+for\s+(any\s+)?(consequential|incidental|special|punitive|indirect|exemplary)\s+damages)\b",
        "description": "Liability extends to indirect or consequential damages",
        "severity_weight": 85.0,
    },
    {
        "rule_id": "RULE_LIAB_LOW_CAP",
        "risk_category": RiskCategory.LIABILITY,
        "pattern": r"\b(aggregate\s+liability\s+shall\s+not\s+exceed|maximum\s+liability\s+is\s+limited\s+to)\s+(fees\s+paid\s+in\s+the\s+preceding\s+(1|one|3|three)\s+month|dollar|amount\s+paid)\b",
        "description": "Liability cap is extremely restrictive",
        "severity_weight": 70.0,
    },

    # --- INDEMNIFICATION ---
    {
        "rule_id": "RULE_INDEM_BROAD",
        "risk_category": RiskCategory.INDEMNIFICATION,
        "pattern": r"\b(defend,?\s*indemnify\s*(and|&)?\s*hold\s*harmless(\s+[\w\s]{1,30})?\s+from\s+(any|all)\b)",
        "description": "Broad indemnification obligation holding party harmless from all claims",
        "severity_weight": 85.0,
    },
    {
        "rule_id": "RULE_INDEM_UNILATERAL",
        "risk_category": RiskCategory.INDEMNIFICATION,
        "pattern": r"\b(customer|vendor|licensee|contractor)\s+(shall|agrees\s+to)\s+indemnify\s+(company|licensor|provider)\b",
        "description": "Unilateral indemnification burden",
        "severity_weight": 75.0,
    },

    # --- TERMINATION ---
    {
        "rule_id": "RULE_TERM_CONVENIENCE_UNILATERAL",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": r"\b(terminate\s+(this\s+agreement\s+)?for\s+convenience|terminate\s+at\s+any\s+time\s+without\s+(cause|reason))\b",
        "description": "Termination for convenience allowed without cause",
        "severity_weight": 80.0,
    },
    {
        "rule_id": "RULE_TERM_SHORT_NOTICE",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": r"\b(written\s+notice\s+of\s+)(less\s+than\s+(14|7)\s+days|immediate\s+termination|0\s+days)\b",
        "description": "Abnormally short notice period for termination",
        "severity_weight": 85.0,
    },
    {
        "rule_id": "RULE_TERM_ACCELERATE_FEES",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": r"\b(upon\s+termination.*all\s+remaining\s+fees.*immediately\s+due|accelerate\s+all\s+future\s+payments)\b",
        "description": "Termination accelerates payment of unexpired term fees",
        "severity_weight": 90.0,
    },

    # --- PAYMENT TERMS ---
    {
        "rule_id": "RULE_PAYMENT_NON_REFUNDABLE",
        "risk_category": RiskCategory.PAYMENT_TERMS,
        "pattern": r"\b(strictly\s+non-refundable|all\s+fees\s+paid\s+are\s+nonrefundable|no\s+refunds\s+(shall|will)\s+be\s+issued)\b",
        "description": "Payments are strictly non-refundable under all circumstances",
        "severity_weight": 70.0,
    },
    {
        "rule_id": "RULE_PAYMENT_HIGH_INTEREST",
        "risk_category": RiskCategory.PAYMENT_TERMS,
        "pattern": r"\b(late\s+payment.*interest.*(1\.5%|2%|18%|24%|compounded\s+daily))\b",
        "description": "Excessive late payment interest rates or daily compounding penalties",
        "severity_weight": 75.0,
    },

    # --- INTELLECTUAL PROPERTY ---
    {
        "rule_id": "RULE_IP_ASSIGNMENT_BROAD",
        "risk_category": RiskCategory.INTELLECTUAL_PROPERTY,
        "pattern": r"\b(hereby\s+assigns?\s+all\s+right,?\s+title,?\s+and\s+interest\s+in\s+(and\s+to\s+)?all|work\s+made\s+for\s+hire)\b",
        "description": "Broad assignment of intellectual property rights and work product",
        "severity_weight": 85.0,
    },
    {
        "rule_id": "RULE_IP_EXCLUSIVE_LICENSE",
        "risk_category": RiskCategory.INTELLECTUAL_PROPERTY,
        "pattern": r"\b(grant.*exclusive,?\s+perpetual,?\s+irrevocable,?\s+worldwide,?\s+royalty-free\s+license)\b",
        "description": "Grants exclusive, perpetual, and irrevocable IP license",
        "severity_weight": 75.0,
    },

    # --- MODIFICATION ---
    {
        "rule_id": "RULE_MOD_UNILATERAL",
        "risk_category": RiskCategory.MODIFICATION,
        "pattern": r"\b(reserves?\s+the\s+right\s+to\s+(modify|amend|update|change)\s+terms.*in\s+its?\s+sole\s+discretion|without\s+prior\s+notice)\b",
        "description": "Unilateral right to modify terms at sole discretion without notice",
        "severity_weight": 85.0,
    },

    # --- RENEWAL ---
    {
        "rule_id": "RULE_RENEWAL_AUTO",
        "risk_category": RiskCategory.RENEWAL,
        "pattern": r"\b(automatically\s+renew|auto-renewal|shall\s+renew\s+for\s+successive\s+terms)\b",
        "description": "Automatic renewal clause",
        "severity_weight": 60.0,
    },

    # --- NON-COMPETE ---
    {
        "rule_id": "RULE_NON_COMPETE_RESTRICT",
        "risk_category": RiskCategory.NON_COMPETE,
        "pattern": r"\b(shall\s+not\s+(directly\s+or\s+indirectly\s+)?(compete|solicit|engage\s+in\s+any\s+competing\s+business))\b",
        "description": "Restrictive non-compete or non-solicitation covenant",
        "severity_weight": 85.0,
    },

    # --- AUDIT RIGHTS ---
    {
        "rule_id": "RULE_AUDIT_UNLIMITED",
        "risk_category": RiskCategory.AUDIT_RIGHTS,
        "pattern": r"\b(right\s+to\s+(audit|inspect)\s+books,?\s+records.*at\s+any\s+time|without\s+prior\s+written\s+notice)\b",
        "description": "Unrestricted right to audit premises or records without notice",
        "severity_weight": 75.0,
    },

    # --- WARRANTY ---
    {
        "rule_id": "RULE_WARRANTY_DISCLAIMER",
        "risk_category": RiskCategory.WARRANTY,
        "pattern": r"\b(provided\s+\"as\s+is\"|disclaims?\s+all\s+(statutory,?\s*)?(warranties|conditions)|without\s+warrant(y|ies)\s+of\s+any\s+kind|no\s+warrant(y|ies)\s+(express\s+or\s+implied|of\s+any\s+kind|is\s+given|is\s+made)|disclaims?\s+any\s+implied\s+warrant(y|ies)\s+of\s+(merchantability|fitness)|(disclaim|exclude|limit)\s+all\s+(express\s+or\s+implied\s+)?(warranties|conditions))\b",
        "description": "Disclaimer of all express or implied warranties",
        "severity_weight": 70.0,
    },
    {
        "rule_id": "RULE_PRICE_UNILATERAL_ALTERATION",
        "risk_category": RiskCategory.PAYMENT_TERMS,
        "pattern": r"\b(prices?\s+quoted\s+are\s+subject\s+to\s+(alteration|change|increase)\s+without\s+notice|unilaterally\s+(adjust|increase)\s+prices?|change\s+prices?\s+at\s+any\s+time)\b",
        "description": "Unilateral right to alter or increase prices without prior notice",
        "severity_weight": 70.0,
    },
    {
        "rule_id": "RULE_TERM_NO_NOTICE",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": r"\b(terminate\s+(this\s+agreement\s+|the\s+services\s+)?(immediately\s+)?without\s+(prior\s+)?(notice|refund)|terminate\s+without\s+(notice|refund)|forfeit(ure)?\s+of\s+(prepaid\s+)?fees?)\b",
        "description": "Immediate termination without notice or refund of fees upon breach/trigger",
        "severity_weight": 80.0,
    },
    {
        "rule_id": "RULE_SUSPENSION_LATE_PAYMENT",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": r"\b(suspend\s+(or\s+terminate\s+)?(services?|access|deliveries|accounts?)(\s+(and|or)\s+(access|services?|deliveries|accounts?))?(\s+immediately)?\s+(following|upon|for|in\s+the\s+event\s+of)\s+((overdue|late|non-)\s*)?payment)\b",
        "description": "Suspension or termination of services/deliveries following overdue payment",
        "severity_weight": 70.0,
    },
    {
        "rule_id": "RULE_REINSTATEMENT_CONDITIONAL",
        "risk_category": RiskCategory.MODIFICATION,
        "pattern": r"\b(reinstatement.*(require|subject\s+to).*approval|(reinstatement|reactivation)\s+fee|subject\s+to\s+new\s+terms|different\s+commercial\s+terms)\b",
        "description": "Reinstatement of service subject to approval, new fees, or updated terms",
        "severity_weight": 65.0,
    },

    # --- DISPUTE RESOLUTION ---
    {
        "rule_id": "RULE_DISPUTE_WAIVER",
        "risk_category": RiskCategory.DISPUTE_RESOLUTION,
        "pattern": r"\b(waives?\s+(any\s+)?right\s+to\s+(a\s+jury\s+trial|class\s+action)|exclusive\s+arbitration)\b",
        "description": "Waiver of jury trial or class action rights",
        "severity_weight": 75.0,
    },

    # --- DATA PRIVACY ---
    {
        "rule_id": "RULE_PRIVACY_UNRESTRICTED",
        "risk_category": RiskCategory.DATA_PRIVACY,
        "pattern": r"\b(right\s+to\s+(sell|share|transfer|process)\s+personal\s+data.*without\s+consent|third-party\s+marketing)\b",
        "description": "Unrestricted processing or sharing of personal data",
        "severity_weight": 85.0,
    },
]
