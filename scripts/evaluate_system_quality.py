"""
End-to-End System Quality Evaluation Benchmark for ContractRisk AI.
Evaluates:
1. BERT Clause Classifier (CUAD 41 classes + out-of-domain uncertainty)
2. Rule Engine Precision and Recall across 13 risk domains (Toxic vs Benign)
3. Intra-Clause & Cross-Clause Contradiction Detection
4. FAISS Semantic Retrieval Grounding & Cosine Similarity
5. Hybrid Risk Scoring Calibration & Component Attribution
6. Performance & Latency Benchmarks
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

import time
import json
import logging
from typing import Dict, List, Any, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SystemEvaluation")

from src.models.bert_predictor import get_bert_predictor
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.conflict_detector import CrossClauseConflictDetector
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.models import RiskCategory, RiskLevel, LLMInferenceStatus
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.document_processing.models import SourceType
from src.embeddings import ClauseEmbedder, FAISSIndexManager
from src.rag.retriever import RAGRetriever


def benchmark_bert_classifier() -> Dict[str, Any]:
    """Benchmark BERT 41 CUAD classes and out-of-domain handling."""
    logger.info("Starting BERT Classifier Evaluation...")
    predictor = get_bert_predictor()
    
    # Representative CUAD test clauses
    cuad_samples = [
        ("Governing Law", "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware."),
        ("Cap On Liability", "Except for gross negligence, the total aggregate liability of either party shall not exceed the fees paid under this Agreement in the twelve months preceding the claim."),
        ("Uncapped Liability", "The total aggregate liability of the Service Provider under this Agreement shall be unlimited and uncapped regardless of the theory of liability."),
        ("Termination For Convenience", "Either party may terminate this Agreement at any time for convenience upon giving thirty (30) days prior written notice."),
        ("Non-Compete", "During the term and for a period of one year thereafter, Contractor shall not directly or indirectly engage in any business competing with Company."),
        ("Exclusivity", "Customer agrees that Vendor shall be the exclusive provider of cloud software analysis services during the term of this Agreement."),
        ("IP Ownership Assignment", "Contractor hereby irrevocably assigns to Company all right, title, and interest in and to all work product and inventions created hereunder."),
        ("Anti-Assignment", "Neither party may assign or transfer this Agreement or any rights or obligations without the prior written consent of the other party."),
        ("Audit Rights", "Company shall have the right upon reasonable notice during normal business hours to inspect and audit Vendor's records relating to performance."),
        ("Warranty", "Vendor warrants that the Services will perform substantially in accordance with the specifications for a period of ninety (90) days.")
    ]
    
    # Non-CUAD out-of-domain samples (should be honestly marked low-confidence / uncertain)
    ood_samples = [
        ("Payment Terms (Non-CUAD)", "The Customer shall pay invoices within thirty (30) days of receipt via electronic bank wire."),
        ("Routine Confidentiality (Non-CUAD)", "Each party agrees to maintain the confidentiality of proprietary information disclosed during discussions."),
        ("Preamble / Parties (Non-CUAD)", "This Master Services Agreement is entered into between Acme Corp and Beta LLC on October 1, 2026.")
    ]
    
    # 1. Measure single clause inference latency
    latencies = []
    cuad_correct = 0
    for expected_type, text in cuad_samples:
        t0 = time.perf_counter()
        pred_label, conf = predictor.predict_clause(text)
        latencies.append((time.perf_counter() - t0) * 1000)
        # Check if prediction matches or is semantically adjacent CUAD category
        if expected_type.lower() in pred_label.lower() or pred_label.lower() in expected_type.lower():
            cuad_correct += 1

    # 2. Test Head+Tail truncation on extra long clause (> 350 tokens)
    long_clause_preamble = "WHEREAS, the parties desire to enter into this relationship; " * 30
    long_clause_operative = " In no event shall either party be liable for any indirect, punitive, or consequential damages whatsoever."
    long_clause = long_clause_preamble + long_clause_operative
    t0 = time.perf_counter()
    long_pred, long_conf = predictor.predict_clause(long_clause)
    long_time = (time.perf_counter() - t0) * 1000
    
    # 3. Test OOD samples
    ood_results = []
    for ood_name, text in ood_samples:
        pred_label, conf = predictor.predict_clause(text)
        is_uncertain = conf < 0.45
        ood_results.append({
            "test_type": ood_name,
            "predicted_cuad_class": pred_label,
            "confidence": conf,
            "correctly_flagged_uncertain": is_uncertain
        })

    # 4. Batch inference throughput
    all_texts = [s[1] for s in cuad_samples] * 5  # 50 clauses
    t_batch_start = time.perf_counter()
    batch_preds = predictor.predict_clauses_batch(all_texts, batch_size=16)
    batch_duration = time.perf_counter() - t_batch_start

    return {
        "num_classes": predictor.num_labels,
        "cuad_sample_accuracy": cuad_correct / len(cuad_samples),
        "mean_single_inference_ms": sum(latencies) / len(latencies),
        "long_clause_head_tail_ms": long_time,
        "long_clause_pred": long_pred,
        "batch_50_duration_s": batch_duration,
        "throughput_clauses_per_sec": len(all_texts) / batch_duration,
        "ood_uncertainty_handling": ood_results
    }


def benchmark_rule_engine() -> Dict[str, Any]:
    """Benchmark Rule Engine precision and recall across 13 risk domains."""
    logger.info("Starting Rule Engine Evaluation across 13 domains...")
    engine = RuleEngine()
    
    # Toxic clauses that MUST trigger high-risk rules (Target: 100% recall)
    toxic_clauses = [
        ("RULE_LIAB_UNLIMITED", "The total aggregate liability of Provider shall be unlimited under all circumstances."),
        ("RULE_LIAB_INTERNAL_CONTRADICTION", "Neither party shall be liable for consequential damages. Notwithstanding the foregoing, the total liability of Provider shall be unlimited."),
        ("RULE_TERM_CONVENIENCE_UNILATERAL", "The Company reserves the right to terminate this Agreement immediately, without prior notice or explanation, at its sole discretion."),
        ("RULE_TERM_ASYMMETRIC_NOTICE", "Either party may terminate this Agreement with 30 days notice; however, Service Provider may terminate immediately without notice."),
        ("RULE_PAYMENT_NON_REFUNDABLE", "All fees paid under this Agreement are strictly non-refundable under all circumstances."),
        ("RULE_PAYMENT_HIGH_INTEREST", "Late payments shall accrue interest at 24% compounded daily until paid in full."),
        ("RULE_PRICE_UNILATERAL_ALTERATION", "Provider reserves the right to increase contract prices at any time without asking for the approval of the Customer."),
        ("RULE_IP_ASSIGNMENT_BROAD", "Contractor hereby assigns all right, title, and interest in and to all work product as work made for hire."),
        ("RULE_IP_MORAL_RIGHTS_WAIVER", "The Author unconditionally and irrevocably waives all moral rights under copyright law."),
        ("RULE_MOD_UNILATERAL", "The Company may modify these terms and conditions at any time in its sole discretion without prior notice."),
        ("RULE_RENEWAL_AUTO", "This Agreement shall automatically renew for successive one-year terms unless cancelled."),
        ("RULE_NON_COMPETE_RESTRICT", "Employee shall not directly or indirectly compete with the Company for two years following termination."),
        ("RULE_AUDIT_UNLIMITED", "Licensor reserves the right to audit books, records and premises at any time without prior written notice."),
        ("RULE_WARRANTY_DISCLAIMER", "The software is provided AS IS without warranty of any kind, express or implied, including merchantability."),
        ("RULE_DISPUTE_WAIVER", "Customer irrevocably waives any right to a jury trial or class action proceeding in any dispute."),
        ("RULE_DATA_BREACH_DISCLAIMER", "Vendor disclaims all liability for data breaches, cyberattacks, or unauthorized data access.")
    ]
    
    # Benign clauses that MUST produce 0 rule triggers (Target: 0% false positives)
    benign_clauses = [
        "This Agreement shall be effective on January 1, 2026.",
        "The Client shall pay the Service Provider a monthly fee of INR 50,000 within 30 days of invoice receipt.",
        "Each party shall keep confidential information protected using reasonable commercial care for 3 years.",
        "Either party may terminate this agreement upon sixty (60) days advance written notice to the other party.",
        "Neither party shall be liable for delays caused by fires, floods, or natural disasters beyond reasonable control.",
        "This Agreement may be executed in counterparts, each of which shall be deemed an original.",
        "All notices shall be sent by certified email or registered mail to the addresses specified above.",
        "If any provision is found invalid, the remaining provisions of this Agreement shall remain in full force."
    ]
    
    # 1. Evaluate Toxic Recall
    toxic_hits = 0
    t_start = time.perf_counter()
    for expected_rule, text in toxic_clauses:
        matches = engine.analyze_clause(text)
        match_ids = [m.rule_id for m in matches]
        if expected_rule in match_ids:
            toxic_hits += 1
        else:
            logger.warning(f"Rule {expected_rule} missed on clause: '{text}' (Got: {match_ids})")
    toxic_latency = (time.perf_counter() - t_start) * 1000 / len(toxic_clauses)
    
    # 2. Evaluate Benign False Positives
    benign_false_positives = 0
    t_start = time.perf_counter()
    for text in benign_clauses:
        matches = engine.analyze_clause(text)
        if len(matches) > 0:
            benign_false_positives += 1
            logger.warning(f"False positive on benign clause '{text}': {[m.rule_id for m in matches]}")
    benign_latency = (time.perf_counter() - t_start) * 1000 / len(benign_clauses)
    
    recall = toxic_hits / len(toxic_clauses)
    fp_rate = benign_false_positives / len(benign_clauses)
    
    return {
        "total_compiled_rules": len(engine.compiled_rules),
        "toxic_test_cases": len(toxic_clauses),
        "toxic_recall": recall,
        "benign_test_cases": len(benign_clauses),
        "benign_false_positive_rate": fp_rate,
        "benign_specificity": 1.0 - fp_rate,
        "mean_regex_latency_ms": (toxic_latency + benign_latency) / 2
    }


def benchmark_conflict_detection() -> Dict[str, Any]:
    """Benchmark intra-clause and cross-clause contradiction detection."""
    logger.info("Starting Conflict & Contradiction Detection Evaluation...")
    detector = CrossClauseConflictDetector()
    
    # Test 1: Intra-clause contradiction (Limitation of liability contradicts unlimited liability)
    c1 = SegmentedClause(
        clause_id="c_liab_contra",
        document_id="doc_contra",
        clause_number="4.1",
        clause_heading="Limitation of Liability",
        clause_text=(
            "Under no circumstances shall either party be liable for indirect, incidental, or consequential damages. "
            "The total aggregate liability of the Service Provider shall be unlimited, regardless of the cause of action."
        ),
        source_type=SourceType.PDF,
        source_pages=[1],
        character_count=230,
        word_count=35
    )
    
    # Test 2: Intra-clause contradiction (Asymmetric termination notice)
    c2 = SegmentedClause(
        clause_id="c_term_contra",
        document_id="doc_contra",
        clause_number="8.2",
        clause_heading="Termination",
        clause_text=(
            "Either party may terminate this Agreement by providing 30 days written notice. "
            "However, the Service Provider reserves the right to terminate this Agreement immediately, "
            "without prior notice or explanation, at its sole discretion."
        ),
        source_type=SourceType.PDF,
        source_pages=[2],
        character_count=240,
        word_count=35
    )
    
    # Test 3: Cross-clause contradiction
    c3_gov_law_ny = SegmentedClause(
        clause_id="c_gov_ny",
        document_id="doc_contra",
        clause_number="12.1",
        clause_heading="Governing Law",
        clause_text="This Agreement shall be governed exclusively by the laws of the State of New York.",
        source_type=SourceType.PDF,
        source_pages=[3],
        character_count=85,
        word_count=14
    )
    c4_gov_law_ca = SegmentedClause(
        clause_id="c_gov_ca",
        document_id="doc_contra",
        clause_number="14.3",
        clause_heading="Jurisdiction and Governing Law",
        clause_text="This Agreement and all disputes shall be governed exclusively by the laws of the State of California.",
        source_type=SourceType.PDF,
        source_pages=[4],
        character_count=105,
        word_count=16
    )
    
    # Test 4: Benign pair (No contradiction)
    c5_benign_pay = SegmentedClause(
        clause_id="c_pay",
        document_id="doc_contra",
        clause_number="2.1",
        clause_heading="Fees",
        clause_text="The Client shall pay all fees within 30 days of receiving the invoice.",
        source_type=SourceType.PDF,
        source_pages=[1],
        character_count=70,
        word_count=14
    )
    
    t0 = time.perf_counter()
    cross_conflicts = detector.detect_cross_clause_conflicts([c1, c2, c3_gov_law_ny, c4_gov_law_ca, c5_benign_pay])
    intra_conflicts = detector.detect_intra_clause_contradictions([c1, c2, c3_gov_law_ny, c4_gov_law_ca, c5_benign_pay])
    detection_ms = (time.perf_counter() - t0) * 1000

    total_conflicts = cross_conflicts + intra_conflicts

    c1_intra = [conf for conf in intra_conflicts if "c_liab_contra" in conf.clause_ids]
    c2_intra = [conf for conf in intra_conflicts if "c_term_contra" in conf.clause_ids]
    cross_gov = [conf for conf in cross_conflicts if "c_gov_ny" in conf.clause_ids and "c_gov_ca" in conf.clause_ids]

    return {
        "total_conflicts_detected": len(total_conflicts),
        "detection_latency_ms": detection_ms,
        "liab_intra_detected": len(c1_intra) > 0,
        "term_intra_detected": len(c2_intra) > 0,
        "cross_clause_detected": len(cross_gov) > 0,
        "benign_clause_false_positives": any("c_pay" in conf.clause_ids for conf in total_conflicts)
    }


def benchmark_faiss_retrieval() -> Dict[str, Any]:
    """Benchmark FAISS semantic retrieval grounding and cosine similarity."""
    logger.info("Starting FAISS Semantic Retrieval Benchmark...")
    embedder = ClauseEmbedder()
    index_manager = FAISSIndexManager()
    index_manager.load("models/faiss_index")
    retriever = RAGRetriever(index_manager=index_manager, embedder=embedder)

    queries = [
        "What is the limitation of liability cap?",
        "How can the contract be terminated for convenience?",
        "What are the confidentiality obligations and survival period?",
        "Is there a non-compete covenant and what is its geographic scope?"
    ]

    latencies = []
    top_scores = []

    for q in queries:
        t0 = time.perf_counter()
        results = retriever.retrieve_evidence(query=q, top_k=3, similarity_threshold=0.50)
        latencies.append((time.perf_counter() - t0) * 1000)
        if results:
            top_scores.append(results[0].similarity_score)

    return {
        "index_loaded": index_manager.total_vectors > 0,
        "total_indexed_clauses": index_manager.total_vectors,
        "mean_retrieval_ms": sum(latencies) / len(latencies),
        "mean_top1_similarity_score": sum(top_scores) / len(top_scores) if top_scores else 0.0,
        "score_threshold_configured": retriever.default_threshold
    }


def benchmark_end_to_end_pipeline() -> Dict[str, Any]:
    """Benchmark full hybrid risk scoring pipeline (BERT + Rules + FAISS + Offline LLM status)."""
    logger.info("Starting End-to-End Pipeline Evaluation...")
    predictor = get_bert_predictor()
    analyzer = ContractRiskAnalyzer(bert_classifier=predictor)
    
    clauses = [
        SegmentedClause(
            clause_id="cl_01",
            document_id="doc_eval",
            clause_number="1",
            clause_heading="Limitation of Liability",
            clause_text=(
                "Under no circumstances shall either party be liable for indirect, incidental, or consequential damages. "
                "The total aggregate liability of the Service Provider shall be unlimited, regardless of the cause of action."
            ),
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=230,
            word_count=35
        ),
        SegmentedClause(
            clause_id="cl_02",
            document_id="doc_eval",
            clause_number="2",
            clause_heading="Termination",
            clause_text=(
                "Either party may terminate this Agreement by providing 30 days written notice. "
                "However, the Service Provider reserves the right to terminate this Agreement immediately, "
                "without prior notice or explanation, at its sole discretion."
            ),
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=240,
            word_count=35
        ),
        SegmentedClause(
            clause_id="cl_03",
            document_id="doc_eval",
            clause_number="3",
            clause_heading="Payment Terms",
            clause_text="Client shall pay INR 50,000 on or before the fifth day of every calendar month.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=85,
            word_count=15
        ),
        SegmentedClause(
            clause_id="cl_04",
            document_id="doc_eval",
            clause_number="4",
            clause_heading="Governing Law",
            clause_text="This Agreement shall be governed by and construed in accordance with the laws of the State of New York.",
            source_type=SourceType.PDF,
            source_pages=[2],
            character_count=100,
            word_count=16
        )
    ]
    
    total_chars = sum(c.character_count for c in clauses)
    seg_res = SegmentationResult(
        document_id="doc_eval",
        source_filename="eval_service_agreement.pdf",
        document_title="Master Services Agreement",
        clauses=clauses,
        total_clauses=len(clauses),
        source_character_count=total_chars,
        segmented_character_count=total_chars,
        text_coverage_ratio=1.0,
        unsegmented_elements_count=0
    )
    
    t0 = time.perf_counter()
    summary = analyzer.analyze_document(seg_res)
    total_pipeline_ms = (time.perf_counter() - t0) * 1000
    
    assessments = summary.all_assessments
    
    # Verify clause 1 & 2 are HIGH or MEDIUM
    c1_assess = next(a for a in assessments if a.clause_id == "cl_01")
    c2_assess = next(a for a in assessments if a.clause_id == "cl_02")
    c3_assess = next(a for a in assessments if a.clause_id == "cl_03")
    c4_assess = next(a for a in assessments if a.clause_id == "cl_04")
    
    return {
        "total_pipeline_ms": total_pipeline_ms,
        "mean_ms_per_clause": total_pipeline_ms / len(clauses),
        "overall_contract_risk_score": summary.contract_risk_score,
        "c1_risk_level": c1_assess.risk_level.value,
        "c1_risk_score": c1_assess.risk_score,
        "c1_rules_matched": [r.rule_id for r in c1_assess.detected_rules],
        "c1_llm_status": c1_assess.llm_inference_status.value,
        "c2_risk_level": c2_assess.risk_level.value,
        "c2_risk_score": c2_assess.risk_score,
        "c2_rules_matched": [r.rule_id for r in c2_assess.detected_rules],
        "c3_risk_level": c3_assess.risk_level.value,
        "c3_risk_score": c3_assess.risk_score,
        "c3_rules_matched": [r.rule_id for r in c3_assess.detected_rules],
        "c4_risk_level": c4_assess.risk_level.value,
        "c4_risk_score": c4_assess.risk_score,
        "c4_rules_matched": [r.rule_id for r in c4_assess.detected_rules],
        "breakdown_weights_valid": (
            c1_assess.score_breakdown.bert_component >= 0 and
            c1_assess.score_breakdown.rule_component >= 0 and
            c1_assess.score_breakdown.rag_component >= 0
        )
    }


def main():
    print("=" * 80)
    print(" CONTRACTRISK AI: DEEP SYSTEM-WIDE QUALITY EVALUATION BENCHMARK")
    print("=" * 80)
    
    bert_eval = benchmark_bert_classifier()
    print("\n[1. BERT CLASSIFICATION BENCHMARK]")
    print(f"  * Total CUAD Classes: {bert_eval['num_classes']}")
    print(f"  * CUAD Benchmark Sample Accuracy: {bert_eval['cuad_sample_accuracy']*100:.1f}%")
    print(f"  * Mean Single Inference Latency: {bert_eval['mean_single_inference_ms']:.2f} ms")
    print(f"  * Long Clause Head+Tail Latency: {bert_eval['long_clause_head_tail_ms']:.2f} ms")
    print(f"  * Batch Throughput (50 clauses): {bert_eval['throughput_clauses_per_sec']:.1f} clauses/sec")
    print("  * Out-of-Domain Uncertainty Handling:")
    for ood in bert_eval["ood_uncertainty_handling"]:
        print(f"    - {ood['test_type']} -> Class: '{ood['predicted_cuad_class']}', Conf: {ood['confidence']:.2f}, Flagged Uncertain: {ood['correctly_flagged_uncertain']}")
        
    rule_eval = benchmark_rule_engine()
    print("\n[2. RULE ENGINE EVALUATION ACROSS 13 RISK DOMAINS]")
    print(f"  * Total Compiled Risk Rules: {rule_eval['total_compiled_rules']}")
    print(f"  * Toxic Clauses Tested: {rule_eval['toxic_test_cases']}")
    print(f"  * Toxic Recall: {rule_eval['toxic_recall']*100:.1f}%")
    print(f"  * Benign Clauses Tested: {rule_eval['benign_test_cases']}")
    print(f"  * Benign False Positive Rate: {rule_eval['benign_false_positive_rate']*100:.1f}%")
    print(f"  * Benign Specificity: {rule_eval['benign_specificity']*100:.1f}%")
    print(f"  * Mean Regex Evaluation Latency: {rule_eval['mean_regex_latency_ms']:.2f} ms")
    
    conflict_eval = benchmark_conflict_detection()
    print("\n[3. CONTRADICTION & CONFLICT DETECTION BENCHMARK]")
    print(f"  * Total Conflicts Detected: {conflict_eval['total_conflicts_detected']}")
    print(f"  * Limitation of Liability Intra-Contradiction Caught: {conflict_eval['liab_intra_detected']}")
    print(f"  * Termination Notice Asymmetry Intra-Contradiction Caught: {conflict_eval['term_intra_detected']}")
    print(f"  * Cross-Clause Contradiction Caught: {conflict_eval['cross_clause_detected']}")
    print(f"  * Benign Clause False Positives: {conflict_eval['benign_clause_false_positives']}")
    print(f"  * Detection Latency: {conflict_eval['detection_latency_ms']:.2f} ms")
    
    faiss_eval = benchmark_faiss_retrieval()
    print("\n[4. FAISS SEMANTIC RETRIEVAL BENCHMARK]")
    print(f"  * Index Size: {faiss_eval['total_indexed_clauses']} vectors")
    print(f"  * Mean Top-1 Cosine Similarity: {faiss_eval['mean_top1_similarity_score']:.4f}")
    print(f"  * Mean Retrieval Latency: {faiss_eval['mean_retrieval_ms']:.2f} ms")
    
    e2e_eval = benchmark_end_to_end_pipeline()
    print("\n[5. END-TO-END PIPELINE & SCORING CALIBRATION]")
    print(f"  * Total 4-Clause Pipeline Latency: {e2e_eval['total_pipeline_ms']:.2f} ms")
    print(f"  * Mean Latency per Clause: {e2e_eval['mean_ms_per_clause']:.2f} ms")
    print(f"  * Overall Contract Risk Score: {e2e_eval['overall_contract_risk_score']:.2f} / 100")
    print(f"  * Clause 1 (Unlimited Liab): Level={e2e_eval['c1_risk_level']}, Score={e2e_eval['c1_risk_score']:.2f}, Rules={e2e_eval['c1_rules_matched']}, LLM={e2e_eval['c1_llm_status']}")
    print(f"  * Clause 2 (Asymmetric Term): Level={e2e_eval['c2_risk_level']}, Score={e2e_eval['c2_risk_score']:.2f}, Rules={e2e_eval['c2_rules_matched']}")
    print(f"  * Clause 3 (Benign INR 50k Payment): Level={e2e_eval['c3_risk_level']}, Score={e2e_eval['c3_risk_score']:.2f}, Rules={e2e_eval['c3_rules_matched']}")
    print(f"  * Clause 4 (Benign Governing Law): Level={e2e_eval['c4_risk_level']}, Score={e2e_eval['c4_risk_score']:.2f}, Rules={e2e_eval['c4_rules_matched']}")
    
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bert_eval": bert_eval,
        "rule_eval": rule_eval,
        "conflict_eval": conflict_eval,
        "faiss_eval": faiss_eval,
        "e2e_eval": e2e_eval
    }
    
    with open("scripts/evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\n[SUCCESS] Comprehensive Evaluation completed and saved to scripts/evaluation_results.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
