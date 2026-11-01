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
        "pattern": (
            r"\b(unlimited\s+(?:total\s+|aggregate\s+)?liability|"
            r"(?:total|aggregate|overall|maximum)?\s*liability(?:\s+of\s+[^,;.\n]+?)?\s+(?:shall\s+be|is)\s+(?:unlimited|uncapped|without\s+limit)|"
            r"liability(?:\s+of\s+[^,;.\n]+?)?\s+(?:shall\s+be|is)\s+(?:unlimited|uncapped|without\s+limit)|"
            r"without\s+(?:any\s+)?limitation|shall\s+not\s+be\s+limited|no\s+limitation\s+on\s+liability|"
            r"no\s+cap\s+on\s+liability|subject\s+to\s+no\s+cap)\b"
        ),
        "description": "Clause creates or imposes unlimited liability",
        "severity_weight": 95.0,
    },
    {
        "rule_id": "RULE_LIAB_INTERNAL_CONTRADICTION",
        "risk_category": RiskCategory.LIABILITY,
        "pattern": (
            r"(?s)(?:\b(?:(?:shall\s+)?not\s+(?:be\s+)?liable|neither\s+party(?:\s+shall\s+be)?\s+liable|under\s+no\s+circumstances\s+shall(?:\s+either\s+party)?\s+be\s+liable)(?:\s+to\s+[^.]*?)?\s+for\s+.*?(?:consequential|indirect|incidental|special|punitive)\s+damages\b.*?\b(?:total|aggregate|overall)?\s*liability(?:\s+of\s+[^,;.\n]+?)?\s+(?:shall\s+be|is)\s+unlimited\b|"
            r"\b(?:total|aggregate|overall)?\s*liability(?:\s+of\s+[^,;.\n]+?)?\s+(?:shall\s+be|is)\s+unlimited\b.*?\b(?:(?:shall\s+)?not\s+(?:be\s+)?liable|neither\s+party(?:\s+shall\s+be)?\s+liable|under\s+no\s+circumstances\s+shall(?:\s+either\s+party)?\s+be\s+liable)(?:\s+to\s+[^.]*?)?\s+for\s+.*?(?:consequential|indirect|incidental|special|punitive)\s+damages\b)"
        ),
        "description": "Intra-clause contradiction: Clause excludes categories of damages but subsequently states total liability is unlimited",
        "severity_weight": 85.0,
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
    {
        "rule_id": "RULE_LIAB_CONTRADICTORY_DAMAGE",
        "risk_category": RiskCategory.LIABILITY,
        "pattern": (
            r"\b((accepts?\s+(?:full\s+)?(?:responsibility|liability)\s+for\s+.*?"
            r"(?:but|however|yet|subsequently|\.)\s+.*?"
            r"(?:under\s+no\s+circumstances\s+shall.*?(?:be\s+(?:held\s+)?liable|be\s+required\s+to\s+pay|pay)|"
            r"(?:will\s+not|shall\s+not)\s+(?:be\s+(?:held\s+)?liable|be\s+required\s+to\s+pay|pay)|"
            r"not\s+be\s+required\s+to\s+pay|"
            r"disclaims?\s+(?:all\s+|any\s+)?(?:liability|responsibility|obligation)))|"
            r"(responsible\s+for\s+.*?damage.*?\b"
            r"(?:will\s+not|shall\s+not|not\s+liable\s+to|no\s+obligation\s+to|refuses?\s+to|not\s+be\s+required\s+to)\s+pay\s+"
            r"(?:compensation\s+|for\s+)?(?:any\s+|such\s+)?damage)|"
            r"((?:will\s+not|shall\s+not|no\s+obligation\s+to|not\s+be\s+required\s+to)\s+pay\s+"
            r"(?:compensation\s+for|for\s+(?:any\s+|such\s+)?damage).*?under\s+any\s+circumstances)|"
            r"(responsible\s+for\s+.*?damage.*?subsequently\s+(?:denies|disclaims|excludes)\s+.*?pay))\b"
        ),
        "description": "Contradictory liability provision accepting responsibility but denying payment for damage",
        "severity_weight": 85.0,
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
    {
        "rule_id": "RULE_INDEM_NO_CAP",
        "risk_category": RiskCategory.INDEMNIFICATION,
        "pattern": r"\b(indemnification\s+obligations?\s+(?:shall\s+be|are)\s+(?:unlimited|uncapped|not\s+subject\s+to\s+any\s+(?:limitation|cap)|excluded\s+from\s+(?:the\s+)?liability\s+cap))\b",
        "description": "Indemnification obligation explicitly excluded from liability caps or declared uncapped",
        "severity_weight": 90.0,
    },
    {
        "rule_id": "RULE_INDEM_NEGLIGENCE_COVERAGE",
        "risk_category": RiskCategory.INDEMNIFICATION,
        "pattern": r"\b(indemnify.*?(?:even\s+if\s+caused\s+by|including).*?(?:sole\s+negligence|gross\s+negligence|willful\s+misconduct))\b",
        "description": "Indemnification covers indemnified party's own negligence or misconduct",
        "severity_weight": 85.0,
    },

    # --- TERMINATION ---
    {
        "rule_id": "RULE_TERM_CONVENIENCE_UNILATERAL",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": (
            r"\b(terminate\s+(this\s+agreement\s+)?for\s+convenience|"
            r"terminate\s+at\s+any\s+time\s+without\s+(cause|reason)|"
            r"(?:reserves?\s+the\s+right\s+to\s+terminate|may\s+terminate|terminate)\s+(?:this\s+agreement\s+)?.*?\b(?:at\s+(?:its?|their)\s+sole\s+discretion|without\s+(?:prior\s+)?(?:notice|cause|explanation)))\b"
        ),
        "description": "Termination for convenience allowed without cause or notice at sole discretion",
        "severity_weight": 85.0,
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
    {
        "rule_id": "RULE_PAYMENT_ACCELERATION_DEFAULT",
        "risk_category": RiskCategory.PAYMENT_TERMS,
        "pattern": r"\b((?:upon|in\s+the\s+event\s+of)\s+(?:late\s+payment|payment\s+default|failure\s+to\s+pay).*?(?:all\s+sums|entire\s+contract\s+value|all\s+unpaid\s+amounts|total\s+fees)\s+(?:shall\s+become\s+)?immediately\s+due\s+and\s+payable)\b",
        "description": "Payment acceleration clause making all future/unpaid fees immediately payable upon payment delay",
        "severity_weight": 85.0,
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
    {
        "rule_id": "RULE_IP_MORAL_RIGHTS_WAIVER",
        "risk_category": RiskCategory.INTELLECTUAL_PROPERTY,
        "pattern": r"\b(unconditionally\s+and\s+irrevocably\s+waives?\s+(?:all\s+)?moral\s+rights|waives?\s+any\s+moral\s+rights\s+under\s+copyright\s+law)\b",
        "description": "Unconditional waiver of author moral rights",
        "severity_weight": 75.0,
    },
    {
        "rule_id": "RULE_IP_PREEXISTING_ASSIGNMENT",
        "risk_category": RiskCategory.INTELLECTUAL_PROPERTY,
        "pattern": r"\b(assigns?\s+all\s+(?:pre-existing|background|prior)\s+intellectual\s+property|transfer\s+of\s+all\s+background\s+ip\s+rights)\b",
        "description": "Assignment of pre-existing background intellectual property rights",
        "severity_weight": 85.0,
    },

    # --- MODIFICATION ---
    {
        "rule_id": "RULE_MOD_UNILATERAL",
        "risk_category": RiskCategory.MODIFICATION,
        "pattern": r"\b((reserves?\s+the\s+right\s+to\s+(modify|amend|update|change)|(may|can)\s+(modify|amend|update|change)|(modify|amend|update|change)\s+(the\s+|these\s+)?(terms|agreement|contract|provisions?)).*?\b((in|at)\s+(its?|their|his|her|our)\s+sole\s+discretion|without\s+(prior\s+)?notice)|(in|at)\s+(its?|their|his|her|our)\s+sole\s+discretion.*?\b(modify|amend|update|change)\s+(the\s+|these\s+)?(terms|agreement|contract))\b",
        "description": "Unilateral right to modify terms at sole discretion without notice",
        "severity_weight": 85.0,
    },

    # --- RENEWAL ---
    {
        "rule_id": "RULE_RENEWAL_AUTO",
        "risk_category": RiskCategory.RENEWAL,
        "pattern": r"\b(automatically\s+renew(?:s|ed|ing)?|auto-renew(?:al)?|renew(?:s|ed)?\s+automatically|shall\s+(?:automatically\s+)?renew\s+for\s+successive\s+(?:terms?|periods?)|evergreen\s+(?:provision|clause|contract|agreement))\b",
        "description": "Automatic renewal clause",
        "severity_weight": 60.0,
    },
    {
        "rule_id": "RULE_RENEWAL_BURDENSOME_OPT_OUT",
        "risk_category": RiskCategory.RENEWAL,
        "pattern": r"\b(renew(?:s|ed)?\s+(?:automatically|for\s+successive).*?(?:unless|provided).*?(?:written\s+notice|cancel).*?(?:at\s+least\s+(?:60|90|120|180)\s+days|prior\s+to\s+the\s+expiration))\b",
        "description": "Burdensome advance notice window required to prevent automatic contract renewal",
        "severity_weight": 75.0,
    },

    # --- NON-COMPETE ---
    {
        "rule_id": "RULE_NON_COMPETE_RESTRICT",
        "risk_category": RiskCategory.NON_COMPETE,
        "pattern": r"\b(shall\s+not\s+(directly\s+or\s+indirectly\s+)?(compete|solicit|engage\s+in\s+any\s+competing\s+business))\b",
        "description": "Restrictive non-compete or non-solicitation covenant",
        "severity_weight": 85.0,
    },
    {
        "rule_id": "RULE_NON_COMPETE_BROAD_SCOPE",
        "risk_category": RiskCategory.NON_COMPETE,
        "pattern": r"\b((?:covenant|agree)s?\s+not\s+to\s+compete|non-compete\s+obligation|shall\s+not\s+(?:directly\s+or\s+indirectly\s+)?(?:enter\s+into|render\s+services\s+to|be\s+employed\s+by|participate\s+in)\s+(?:any\s+)?(?:competing|similar)\s+(?:business|entity|activity)|worldwide\s+(?:non-compete|restriction)|without\s+geographic\s+limit(?:ation)?)\b",
        "description": "Broad non-compete restriction lacking geographic or functional boundaries",
        "severity_weight": 85.0,
    },
    {
        "rule_id": "RULE_NON_SOLICIT_RESTRICTION",
        "risk_category": RiskCategory.NON_COMPETE,
        "pattern": r"\b(shall\s+not\s+(?:directly\s+or\s+indirectly\s+)?(?:solicit|induce|recruit|hire|entice)\s+(?:any\s+)?(?:employee|contractor|client|customer|supplier))\b",
        "description": "Restrictive non-solicitation covenant targeting personnel or clients",
        "severity_weight": 75.0,
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
        "pattern": (
            r"\b(prices?\s+quoted\s+are\s+subject\s+to\s+(alteration|change|increase)\s+without\s+notice|"
            r"unilaterally\s+(adjust|increase|alter|change|modify)\s+(the\s+)?(prices?|fees?|rates?)|"
            r"(increase|raise|adjust|alter|modify|escalate)\s+(?:or\s+\w+\s+)?(the\s+)?(agreed\s+|contract\s+|quoted\s+)?(prices?|fees?|rates?|charges?|amounts?)\s+(at\s+any\s+time\s+)?without\s+(asking|the\s+approval|the\s+consent|prior\s+written|consulting|requiring|obtaining|seeking|notice)|"
            r"(can|may|reserves?\s+the\s+right\s+to)\s+(increase|raise|adjust|alter|change|modify)\s+(?:or\s+\w+\s+)?(the\s+)?(agreed\s+|contract\s+)?(prices?|fees?|rates?|amounts?).*?without\s+(asking|approval|consent|notice)|"
            r"change\s+prices?\s+at\s+any\s+time(\s+without\s+notice)?|"
            r"(must|shall)\s+pay\s+(the\s+)?(new|increased|adjusted)\s+(amount|price|fee|rate)s?\s+(even\s+if|regardless).*?\b(does\s+not\s+agree|without\s+agreement))\b"
        ),
        "description": "Unilateral price increase or modification without customer approval or consent",
        "severity_weight": 75.0,
    },
    {
        "rule_id": "RULE_TERM_NO_NOTICE",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": (
            r"\b((?:terminate|end|cancel|stop\s+(?:the\s+)?work|cease\s+(?:the\s+)?work|suspend\s+(?:the\s+)?work|discontinue\s+(?:the\s+)?services?)\s+"
            r"(?:this\s+agreement\s+|the\s+services\s+|the\s+work\s+)?"
            r"(?:immediately\s*)?[,;]?\s*(?:at\s+any\s+time\s*)?[,;]?\s*"
            r"without\s+(?:giving|providing)?\s*(?:any\s+)?(?:prior\s+)?(?:reason|notice|cause|explanation|refund)|"
            r"terminate\s+without\s+(?:notice|refund)|"
            r"forfeit(?:ure)?\s+of\s+(?:prepaid\s+)?fees?)\b"
        ),
        "description": "Immediate termination or work stoppage without notice or justification",
        "severity_weight": 80.0,
    },
    {
        "rule_id": "RULE_TERM_ASYMMETRIC_NOTICE",
        "risk_category": RiskCategory.TERMINATION,
        "pattern": (
            r"(?s)(?:either\s+party|both\s+parties|parties)\s+(?:may\s+)?terminate.*?(?:days?.*?notice|notice).*?"
            r"(?:provided|however|except|notwithstanding).*?(?:(?:the\s+)?(?:service\s+provider|contractor|vendor|company|licensor)\s+(?:may|reserves?\s+the\s+right\s+to)\s+terminate|terminate).*?"
            r"(?:immediately\s*)?[,;]?\s*(?:at\s+any\s+time\s*)?[,;]?\s*without\s+(?:prior\s+)?(?:notice|cause|explanation)"
        ),
        "description": "Asymmetric termination rights: Mutual advance notice requirement contradicted by unilateral immediate termination right without notice",
        "severity_weight": 85.0,
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
    {
        "rule_id": "RULE_DATA_BREACH_DISCLAIMER",
        "risk_category": RiskCategory.DATA_PRIVACY,
        "pattern": r"\b((?:disclaims?|no|not)\s+(?:all\s+|any\s+)?(?:liability|responsibility)\s+for\s+(?:all\s+|any\s+)?(?:data\s+breach(?:es)?|security\s+incident|unauthorized\s+access|data\s+loss|cyberattack|loss\s+of\s+data))\b",
        "description": "Disclaimer of liability or responsibility for data breaches or security incidents",
        "severity_weight": 90.0,
    },
    {
        "rule_id": "RULE_DATA_CROSS_BORDER_UNRESTRICTED",
        "risk_category": RiskCategory.DATA_PRIVACY,
        "pattern": r"\b(transfer\s+(?:personal\s+)?data\s+(?:outside|cross-border|internationally|to\s+any\s+jurisdiction)\s+without\s+(?:prior\s+)?(?:notice|consent|safeguards))\b",
        "description": "Unrestricted international cross-border transfer of personal data without consent or safeguards",
        "severity_weight": 75.0,
    },

    # --- CONFIDENTIALITY ---
    {
        "rule_id": "RULE_CONFID_PERPETUAL_SURVIVAL",
        "risk_category": RiskCategory.CONFIDENTIALITY,
        "pattern": r"\b(confidentiality\s+obligations?\s+shall\s+survive\s+(?:in\s+perpetuity|indefinitely|forever)|duty\s+of\s+confidentiality\s+shall\s+never\s+expire)\b",
        "description": "Perpetual or indefinite confidentiality obligations surviving termination forever",
        "severity_weight": 70.0,
    },

    # --- GOVERNING LAW & JURISDICTION ---
    {
        "rule_id": "RULE_GOV_LAW_FOREIGN_VENUE",
        "risk_category": RiskCategory.GOVERNING_LAW,
        "pattern": r"\b(exclusive\s+jurisdiction\s+of\s+the\s+courts\s+of\s+(?:foreign|offshore|distant|bermuda|cayman|singapore|england|delaware|new\s+york)\s+and\s+waives\s+any\s+objection\s+to\s+venue)\b",
        "description": "Exclusive jurisdiction in a foreign or distant venue with waiver of venue objections",
        "severity_weight": 75.0,
    },

    # --- FORCE MAJEURE ---
    {
        "rule_id": "RULE_FORCE_MAJEURE_ASYMMETRIC",
        "risk_category": RiskCategory.FORCE_MAJEURE,
        "pattern": r"\b((?:provider|company|vendor)\s+shall\s+be\s+excused\s+from\s+performance\s+due\s+to\s+force\s+majeure.*?(?:customer|client)\s+shall\s+remain\s+obligated\s+to\s+pay|force\s+majeure\s+shall\s+not\s+excuse\s+payment\s+obligations)\b",
        "description": "Asymmetric force majeure excusing provider performance while strictly preserving customer payment obligations",
        "severity_weight": 70.0,
    },
]
