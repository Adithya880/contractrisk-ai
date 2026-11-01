"""
Cross-Clause Conflict and Contradiction Detector Module for ContractRisk AI.
Phase 3 — Detects genuine, verified contradictions and direct inconsistencies
between clauses or within compound contractual provisions.
Produces grounded, evidence-backed explanations without speculative leaps.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from src.risk_analysis.models import CrossClauseConflict, RiskLevel


_WORD_TO_DAYS = {
    "thirty": 30, "sixty": 60, "ninety": 90, "forty-five": 45, "twenty": 20,
    "fifteen": 15, "ten": 10, "seven": 7, "fourteen": 14
}


class CrossClauseConflictDetector:
    """
    High-precision detector for cross-clause and intra-clause contradictions.
    Only flags genuine, verified contradictions (e.g. conflicting notice periods,
    liability caps contradicted by exclusions, or price changes allowed vs prohibited).
    """

    def __init__(self):
        # Explicit prohibition of price changes vs unilateral price changes
        self.re_prohibit_price_change = re.compile(
            r"\b(prices?\s+(?:are|shall\s+be)\s+fixed|fixed\s+price|"
            r"not\s+subject\s+to\s+(?:any\s+)?(?:increase|alteration|modification|escalation)|"
            r"no\s+(?:price\s+)?(?:increase|adjustment|change)\s+without\s+(?:mutual|prior\s+written)\s+(?:consent|agreement)|"
            r"(?:cannot|shall\s+not)\s+be\s+(?:increased|altered|changed|modified)\s+without\s+(?:mutual|prior\s+written)\s+(?:consent|agreement))\b",
            re.IGNORECASE
        )
        self.re_permit_unilateral_price = re.compile(
            r"\b((?:reserves?\s+the\s+right\s+to\s+)?(?:increase|raise|alter|modify|escalate|change)\s+(?:the\s+)?(?:agreed\s+|quoted\s+)?(?:prices?|fees?|rates?)\s+"
            r"(?:at\s+any\s+time\s+)?without\s+(?:asking|the\s+approval|the\s+consent|prior\s+written|consulting|notice|agreement)|"
            r"unilaterally\s+(?:adjust|increase|alter|change|modify)\s+(?:the\s+)?(?:prices?|fees?|rates?))\b",
            re.IGNORECASE
        )

        # Termination notice periods (extracting number of days or words)
        self.re_notice_days_term = re.compile(
            r"\b(?:terminat\w*|cancel\w*|end\s+this\s+agreement)\b.*?\b(?:(?:thirty|sixty|ninety|forty-five|twenty|fifteen|fourteen|ten|seven|\d+)\s*(?:\(\s*(\d+)\s*\)\s*)?|(\d+))\s*days?'?\s+(?:prior\s+)?(?:written\s+)?notice\b|"
            r"\b(?:(?:thirty|sixty|ninety|forty-five|twenty|fifteen|fourteen|ten|seven|\d+)\s*(?:\(\s*(\d+)\s*\)\s*)?|(\d+))\s*days?'?\s+(?:prior\s+)?(?:written\s+)?notice.*?\b(?:terminat|cancel|end\s+this\s+agreement)\b",
            re.IGNORECASE
        )
        self.re_immediate_termination_no_cause = re.compile(
            r"\b(?:terminate|end\s+this\s+agreement|stop\s+the\s+work|cease\s+work)\s+"
            r"(?:immediately\s+)?(?:at\s+any\s+time\s+)?without\s+(?:giving\s+)?(?:any\s+)?(?:reason|notice|cause|explanation)\b",
            re.IGNORECASE
        )

        # Liability cap vs explicit exclusion from liability cap
        self.re_liability_cap = re.compile(
            r"\b(?:aggregate\s+liability\s+(?:shall\s+not\s+exceed|is\s+limited\s+to)|"
            r"maximum\s+liability\s+(?:shall\s+not\s+exceed|is\s+limited\s+to)|"
            r"liability\s+capped\s+at|cap\s+on\s+liability\s+of)\s+([₹$€£\d]+|fees\s+paid|amount\s+paid)\b",
            re.IGNORECASE
        )
        self.re_liability_uncapped_contradiction = re.compile(
            r"\b(?:liability\s+(?:shall\s+not\s+be\s+limited|is\s+unlimited|shall\s+not\s+be\s+subject\s+to\s+any\s+cap)|"
            r"no\s+cap\s+(?:or\s+limitation\s+)?on\s+liability|unlimited\s+liability\s+for\s+all\s+claims|"
            r"excludes?\s+.*?\s+from\s+(?:any\s+)?(?:cap|limitation\s+of\s+liability))\b",
            re.IGNORECASE
        )

        # Damage responsibility vs absolute refusal to compensate
        self.re_damage_responsibility = re.compile(
            r"\b(?:accepts?\s+(?:full\s+)?(?:responsibility|liability)\s+for\s+.*?(?:damage|loss)|"
            r"(?:responsible|liable)\s+for\s+(?:any\s+)?damage\s+caused)\b",
            re.IGNORECASE
        )
        self.re_damage_disclaimer = re.compile(
            r"\b(?:under\s+no\s+circumstances\s+shall.*?(?:be\s+(?:held\s+)?liable|be\s+required\s+to\s+pay|pay)|"
            r"(?:will\s+not|shall\s+not|no\s+obligation\s+to|refuses?\s+to)\s+pay\s+for\s+(?:any\s+)?damage)\b",
            re.IGNORECASE
        )

        # Governing Law / Exclusive Jurisdiction
        self.re_gov_law = re.compile(
            r"\b(?:governed\s+(?:\w+\s+)?by\s+the\s+laws\s+of\s+(?:the\s+State\s+of\s+)?([A-Za-z\s]+?)(?:[.;,]|\band\b|$)|"
            r"exclusive\s+jurisdiction\s+of\s+(?:the\s+courts\s+of\s+)?([A-Za-z\s]+?)(?:[.;,]|\band\b|$))",
            re.IGNORECASE
        )

        # Warranty vs strict As-Is Disclaimer
        self.re_express_warranty = re.compile(
            r"\b(?:warrants?\s+(?:and\s+represents?\s+)?that\s+(?:all\s+|the\s+)?(?:services|work|deliverables|products?)|"
            r"expressly\s+warrants?\s+that|guarantees?\s+that)\b",
            re.IGNORECASE
        )
        self.re_as_is_disclaimer = re.compile(
            r"\b(?:provided\s+(?:strictly\s+)?(?:on\s+an\s+)?[\"']?as[- ]is[\"']?|"
            r"disclaims?\s+all\s+warranties|"
            r"without\s+any\s+warranties\s+(?:express\s+or\s+implied)|no\s+warranty\s+express\s+or\s+implied)\b",
            re.IGNORECASE
        )

    def _get_clause_field(self, clause: Any, field_name: str, default: Any = None) -> Any:
        """Helper to extract attribute from Pydantic model or dict."""
        if hasattr(clause, field_name):
            val = getattr(clause, field_name)
            return val if val is not None else default
        elif isinstance(clause, dict):
            return clause.get(field_name, default)
        return default

    def detect_cross_clause_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """
        Scan across distinct contract clauses to detect genuine contradictions and conflicts.
        Strictly requires comparisons across different clauses (id1 != id2).
        """
        conflicts: List[CrossClauseConflict] = []
        if not clauses or len(clauses) < 2:
            return conflicts

        # 1. Termination Notice Contradictions (e.g. 30 days vs 90 days notice, or notice vs immediate no-cause stoppage)
        conflicts.extend(self._detect_termination_notice_conflicts(clauses))

        # 2. Liability Cap vs Uncapped Liability Contradictions
        conflicts.extend(self._detect_liability_cap_conflicts(clauses))

        # 3. Price Prohibition vs Unilateral Price Increase Contradiction
        conflicts.extend(self._detect_price_payment_conflicts(clauses))

        # 4. Damage Responsibility vs Absolute Refusal to Pay Contradiction
        conflicts.extend(self._detect_damage_responsibility_conflicts(clauses))

        # 5. Conflicting Governing Law / Jurisdiction
        conflicts.extend(self._detect_governing_law_conflicts(clauses))

        # 6. Express Warranty vs Strict As-Is Disclaimer
        conflicts.extend(self._detect_warranty_conflicts(clauses))

        return [c for c in conflicts if len(set(c.clause_ids)) > 1]

    def detect_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """
        Scan distinct clauses for cross-clause contradictions.
        (Cross-clause conflicts strictly compare different clauses).
        """
        return self.detect_cross_clause_conflicts(clauses)

    def detect_intra_clause_contradictions(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """
        Inspect each individual clause for internal contradictions and unilateral asymmetries.
        """
        intra_conflicts: List[CrossClauseConflict] = []
        if not clauses:
            return intra_conflicts

        for c in clauses:
            cid = str(self._get_clause_field(c, "clause_id") or "")
            cnum = str(self._get_clause_field(c, "clause_number") or f"Clause {cid}")
            text = self._get_clause_field(c, "clause_text", "")
            if not text:
                continue

            # A. Limitation of Liability Inconsistency:
            # Clause excludes categories of damages (indirect, consequential, special) OR specifies liability caps,
            # but subsequently states that total liability is unlimited.
            has_excl = bool(re.search(
                r"\b(?:(?:shall\s+)?not\s+(?:be\s+)?liable|neither\s+party(?:\s+shall\s+be)?\s+liable|under\s+no\s+circumstances\s+shall(?:\s+either\s+party)?\s+be\s+liable)(?:\s+to\s+[^.]*?)?\s+for\s+.*?(?:consequential|indirect|incidental|special|punitive)\s+damages|"
                r"disclaims?\s+(?:all\s+)?(?:consequential|indirect)\s+damages|"
                r"exclusion\s+of\s+(?:consequential|indirect)\s+damages|"
                r"aggregate\s+liability\s+(?:shall\s+not\s+exceed|is\s+limited\s+to)|"
                r"maximum\s+liability\s+(?:shall\s+not\s+exceed|is\s+limited\s+to)",
                text, re.I
            ))
            has_unlim = bool(re.search(
                r"\b(?:total|aggregate|overall|maximum)?\s*liability(?:\s+of\s+[^,;.\n]+?)?\s+(?:shall\s+be|is)\s+(?:unlimited|uncapped|without\s+limit)|"
                r"unlimited\s+liability|"
                r"liability(?:\s+of\s+[^,;.\n]+?)?\s+shall\s+not\s+be\s+limited|"
                r"no\s+cap\s+(?:or\s+limitation\s+)?on\s+liability",
                text, re.I
            ))
            if has_excl and has_unlim:
                intra_conflicts.append(
                    CrossClauseConflict(
                        conflict_id=f"intra_liab_{uuid.uuid4().hex[:8]}",
                        conflict_type="Limitation of Liability Inconsistency",
                        severity=RiskLevel.HIGH,
                        clause_ids=[cid],
                        clause_numbers=[cnum],
                        explanation=(
                            f"Clause {cnum} contains an internal contradiction: it purports to exclude categories of damages "
                            f"(such as consequential or indirect losses) or limit liability, yet subsequently states that total liability "
                            f"is unlimited, creating critical legal ambiguity regarding actual financial exposure."
                        ),
                        conflicting_excerpt_a=text[:160].strip(),
                        conflicting_excerpt_b="Stipulates total liability is unlimited despite damage limitations."
                    )
                )

            # B. Termination Asymmetry:
            # Mutual notice (e.g. 30 days notice for both parties), but immediate termination without notice for one party.
            m_notice = self.re_notice_days_term.search(text)
            has_immediate_provider = bool(re.search(
                r"\b(?:(?:the\s+)?(?:service\s+provider|contractor|vendor|company|licensor)\s+(?:may|reserves?\s+the\s+right\s+to)\s+terminate|(?:provided|however|except)\s+.*?\bterminate)\s+(?:this\s+agreement\s+)?(?:immediately\s*)?[,;]?\s*(?:at\s+any\s+time\s*)?[,;]?\s*without\s+(?:prior\s+)?(?:notice|cause|explanation)",
                text, re.I | re.DOTALL
            ))
            if m_notice and has_immediate_provider:
                digits_match = re.search(r"\b(\d+)\b", m_notice.group(0))
                days_str = digits_match.group(1) if digits_match else "30"
                intra_conflicts.append(
                    CrossClauseConflict(
                        conflict_id=f"intra_term_{uuid.uuid4().hex[:8]}",
                        conflict_type="Termination Notice Asymmetry",
                        severity=RiskLevel.HIGH,
                        clause_ids=[cid],
                        clause_numbers=[cnum],
                        explanation=(
                            f"Clause {cnum} establishes a {days_str}-day mutual notice period for termination, but contains an asymmetric carve-out "
                            f"permitting the service provider to terminate immediately without notice, eliminating termination protection for the client."
                        ),
                        conflicting_excerpt_a=text[:160].strip(),
                        conflicting_excerpt_b=f"Mutual {days_str}-day notice requirement negated by unilateral immediate termination right."
                    )
                )

            # C. Fixed Price vs Unilateral Alteration inside same clause:
            if self.re_prohibit_price_change.search(text) and self.re_permit_unilateral_price.search(text):
                intra_conflicts.append(
                    CrossClauseConflict(
                        conflict_id=f"intra_price_{uuid.uuid4().hex[:8]}",
                        conflict_type="Intra-Clause Price Inconsistency",
                        severity=RiskLevel.HIGH,
                        clause_ids=[cid],
                        clause_numbers=[cnum],
                        explanation=(
                            f"Clause {cnum} establishes fixed payment terms while simultaneously allowing unilateral price increases without approval."
                        ),
                        conflicting_excerpt_a=text[:160].strip(),
                        conflicting_excerpt_b="Fixed fee guarantee contradicted by unilateral price increase reservation."
                    )
                )

            # D. Damage Responsibility vs Disclaimer inside same clause:
            if self.re_damage_responsibility.search(text) and self.re_damage_disclaimer.search(text):
                intra_conflicts.append(
                    CrossClauseConflict(
                        conflict_id=f"intra_dmg_{uuid.uuid4().hex[:8]}",
                        conflict_type="Intra-Clause Damage Responsibility Contradiction",
                        severity=RiskLevel.HIGH,
                        clause_ids=[cid],
                        clause_numbers=[cnum],
                        explanation=(
                            f"Clause {cnum} accepts responsibility for damage caused, yet denies obligation or liability to pay for such damage."
                        ),
                        conflicting_excerpt_a=text[:160].strip(),
                        conflicting_excerpt_b="Acceptance of damage responsibility contradicted by disclaimer of payment obligations."
                    )
                )

        return intra_conflicts

    def _detect_termination_notice_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """Detect genuine contradictions in termination notice periods or notice vs immediate termination."""
        notice_items: List[Tuple[Any, int, str]] = []
        immediate_items: List[Tuple[Any, str]] = []

        for c in clauses:
            text = self._get_clause_field(c, "clause_text", "")
            # Check for notice periods with numeric days
            m_notice = self.re_notice_days_term.search(text)
            if m_notice:
                digits_match = re.search(r"\b(\d+)\b", m_notice.group(0))
                if digits_match:
                    days = int(digits_match.group(1))
                    notice_items.append((c, days, m_notice.group(0)))
                else:
                    word_match = re.search(r"\b(thirty|sixty|ninety|forty-five|twenty|fifteen|fourteen|ten|seven)\b", m_notice.group(0), re.IGNORECASE)
                    if word_match and word_match.group(1).lower() in _WORD_TO_DAYS:
                        days = _WORD_TO_DAYS[word_match.group(1).lower()]
                        notice_items.append((c, days, m_notice.group(0)))

            m_imm = self.re_immediate_termination_no_cause.search(text)
            if m_imm:
                immediate_items.append((c, m_imm.group(0)))

        conflicts = []

        # Compare notice periods across distinct clauses (e.g. 30 days vs 90 days for termination)
        for i in range(len(notice_items)):
            c1, d1, snip1 = notice_items[i]
            id1 = str(self._get_clause_field(c1, "clause_id") or "")
            num1 = str(self._get_clause_field(c1, "clause_number") or f"Clause {id1}")
            text1 = self._get_clause_field(c1, "clause_text", "")

            for j in range(i + 1, len(notice_items)):
                c2, d2, snip2 = notice_items[j]
                id2 = str(self._get_clause_field(c2, "clause_id") or "")
                num2 = str(self._get_clause_field(c2, "clause_number") or f"Clause {id2}")
                text2 = self._get_clause_field(c2, "clause_text", "")

                if id1 != id2 and d1 != d2:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Contradictory Termination Notice Periods",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id1, id2],
                            clause_numbers=[num1, num2],
                            explanation=(
                                f"Clause {num1} establishes a {d1}-day termination notice period, while "
                                f"Clause {num2} establishes a conflicting {d2}-day notice period for terminating the agreement."
                            ),
                            conflicting_excerpt_a=text1[:160].strip(),
                            conflicting_excerpt_b=text2[:160].strip()
                        )
                    )

        # Compare advance notice vs immediate stoppage without notice
        for c1, d1, snip1 in notice_items:
            id1 = str(self._get_clause_field(c1, "clause_id") or "")
            num1 = str(self._get_clause_field(c1, "clause_number") or f"Clause {id1}")
            text1 = self._get_clause_field(c1, "clause_text", "")

            for c2, snip2 in immediate_items:
                id2 = str(self._get_clause_field(c2, "clause_id") or "")
                num2 = str(self._get_clause_field(c2, "clause_number") or f"Clause {id2}")
                text2 = self._get_clause_field(c2, "clause_text", "")

                if id1 != id2:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Termination Notice vs Immediate Stoppage Contradiction",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id1, id2],
                            clause_numbers=[num1, num2],
                            explanation=(
                                f"Clause {num1} requires advance written notice of {d1} days to terminate, "
                                f"whereas Clause {num2} allows immediate termination or work stoppage without notice."
                            ),
                            conflicting_excerpt_a=text1[:160].strip(),
                            conflicting_excerpt_b=text2[:160].strip()
                        )
                    )

        return conflicts

    def _detect_liability_cap_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """Detect contradictions between liability cap and explicit uncapped liability on the same scope."""
        cap_clauses = []
        uncapped_clauses = []

        for c in clauses:
            text = self._get_clause_field(c, "clause_text", "")
            m_cap = self.re_liability_cap.search(text)
            m_uncap = self.re_liability_uncapped_contradiction.search(text)

            if m_cap:
                cap_clauses.append((c, m_cap.group(0), text))
            if m_uncap:
                # Exclude standard preservation carve-outs ("Nothing shall limit liability for death or injury")
                if not re.search(r"\bnothing\s+in\s+this\s+agreement\s+shall\s+(?:exclude|limit)\b.*?\b(?:death|personal\s+injury|fraud)\b", text, re.I):
                    uncapped_clauses.append((c, m_uncap.group(0), text))

        conflicts = []
        for c_cap, snip_cap, text_cap in cap_clauses:
            id_cap = str(self._get_clause_field(c_cap, "clause_id") or "")
            num_cap = str(self._get_clause_field(c_cap, "clause_number") or f"Clause {id_cap}")

            for c_un, snip_un, text_un in uncapped_clauses:
                id_un = str(self._get_clause_field(c_un, "clause_id") or "")
                num_un = str(self._get_clause_field(c_un, "clause_number") or f"Clause {id_un}")

                if id_cap != id_un:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Liability Cap vs Uncapped Liability Contradiction",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id_cap, id_un],
                            clause_numbers=[num_cap, num_un],
                            explanation=(
                                f"Clause {num_cap} establishes a strict liability cap ({snip_cap}), while "
                                f"Clause {num_un} declares liability uncapped or excluded from limitation."
                            ),
                            conflicting_excerpt_a=text_cap[:160].strip(),
                            conflicting_excerpt_b=text_un[:160].strip()
                        )
                    )
        return conflicts

    def _detect_price_payment_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """Detect contradiction when one clause explicitly prohibits price changes and another permits unilateral alteration."""
        prohibited_clauses = []
        unilateral_clauses = []

        for c in clauses:
            text = self._get_clause_field(c, "clause_text", "")
            m_proh = self.re_prohibit_price_change.search(text)
            m_perm = self.re_permit_unilateral_price.search(text)

            if m_proh:
                prohibited_clauses.append((c, m_proh.group(0), text))
            if m_perm:
                unilateral_clauses.append((c, m_perm.group(0), text))

        conflicts = []
        for c_pr, snip_pr, text_pr in prohibited_clauses:
            id_pr = str(self._get_clause_field(c_pr, "clause_id") or "")
            num_pr = str(self._get_clause_field(c_pr, "clause_number") or f"Clause {id_pr}")

            for c_un, snip_un, text_un in unilateral_clauses:
                id_un = str(self._get_clause_field(c_un, "clause_id") or "")
                num_un = str(self._get_clause_field(c_un, "clause_number") or f"Clause {id_un}")

                if id_pr != id_un:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Price Stability vs Unilateral Increase Contradiction",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id_pr, id_un],
                            clause_numbers=[num_pr, num_un],
                            explanation=(
                                f"Clause {num_pr} establishes that prices are fixed and cannot be changed without mutual consent, "
                                f"directly contradicting Clause {num_un} which permits unilateral price increases without approval."
                            ),
                            conflicting_excerpt_a=text_pr[:160].strip(),
                            conflicting_excerpt_b=text_un[:160].strip()
                        )
                    )
        return conflicts

    def _detect_damage_responsibility_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """Detect contradiction between accepting responsibility for damage and absolute disclaimer of compensation."""
        resp_clauses = []
        disclaim_clauses = []

        for c in clauses:
            text = self._get_clause_field(c, "clause_text", "")
            m_resp = self.re_damage_responsibility.search(text)
            m_disc = self.re_damage_disclaimer.search(text)

            if m_resp:
                resp_clauses.append((c, m_resp.group(0), text))
            if m_disc:
                disclaim_clauses.append((c, m_disc.group(0), text))

        conflicts = []
        for c_r, snip_r, text_r in resp_clauses:
            id_r = str(self._get_clause_field(c_r, "clause_id") or "")
            num_r = str(self._get_clause_field(c_r, "clause_number") or f"Clause {id_r}")

            for c_d, snip_d, text_d in disclaim_clauses:
                id_d = str(self._get_clause_field(c_d, "clause_id") or "")
                num_d = str(self._get_clause_field(c_d, "clause_number") or f"Clause {id_d}")

                if id_r != id_d:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Liability Acceptance vs Remedy Disclaimer Contradiction",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id_r, id_d],
                            clause_numbers=[num_r, num_d],
                            explanation=(
                                f"Clause {num_r} accepts legal or operational responsibility for damages ({snip_r}), "
                                f"yet Clause {num_d} disclaims any obligation to pay compensation or damages under any circumstances."
                            ),
                            conflicting_excerpt_a=text_r[:160].strip(),
                            conflicting_excerpt_b=text_d[:160].strip()
                        )
                    )
        return conflicts

    def _detect_governing_law_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """Detect conflicting governing law or jurisdiction across distinct clauses."""
        law_entries = []
        for c in clauses:
            text = self._get_clause_field(c, "clause_text", "")
            m = self.re_gov_law.search(text)
            if m:
                raw_loc = (m.group(1) or m.group(2) or "").strip().lower()
                # Clean location string
                raw_loc = re.sub(r"\b(courts|laws?|jurisdiction)\b", "", raw_loc).strip()
                if len(raw_loc) >= 3:
                    law_entries.append((c, raw_loc, text))

        conflicts = []
        for i in range(len(law_entries)):
            c1, loc1, text1 = law_entries[i]
            id1 = str(self._get_clause_field(c1, "clause_id") or "")
            num1 = str(self._get_clause_field(c1, "clause_number") or f"Clause {id1}")

            for j in range(i + 1, len(law_entries)):
                c2, loc2, text2 = law_entries[j]
                id2 = str(self._get_clause_field(c2, "clause_id") or "")
                num2 = str(self._get_clause_field(c2, "clause_number") or f"Clause {id2}")

                if loc1 != loc2 and id1 != id2:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Conflicting Governing Law / Jurisdiction",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id1, id2],
                            clause_numbers=[num1, num2],
                            explanation=(
                                f"Clause {num1} designates '{loc1.title()}' as governing law/jurisdiction, "
                                f"directly conflicting with Clause {num2} designating '{loc2.title()}'."
                            ),
                            conflicting_excerpt_a=text1[:160].strip(),
                            conflicting_excerpt_b=text2[:160].strip()
                        )
                    )
        return conflicts

    def _detect_warranty_conflicts(self, clauses: List[Any]) -> List[CrossClauseConflict]:
        """Detect express warranty commitments contradicted by as-is disclaimers."""
        warr_clauses = []
        asis_clauses = []

        for c in clauses:
            text = self._get_clause_field(c, "clause_text", "")
            m_w = self.re_express_warranty.search(text)
            m_a = self.re_as_is_disclaimer.search(text)

            if m_w:
                warr_clauses.append((c, text))
            if m_a:
                asis_clauses.append((c, text))

        conflicts = []
        for w_c, text_w in warr_clauses:
            id_w = str(self._get_clause_field(w_c, "clause_id") or "")
            num_w = str(self._get_clause_field(w_c, "clause_number") or f"Clause {id_w}")

            for a_c, text_a in asis_clauses:
                id_a = str(self._get_clause_field(a_c, "clause_id") or "")
                num_a = str(self._get_clause_field(a_c, "clause_number") or f"Clause {id_a}")

                if id_w != id_a:
                    conflicts.append(
                        CrossClauseConflict(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="Express Warranty vs As-Is Disclaimer Contradiction",
                            severity=RiskLevel.HIGH,
                            clause_ids=[id_w, id_a],
                            clause_numbers=[num_w, num_a],
                            explanation=(
                                f"Clause {num_w} gives an express warranty of performance or quality, "
                                f"which is directly nullified by Clause {num_a} disclaiming all warranties on a strict as-is basis."
                            ),
                            conflicting_excerpt_a=text_w[:160].strip(),
                            conflicting_excerpt_b=text_a[:160].strip()
                        )
                    )
        return conflicts
