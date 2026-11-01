"""
Generate all system architecture and UML diagrams for ContractRisk AI documentation.
Saves high-resolution PNGs in reports/diagrams/.
"""

import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle

OUT_DIR = os.path.join("reports", "diagrams")
os.makedirs(OUT_DIR, exist_ok=True)

# Colors matching Navy, Teal, White palette
NAVY_DARK = "#0f2744"
NAVY_MED = "#1e3a8a"
NAVY_LIGHT = "#3b82f6"
TEAL_DARK = "#0f766e"
TEAL_MED = "#0d9488"
TEAL_LIGHT = "#14b8a6"
SLATE_DARK = "#1e293b"
SLATE_MED = "#475569"
SLATE_LIGHT = "#f1f5f9"
WHITE = "#ffffff"
AMBER = "#f59e0b"
RED = "#ef4444"
GREEN = "#10b981"


def create_system_architecture():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=220)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    # Title
    ax.text(6, 7.2, "ContractRisk AI — System Architecture Diagram", 
            ha="center", va="center", fontsize=15, fontweight="bold", color=NAVY_DARK)

    # 1. Presentation Layer (Top)
    p_layer = FancyBboxPatch((0.5, 5.7), 11, 1.1, boxstyle="round,pad=0.1", 
                             ec=TEAL_MED, fc="#f0fdfa", lw=1.5)
    ax.add_patch(p_layer)
    ax.text(0.7, 6.55, "PRESENTATION LAYER (Streamlit Frontend)", fontsize=10, fontweight="bold", color=TEAL_DARK)

    components_p = [
        ("PDF/DOCX Uploader", 1.8),
        ("State Machine (5 States)", 4.6),
        ("8-Stage Progress View", 7.4),
        ("Executive Results Dashboard", 10.1)
    ]
    for name, x in components_p:
        box = FancyBboxPatch((x-1.1, 5.85), 2.2, 0.55, boxstyle="round,pad=0.05", ec=TEAL_MED, fc=WHITE, lw=1)
        ax.add_patch(box)
        ax.text(x, 6.12, name, ha="center", va="center", fontsize=8.5, fontweight="bold", color=SLATE_DARK)

    # Arrow Down
    ax.annotate("", xy=(6, 5.3), xytext=(6, 5.7),
                arrowprops=dict(arrowstyle="->", lw=2, color=NAVY_MED))
    ax.text(6.1, 5.5, "HTTP REST / Multipart Upload", fontsize=8, color=SLATE_MED)

    # 2. API Gateway & Controller Layer
    api_layer = FancyBboxPatch((0.5, 4.3), 11, 0.95, boxstyle="round,pad=0.1", 
                              ec=NAVY_LIGHT, fc="#eff6ff", lw=1.5)
    ax.add_patch(api_layer)
    ax.text(0.7, 5.0, "API GATEWAY LAYER (FastAPI & Uvicorn)", fontsize=10, fontweight="bold", color=NAVY_MED)

    components_api = [
        ("POST /api/v1/analyze", 2.2),
        ("GET /progress/{task_id}", 5.0),
        ("GET /models", 7.6),
        ("GET /documents", 10.0)
    ]
    for name, x in components_api:
        box = FancyBboxPatch((x-1.1, 4.45), 2.2, 0.45, boxstyle="round,pad=0.05", ec=NAVY_LIGHT, fc=WHITE, lw=1)
        ax.add_patch(box)
        ax.text(x, 4.67, name, ha="center", va="center", fontsize=8, fontweight="bold", color=NAVY_MED)

    # Arrow Down
    ax.annotate("", xy=(6, 3.8), xytext=(6, 4.3),
                arrowprops=dict(arrowstyle="->", lw=2, color=NAVY_MED))

    # 3. Core Processing & Hybrid AI Intelligence Layer
    ai_layer = FancyBboxPatch((0.5, 1.4), 11, 2.3, boxstyle="round,pad=0.1", 
                             ec=NAVY_DARK, fc="#f8fafc", lw=1.5)
    ax.add_patch(ai_layer)
    ax.text(0.7, 3.45, "PROCESSING & HYBRID AI INFERENCE CORE", fontsize=10, fontweight="bold", color=NAVY_DARK)

    # Document Extraction & Segmentation Box
    doc_box = FancyBboxPatch((0.8, 1.6), 2.4, 1.6, boxstyle="round,pad=0.05", ec=SLATE_MED, fc=WHITE, lw=1)
    ax.add_patch(doc_box)
    ax.text(2.0, 3.0, "1. Document Ingestion", ha="center", fontsize=9, fontweight="bold", color=NAVY_DARK)
    ax.text(2.0, 2.65, "• PyMuPDF Extractor\n• python-docx Parser\n• Text Normalizer\n• Clause Segmenter", 
            ha="center", va="center", fontsize=7.5, color=SLATE_DARK)

    # BERT Classification Box
    bert_box = FancyBboxPatch((3.5, 1.6), 2.3, 1.6, boxstyle="round,pad=0.05", ec=NAVY_MED, fc="#f0f7ff", lw=1)
    ax.add_patch(bert_box)
    ax.text(4.65, 3.0, "2. BERT Classifier", ha="center", fontsize=9, fontweight="bold", color=NAVY_MED)
    ax.text(4.65, 2.65, "• bert-base-uncased\n• Fine-Tuned (41 Classes)\n• Batch Tensor Head\n• Softmax Confidence", 
            ha="center", va="center", fontsize=7.5, color=SLATE_DARK)

    # Rules & Scoring Box
    rule_box = FancyBboxPatch((6.1, 1.6), 2.4, 1.6, boxstyle="round,pad=0.05", ec=TEAL_DARK, fc="#f0fdfa", lw=1)
    ax.add_patch(rule_box)
    ax.text(7.3, 3.0, "3. Rule & Scorer Core", ha="center", fontsize=9, fontweight="bold", color=TEAL_DARK)
    ax.text(7.3, 2.65, "• RuleEngine (16 Domains)\n• Conflict Detector\n• Deterministic Hybrid\n  Scorer (30/35/15/20)", 
            ha="center", va="center", fontsize=7.5, color=SLATE_DARK)

    # RAG & Local Qwen3 Box
    rag_box = FancyBboxPatch((8.8, 1.6), 2.4, 1.6, boxstyle="round,pad=0.05", ec=AMBER, fc="#fffbeb", lw=1)
    ax.add_patch(rag_box)
    ax.text(10.0, 3.0, "4. RAG & Qwen3 LLM", ha="center", fontsize=9, fontweight="bold", color="#b45309")
    ax.text(10.0, 2.65, "• all-MiniLM-L6-v2\n• FAISS IndexFlatIP\n• Qwen3 4B Instruct\n  (LM Studio Local GGUF)\n• Scenario Predictor", 
            ha="center", va="center", fontsize=7.5, color=SLATE_DARK)

    # 4. Persistence Layer (Bottom)
    ax.annotate("", xy=(6, 1.05), xytext=(6, 1.4),
                arrowprops=dict(arrowstyle="->", lw=2, color=NAVY_MED))

    db_layer = FancyBboxPatch((0.5, 0.2), 11, 0.8, boxstyle="round,pad=0.1", 
                             ec="#64748b", fc="#f8fafc", lw=1.5)
    ax.add_patch(db_layer)
    ax.text(0.7, 0.75, "DATA PERSISTENCE LAYER (PostgreSQL 15+ & SQLAlchemy 2.x ORM)", fontsize=9.5, fontweight="bold", color=SLATE_DARK)
    ax.text(6.0, 0.45, "Tables: documents | clauses | risk_assessments | rule_matches | evidence_citations | future_scenarios | contract_summaries", 
            ha="center", fontsize=8, color=SLATE_MED)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "arch_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_workflow_diagram():
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=220)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    ax.text(5.5, 8.2, "ContractRisk AI — Complete End-to-End Pipeline Execution Flow", 
            ha="center", va="center", fontsize=14, fontweight="bold", color=NAVY_DARK)

    stages = [
        ("1. User Contract Upload", "Streamlit UI receives PDF/DOCX file\nSHA-256 hash computed, size verified (<=20MB)", "#eff6ff", NAVY_MED),
        ("2. Document Extraction & Normalization", "PyMuPDF / python-docx extracts elements\nWhitespace, unicode, quotes normalized", "#f0fdfa", TEAL_DARK),
        ("3. Clause Segmentation", "Header regex & numbering detect boundaries\nProduces hierarchical SegmentedClause objects", "#f8fafc", SLATE_DARK),
        ("4. Batched BERT Clause Classification", "Single batched PyTorch tensor forward pass\nPredicts 1 of 41 classes + softmax probability", "#f0f7ff", NAVY_MED),
        ("5. Rule-Based Pattern Matching", "16-domain regex patterns evaluate clauses\nCalculates asymptotic rule component score", "#f0fdfa", TEAL_DARK),
        ("6. Dense Embeddings & FAISS Retrieval", "SentenceTransformer all-MiniLM-L6-v2 encodes\nFAISS IndexFlatIP retrieves top-3 precedents", "#fffbeb", "#b45309"),
        ("7. Conditional Qwen3 Deep Analysis", "Executed ONLY for risky candidate clauses\nGenerates grounded explanation & scenario", "#fff7ed", "#c2410c"),
        ("8. Deterministic Hybrid Risk Scoring", "Score = 0.30*BERT + 0.35*Rule + 0.15*RAG + 0.20*LLM\nMaps to LOW (<35), MEDIUM (35-69), HIGH (>=70)", "#f0fdfa", TEAL_DARK),
        ("9. Cross-Clause Conflict Detection", "Identifies cross-clause contradictions\n(e.g. warranty vs disclaimer, price vs term)", "#fef2f2", RED),
        ("10. Combined Future Scenario Generation", "Consolidates top contract risks into single coherent,\ngrounded scenario with conditional phrasing", "#fdf4ff", "#86198f"),
        ("11. Relational Database Persistence", "Single batched transaction flushes to PostgreSQL\nAtomic commit guarantees data consistency", "#f8fafc", SLATE_DARK),
        ("12. Executive Results Dashboard", "Frontend transitions to terminal view:\nSummary -> Problem Clauses -> Combined Scenario", "#ecfdf5", GREEN),
    ]

    y = 7.6
    for i, (title, desc, bg, border_col) in enumerate(stages):
        box = FancyBboxPatch((1.2, y - 0.42), 8.6, 0.46, boxstyle="round,pad=0.04", 
                             ec=border_col, fc=bg, lw=1.2)
        ax.add_patch(box)
        ax.text(1.5, y - 0.12, title, fontsize=8.5, fontweight="bold", color=border_col)
        ax.text(1.5, y - 0.30, desc, fontsize=7.2, color=SLATE_DARK)

        if i < len(stages) - 1:
            ax.annotate("", xy=(5.5, y - 0.52), xytext=(5.5, y - 0.42),
                        arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
        y -= 0.58

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "workflow_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_use_case_diagram():
    fig, ax = plt.subplots(figsize=(10, 6), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    ax.text(5, 5.7, "UML Use Case Diagram — ContractRisk AI", ha="center", fontsize=14, fontweight="bold", color=NAVY_DARK)

    # Actor: User
    ax.plot([1.2, 1.2], [4.2, 3.4], color=NAVY_MED, lw=2)  # body
    ax.plot([0.8, 1.6], [3.9, 3.9], color=NAVY_MED, lw=2)  # arms
    ax.plot([1.2, 0.8], [3.4, 2.7], color=NAVY_MED, lw=2)  # left leg
    ax.plot([1.2, 1.6], [3.4, 2.7], color=NAVY_MED, lw=2)  # right leg
    head = plt.Circle((1.2, 4.45), 0.25, color=NAVY_MED, fill=False, lw=2)
    ax.add_patch(head)
    ax.text(1.2, 2.4, "Contract Reviewer /\nLegal Analyst", ha="center", fontsize=9, fontweight="bold", color=SLATE_DARK)

    # System boundary box
    sys_box = FancyBboxPatch((2.6, 0.5), 6.8, 4.9, boxstyle="round,pad=0.1", ec=NAVY_MED, fc="#f8fafc", lw=1.5)
    ax.add_patch(sys_box)
    ax.text(6.0, 5.15, "ContractRisk AI System Boundary", ha="center", fontsize=10, fontweight="bold", color=NAVY_MED)

    use_cases = [
        ("Upload Contract Document (PDF/DOCX)", 4.5),
        ("Initiate Contract Analysis", 3.7),
        ("Monitor Real-Time Execution Progress", 2.9),
        ("View Overall Risk Summary & Score", 2.1),
        ("Inspect Problematic Clauses & Explanations", 1.3),
        ("Read Evidence-Grounded Future Scenario", 0.6)
    ]

    for uc_text, y in use_cases:
        ellipse = patches.Ellipse((6.0, y + 0.15), 4.8, 0.5, ec=TEAL_DARK, fc=WHITE, lw=1.2)
        ax.add_patch(ellipse)
        ax.text(6.0, y + 0.15, uc_text, ha="center", va="center", fontsize=8, fontweight="bold", color=SLATE_DARK)
        # Line from actor
        ax.plot([1.6, 3.6], [3.9, y + 0.15], color=NAVY_LIGHT, lw=1, ls="--")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "use_case_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_dfd_level0():
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.5)
    ax.axis("off")

    ax.text(5, 4.1, "Data Flow Diagram (DFD Level 0) — Context Diagram", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    # External Entity: User
    u_box = FancyBboxPatch((0.6, 1.5), 2.2, 1.6, boxstyle="square,pad=0", ec=SLATE_DARK, fc="#f1f5f9", lw=1.5)
    ax.add_patch(u_box)
    ax.text(1.7, 2.3, "EXTERNAL ENTITY\n\nUser /\nContract Reviewer", ha="center", va="center", fontsize=9, fontweight="bold", color=SLATE_DARK)

    # Process 0: ContractRisk AI
    p_circ = plt.Circle((5.0, 2.3), 1.3, ec=NAVY_MED, fc="#eff6ff", lw=2)
    ax.add_patch(p_circ)
    ax.text(5.0, 2.45, "PROCESS 0\n\nContractRisk AI\nHybrid Analysis\nSystem", ha="center", va="center", fontsize=9, fontweight="bold", color=NAVY_MED)

    # Data Store: Database
    d_box = FancyBboxPatch((7.6, 1.5), 2.0, 1.6, boxstyle="square,pad=0", ec=TEAL_DARK, fc="#f0fdfa", lw=1.5)
    ax.add_patch(d_box)
    ax.text(8.6, 2.3, "DATA STORE\n\nPostgreSQL 15+\nContract DB", ha="center", va="center", fontsize=9, fontweight="bold", color=TEAL_DARK)

    # Arrows User -> Process
    ax.annotate("", xy=(3.7, 2.6), xytext=(2.8, 2.6), arrowprops=dict(arrowstyle="->", lw=1.5, color=NAVY_MED))
    ax.text(3.25, 2.75, "Contract File\n(PDF/DOCX)", ha="center", fontsize=7.5, color=SLATE_MED)

    # Arrows Process -> User
    ax.annotate("", xy=(2.8, 1.9), xytext=(3.7, 1.9), arrowprops=dict(arrowstyle="->", lw=1.5, color=NAVY_MED))
    ax.text(3.25, 1.65, "Risk Assessments &\nScenarios", ha="center", fontsize=7.5, color=SLATE_MED)

    # Arrows Process -> DB
    ax.annotate("", xy=(7.6, 2.6), xytext=(6.3, 2.6), arrowprops=dict(arrowstyle="->", lw=1.5, color=TEAL_DARK))
    ax.text(6.95, 2.75, "Persist Results &\nMetadata", ha="center", fontsize=7.5, color=TEAL_DARK)

    # Arrows DB -> Process
    ax.annotate("", xy=(6.3, 1.9), xytext=(7.6, 1.9), arrowprops=dict(arrowstyle="->", lw=1.5, color=TEAL_DARK))
    ax.text(6.95, 1.65, "Query History &\nDocuments", ha="center", fontsize=7.5, color=TEAL_DARK)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "dfd_l0_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_dfd_level1():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=220)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7)
    ax.axis("off")

    ax.text(5.5, 6.7, "Data Flow Diagram (DFD Level 1) — Decomposed System Flow", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    # Processes
    procs = [
        ("1.0 Ingest &\nSegment", 1.8, 5.2),
        ("2.0 Classify\n(BERT)", 5.5, 5.2),
        ("3.0 Detect Rules\n& Conflicts", 9.0, 5.2),
        ("4.0 Vector\nRetrieval (RAG)", 9.0, 2.5),
        ("5.0 Score &\nSynthesize", 5.5, 2.5),
        ("6.0 Persist &\nDisplay", 1.8, 2.5),
    ]

    for title, x, y in procs:
        circ = plt.Circle((x, y), 0.9, ec=NAVY_MED, fc="#eff6ff", lw=1.5)
        ax.add_patch(circ)
        ax.text(x, y, title, ha="center", va="center", fontsize=8, fontweight="bold", color=NAVY_MED)

    # Connections
    # 1.0 -> 2.0
    ax.annotate("", xy=(4.6, 5.2), xytext=(2.7, 5.2), arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE_MED))
    ax.text(3.65, 5.4, "Segmented Clauses", ha="center", fontsize=7, color=SLATE_MED)

    # 2.0 -> 3.0
    ax.annotate("", xy=(8.1, 5.2), xytext=(6.4, 5.2), arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE_MED))
    ax.text(7.25, 5.4, "Class & Softmax", ha="center", fontsize=7, color=SLATE_MED)

    # 3.0 -> 4.0
    ax.annotate("", xy=(9.0, 3.4), xytext=(9.0, 4.3), arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE_MED))
    ax.text(9.5, 3.85, "Rule Matches", va="center", fontsize=7, color=SLATE_MED)

    # 4.0 -> 5.0
    ax.annotate("", xy=(6.4, 2.5), xytext=(8.1, 2.5), arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE_MED))
    ax.text(7.25, 2.7, "Precedents & Context", ha="center", fontsize=7, color=SLATE_MED)

    # 5.0 -> 6.0
    ax.annotate("", xy=(2.7, 2.5), xytext=(4.6, 2.5), arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE_MED))
    ax.text(3.65, 2.7, "Scores & Scenarios", ha="center", fontsize=7, color=SLATE_MED)

    # Data Stores
    # FAISS Store
    faiss_box = FancyBboxPatch((8.0, 0.4), 2.0, 0.8, boxstyle="square,pad=0", ec=AMBER, fc="#fffbeb", lw=1.2)
    ax.add_patch(faiss_box)
    ax.text(9.0, 0.8, "D1: FAISS Index\n(9,447 Vectors)", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#b45309")
    ax.annotate("", xy=(9.0, 1.6), xytext=(9.0, 1.2), arrowprops=dict(arrowstyle="->", lw=1.2, color=AMBER))

    # PostgreSQL Store
    pg_box = FancyBboxPatch((0.8, 0.4), 2.0, 0.8, boxstyle="square,pad=0", ec=TEAL_DARK, fc="#f0fdfa", lw=1.2)
    ax.add_patch(pg_box)
    ax.text(1.8, 0.8, "D2: PostgreSQL DB\n(7 Tables)", ha="center", va="center", fontsize=7.5, fontweight="bold", color=TEAL_DARK)
    ax.annotate("", xy=(1.8, 1.2), xytext=(1.8, 1.6), arrowprops=dict(arrowstyle="->", lw=1.2, color=TEAL_DARK))

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "dfd_l1_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_activity_diagram():
    fig, ax = plt.subplots(figsize=(9, 7.5), dpi=220)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    ax.text(4.5, 7.2, "UML Activity Diagram — Contract Analysis Workflow", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    # Initial Node
    start_c = plt.Circle((4.5, 6.7), 0.15, color=NAVY_DARK)
    ax.add_patch(start_c)

    activities = [
        ("Upload Contract (PDF/DOCX)", 6.0),
        ("Validate File Format & Size", 5.3),
        ("Segment Document into Numbered Clauses", 4.6),
        ("Run Batched BERT & Rule Pattern Engine", 3.9),
    ]

    for act, y in activities:
        box = FancyBboxPatch((2.2, y - 0.22), 4.6, 0.44, boxstyle="round,pad=0.08", ec=NAVY_MED, fc="#eff6ff", lw=1.2)
        ax.add_patch(box)
        ax.text(4.5, y, act, ha="center", va="center", fontsize=8, fontweight="bold", color=SLATE_DARK)

    # Arrows between top activities
    ax.annotate("", xy=(4.5, 6.22), xytext=(4.5, 6.55), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    ax.annotate("", xy=(4.5, 5.52), xytext=(4.5, 5.78), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    ax.annotate("", xy=(4.5, 4.82), xytext=(4.5, 5.08), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    ax.annotate("", xy=(4.5, 4.12), xytext=(4.5, 4.38), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))

    # Decision Diamond
    ax.annotate("", xy=(4.5, 3.4), xytext=(4.5, 3.68), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    diamond = patches.Polygon([[4.5, 3.4], [5.6, 3.0], [4.5, 2.6], [3.4, 3.0]], ec=AMBER, fc="#fffbeb", lw=1.2)
    ax.add_patch(diamond)
    ax.text(4.5, 3.0, "Risky Clause\nDetected?", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#b45309")

    # True Branch -> Deep Qwen3
    ax.annotate("", xy=(7.0, 3.0), xytext=(5.6, 3.0), arrowprops=dict(arrowstyle="->", lw=1.2, color=AMBER))
    ax.text(6.3, 3.15, "[Yes]", fontsize=7.5, fontweight="bold", color=AMBER)
    deep_box = FancyBboxPatch((6.2, 1.8), 2.4, 0.6, boxstyle="round,pad=0.08", ec=AMBER, fc="#fff7ed", lw=1.2)
    ax.add_patch(deep_box)
    ax.text(7.4, 2.1, "Deep Qwen3 Analysis &\nScenario Generation", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#c2410c")

    # False Branch -> Skip LLM
    ax.annotate("", xy=(2.0, 3.0), xytext=(3.4, 3.0), arrowprops=dict(arrowstyle="->", lw=1.2, color=SLATE_MED))
    ax.text(2.6, 3.15, "[No / Routine]", fontsize=7.5, fontweight="bold", color=SLATE_MED)
    fast_box = FancyBboxPatch((0.8, 1.8), 2.4, 0.6, boxstyle="round,pad=0.08", ec=TEAL_MED, fc="#f0fdfa", lw=1.2)
    ax.add_patch(fast_box)
    ax.text(2.0, 2.1, "Fast-Pass Deterministic\nScoring (0 LLM Calls)", ha="center", va="center", fontsize=7.5, fontweight="bold", color=TEAL_DARK)

    # Merge into Aggregate & Display
    merge_bar = FancyBboxPatch((2.2, 1.1), 4.6, 0.44, boxstyle="round,pad=0.08", ec=NAVY_DARK, fc="#f8fafc", lw=1.2)
    ax.add_patch(merge_bar)
    ax.text(4.5, 1.32, "Aggregate Hybrid Scores & Persist to DB", ha="center", va="center", fontsize=8, fontweight="bold", color=NAVY_DARK)

    ax.annotate("", xy=(3.5, 1.54), xytext=(2.0, 1.8), arrowprops=dict(arrowstyle="->", lw=1.2, color=SLATE_MED))
    ax.annotate("", xy=(5.5, 1.54), xytext=(7.4, 1.8), arrowprops=dict(arrowstyle="->", lw=1.2, color=SLATE_MED))

    # End Node
    ax.annotate("", xy=(4.5, 0.55), xytext=(4.5, 1.1), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_DARK))
    end_outer = plt.Circle((4.5, 0.35), 0.2, color=NAVY_DARK, fill=False, lw=1.5)
    end_inner = plt.Circle((4.5, 0.35), 0.12, color=NAVY_DARK)
    ax.add_patch(end_outer)
    ax.add_patch(end_inner)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "activity_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_sequence_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=220)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    ax.text(5.5, 7.1, "UML Sequence Diagram — Contract Analysis Execution", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    lifelines = [
        ("Streamlit\nFrontend", 1.2),
        ("FastAPI\nBackend", 3.6),
        ("ContractRisk\nAnalyzer", 6.0),
        ("BERT/FAISS/\nQwen3 Engines", 8.4),
        ("PostgreSQL\nDatabase", 10.2)
    ]

    for name, x in lifelines:
        box = FancyBboxPatch((x - 0.7, 6.2), 1.4, 0.6, boxstyle="round,pad=0.04", ec=NAVY_MED, fc="#eff6ff", lw=1.2)
        ax.add_patch(box)
        ax.text(x, 6.5, name, ha="center", va="center", fontsize=7.5, fontweight="bold", color=NAVY_MED)
        ax.plot([x, x], [0.6, 6.2], color=SLATE_LIGHT, lw=1.2, ls="--")

    calls = [
        (5.7, 1.2, 3.6, "1: POST /api/v1/analyze (file multipart)", NAVY_DARK),
        (5.2, 3.6, 6.0, "2: analyze_document(SegmentedDoc)", NAVY_MED),
        (4.7, 6.0, 8.4, "3: Batched BERT predict + FAISS search", TEAL_DARK),
        (4.2, 8.4, 6.0, "4: Return labels, confidences, precedents", TEAL_DARK),
        (3.6, 6.0, 8.4, "5: Query Qwen3 (only for risky clauses)", AMBER),
        (3.1, 8.4, 6.0, "6: Return grounded explanations & scenarios", AMBER),
        (2.5, 6.0, 3.6, "7: ContractRiskSummary aggregated", NAVY_MED),
        (1.9, 3.6, 10.2, "8: Single-transaction persist_contract_analysis()", GREEN),
        (1.4, 10.2, 3.6, "9: Transaction committed (ACID)", GREEN),
        (0.9, 3.6, 1.2, "10: 200 OK AnalysisResponse (JSON)", NAVY_DARK)
    ]

    for y, x1, x2, msg, col in calls:
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color=col))
        mid = (x1 + x2) / 2
        ax.text(mid, y + 0.12, msg, ha="center", fontsize=6.8, fontweight="bold", color=col)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "sequence_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_erd_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=220)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    ax.text(5.5, 7.1, "Entity Relationship Diagram (ERD) — PostgreSQL Schema", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    # 1. documents table
    d_box = FancyBboxPatch((0.6, 4.4), 2.8, 2.3, boxstyle="round,pad=0.05", ec=NAVY_DARK, fc=WHITE, lw=1.5)
    ax.add_patch(d_box)
    header = FancyBboxPatch((0.6, 6.25), 2.8, 0.45, boxstyle="round,pad=0.05", ec=NAVY_DARK, fc=NAVY_DARK, lw=1.5)
    ax.add_patch(header)
    ax.text(2.0, 6.47, "documents", ha="center", va="center", fontsize=8.5, fontweight="bold", color=WHITE)
    ax.text(0.8, 5.3, "PK  id (INTEGER)\nUQ  document_id (VARCHAR)\n    filename (VARCHAR)\n    document_type (VARCHAR)\n    uploaded_at (DATETIME)\n    clause_count (INTEGER)\n    processing_status (VARCHAR)", 
            fontsize=7, color=SLATE_DARK)

    # 2. clauses table
    c_box = FancyBboxPatch((4.2, 4.4), 2.8, 2.3, boxstyle="round,pad=0.05", ec=NAVY_MED, fc=WHITE, lw=1.5)
    ax.add_patch(c_box)
    header = FancyBboxPatch((4.2, 6.25), 2.8, 0.45, boxstyle="round,pad=0.05", ec=NAVY_MED, fc=NAVY_MED, lw=1.5)
    ax.add_patch(header)
    ax.text(5.6, 6.47, "clauses", ha="center", va="center", fontsize=8.5, fontweight="bold", color=WHITE)
    ax.text(4.4, 5.3, "PK  id (INTEGER)\nFK  document_id (VARCHAR)\n    clause_id (VARCHAR)\n    clause_number (VARCHAR)\n    clause_title (VARCHAR)\n    clause_text (TEXT)\n    sequence_number (INT)", 
            fontsize=7, color=SLATE_DARK)

    # 3. risk_assessments table
    r_box = FancyBboxPatch((7.8, 4.4), 2.8, 2.3, boxstyle="round,pad=0.05", ec=TEAL_DARK, fc=WHITE, lw=1.5)
    ax.add_patch(r_box)
    header = FancyBboxPatch((7.8, 6.25), 2.8, 0.45, boxstyle="round,pad=0.05", ec=TEAL_DARK, fc=TEAL_DARK, lw=1.5)
    ax.add_patch(header)
    ax.text(9.2, 6.47, "risk_assessments", ha="center", va="center", fontsize=8.5, fontweight="bold", color=WHITE)
    ax.text(8.0, 5.3, "PK  id (INTEGER)\nFK  clause_db_id (INTEGER, UQ)\n    risk_category (VARCHAR)\n    risk_level (VARCHAR)\n    final_score (FLOAT)\n    bert_score / rule_score\n    rag_score / llm_score", 
            fontsize=7, color=SLATE_DARK)

    # Bottom tables
    # 4. contract_summaries
    s_box = FancyBboxPatch((0.6, 1.2), 2.8, 2.1, boxstyle="round,pad=0.05", ec=SLATE_MED, fc=WHITE, lw=1.5)
    ax.add_patch(s_box)
    header = FancyBboxPatch((0.6, 2.85), 2.8, 0.45, boxstyle="round,pad=0.05", ec=SLATE_MED, fc=SLATE_MED, lw=1.5)
    ax.add_patch(header)
    ax.text(2.0, 3.07, "contract_summaries", ha="center", va="center", fontsize=8.5, fontweight="bold", color=WHITE)
    ax.text(0.8, 2.0, "PK  id (INTEGER)\nFK  document_id (VARCHAR)\n    risk_score (FLOAT)\n    risk_level (VARCHAR)\n    high_risk_count (INT)\n    medium_risk_count (INT)\n    low_risk_count (INT)", 
            fontsize=7, color=SLATE_DARK)

    # 5. rule_matches
    rm_box = FancyBboxPatch((4.2, 1.2), 2.8, 2.1, boxstyle="round,pad=0.05", ec=AMBER, fc=WHITE, lw=1.5)
    ax.add_patch(rm_box)
    header = FancyBboxPatch((4.2, 2.85), 2.8, 0.45, boxstyle="round,pad=0.05", ec=AMBER, fc=AMBER, lw=1.5)
    ax.add_patch(header)
    ax.text(5.6, 3.07, "rule_matches", ha="center", va="center", fontsize=8.5, fontweight="bold", color=WHITE)
    ax.text(4.4, 2.0, "PK  id (INTEGER)\nFK  risk_assessment_id (INT)\n    rule_id (VARCHAR)\n    category (VARCHAR)\n    severity (FLOAT)\n    matched_text (TEXT)", 
            fontsize=7, color=SLATE_DARK)

    # 6. future_scenarios
    fs_box = FancyBboxPatch((7.8, 1.2), 2.8, 2.1, boxstyle="round,pad=0.05", ec="#8b5cf6", fc=WHITE, lw=1.5)
    ax.add_patch(fs_box)
    header = FancyBboxPatch((7.8, 2.85), 2.8, 0.45, boxstyle="round,pad=0.05", ec="#8b5cf6", fc="#8b5cf6", lw=1.5)
    ax.add_patch(header)
    ax.text(9.2, 3.07, "future_scenarios", ha="center", va="center", fontsize=8.5, fontweight="bold", color=WHITE)
    ax.text(8.0, 2.0, "PK  id (INTEGER)\nFK  risk_assessment_id (INT, UQ)\n    scenario_title (VARCHAR)\n    trigger_condition (TEXT)\n    scenario_description (TEXT)\n    possible_consequence (TEXT)", 
            fontsize=7, color=SLATE_DARK)

    # Relationship Lines
    # documents -> clauses (1 : N)
    ax.annotate("", xy=(4.2, 5.5), xytext=(3.4, 5.5), arrowprops=dict(arrowstyle="->", lw=1.5, color=NAVY_DARK))
    ax.text(3.8, 5.65, "1 : N", ha="center", fontsize=7.5, fontweight="bold", color=NAVY_DARK)

    # clauses -> risk_assessments (1 : 1)
    ax.annotate("", xy=(7.8, 5.5), xytext=(7.0, 5.5), arrowprops=dict(arrowstyle="->", lw=1.5, color=NAVY_MED))
    ax.text(7.4, 5.65, "1 : 1", ha="center", fontsize=7.5, fontweight="bold", color=NAVY_MED)

    # documents -> contract_summaries (1 : N)
    ax.annotate("", xy=(2.0, 3.3), xytext=(2.0, 4.4), arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE_MED))
    ax.text(2.2, 3.85, "1 : N", fontsize=7.5, fontweight="bold", color=SLATE_MED)

    # risk_assessments -> rule_matches (1 : N)
    ax.annotate("", xy=(6.5, 3.3), xytext=(8.0, 4.4), arrowprops=dict(arrowstyle="->", lw=1.5, color=AMBER))
    ax.text(7.1, 3.85, "1 : N", fontsize=7.5, fontweight="bold", color=AMBER)

    # risk_assessments -> future_scenarios (1 : 1)
    ax.annotate("", xy=(9.2, 3.3), xytext=(9.2, 4.4), arrowprops=dict(arrowstyle="->", lw=1.5, color="#8b5cf6"))
    ax.text(9.4, 3.85, "1 : 1", fontsize=7.5, fontweight="bold", color="#8b5cf6")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "erd_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_component_diagram():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    ax.text(5, 6.1, "UML Component Diagram — ContractRisk AI Modular Structure", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    comps = [
        ("Frontend UI Component\n(Streamlit Views)", 2.2, 4.8, TEAL_MED, "#f0fdfa"),
        ("REST API Controller\n(FastAPI Routers)", 5.0, 4.8, NAVY_MED, "#eff6ff"),
        ("Document Ingestion Component\n(PyMuPDF / Segmenter)", 7.8, 4.8, SLATE_MED, "#f8fafc"),
        ("BERT Classifier Component\n(Fine-Tuned Checkpoint)", 2.2, 2.5, NAVY_DARK, "#f0f7ff"),
        ("Hybrid Risk Analyzer\n(Scoring Engine & Rules)", 5.0, 2.5, TEAL_DARK, "#f0fdfa"),
        ("Vector Search & RAG\n(FAISS Index & Embedder)", 7.8, 2.5, AMBER, "#fffbeb"),
        ("Database Repository Component\n(SQLAlchemy ORM)", 3.6, 0.8, SLATE_DARK, "#f8fafc"),
        ("Local LLM Generator\n(Qwen3 via LM Studio)", 6.4, 0.8, "#c2410c", "#fff7ed")
    ]

    for title, x, y, border_col, bg_col in comps:
        box = FancyBboxPatch((x - 1.1, y - 0.5), 2.2, 1.0, boxstyle="round,pad=0.06", ec=border_col, fc=bg_col, lw=1.3)
        ax.add_patch(box)
        ax.text(x, y, title, ha="center", va="center", fontsize=7.5, fontweight="bold", color=border_col)

    # Connections
    ax.annotate("", xy=(3.9, 4.8), xytext=(3.3, 4.8), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    ax.annotate("", xy=(6.7, 4.8), xytext=(6.1, 4.8), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    ax.annotate("", xy=(5.0, 3.5), xytext=(5.0, 4.3), arrowprops=dict(arrowstyle="->", lw=1.2, color=NAVY_MED))
    ax.annotate("", xy=(3.3, 2.5), xytext=(3.9, 2.5), arrowprops=dict(arrowstyle="<-", lw=1.2, color=TEAL_DARK))
    ax.annotate("", xy=(6.7, 2.5), xytext=(6.1, 2.5), arrowprops=dict(arrowstyle="->", lw=1.2, color=TEAL_DARK))
    ax.annotate("", xy=(4.2, 1.8), xytext=(4.6, 2.0), arrowprops=dict(arrowstyle="->", lw=1.2, color=SLATE_DARK))
    ax.annotate("", xy=(5.8, 1.8), xytext=(5.4, 2.0), arrowprops=dict(arrowstyle="->", lw=1.2, color="#c2410c"))

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "component_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_deployment_diagram():
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    ax.text(5, 5.1, "UML Deployment Diagram — Local Host Topology", ha="center", fontsize=13, fontweight="bold", color=NAVY_DARK)

    # Host Node Boundary
    node = FancyBboxPatch((0.5, 0.4), 9.0, 4.3, boxstyle="round,pad=0.1", ec=NAVY_DARK, fc="#f8fafc", lw=1.5)
    ax.add_patch(node)
    ax.text(1.0, 4.4, "<<device>> Development Host (ASUS TUF Gaming F15 - Windows 11 / AMD64)", fontsize=9, fontweight="bold", color=NAVY_DARK)

    # 1. Streamlit Process
    st_box = FancyBboxPatch((0.9, 2.3), 2.5, 1.8, boxstyle="round,pad=0.05", ec=TEAL_MED, fc=WHITE, lw=1.2)
    ax.add_patch(st_box)
    ax.text(2.15, 3.7, "<<execution environment>>\nStreamlit Frontend", ha="center", fontsize=8, fontweight="bold", color=TEAL_DARK)
    ax.text(2.15, 2.8, "• Python 3.11 Runtime\n• Port: 8501 (HTTP)\n• State Machine\n• Custom Dark Theme", ha="center", fontsize=7, color=SLATE_DARK)

    # 2. FastAPI Process
    api_box = FancyBboxPatch((3.8, 2.3), 2.5, 1.8, boxstyle="round,pad=0.05", ec=NAVY_MED, fc=WHITE, lw=1.2)
    ax.add_patch(api_box)
    ax.text(5.05, 3.7, "<<execution environment>>\nFastAPI & Uvicorn", ha="center", fontsize=8, fontweight="bold", color=NAVY_MED)
    ax.text(5.05, 2.8, "• Python 3.11 Runtime\n• Port: 8000 (HTTP)\n• PyTorch + CUDA Core\n• FAISS-CPU Engine", ha="center", fontsize=7, color=SLATE_DARK)

    # 3. LM Studio Server
    lm_box = FancyBboxPatch((6.7, 2.3), 2.5, 1.8, boxstyle="round,pad=0.05", ec=AMBER, fc=WHITE, lw=1.2)
    ax.add_patch(lm_box)
    ax.text(7.95, 3.7, "<<execution environment>>\nLM Studio Local Server", ha="center", fontsize=8, fontweight="bold", color="#b45309")
    ax.text(7.95, 2.8, "• Port: 1234 (HTTP API)\n• Qwen3 4B Instruct\n• GGUF Q4_K_M\n• Full GPU Offload", ha="center", fontsize=7, color=SLATE_DARK)

    # 4. PostgreSQL Node (Bottom)
    pg_box = FancyBboxPatch((3.8, 0.7), 2.5, 1.2, boxstyle="round,pad=0.05", ec=GREEN, fc=WHITE, lw=1.2)
    ax.add_patch(pg_box)
    ax.text(5.05, 1.6, "<<database system>> PostgreSQL 15+", ha="center", fontsize=8, fontweight="bold", color=GREEN)
    ax.text(5.05, 1.1, "• Port: 5432 (TCP)\n• Relational Tables & JSONB", ha="center", fontsize=7, color=SLATE_DARK)

    # Connection arrows
    ax.annotate("", xy=(3.8, 3.2), xytext=(3.4, 3.2), arrowprops=dict(arrowstyle="<->", lw=1.2, color=NAVY_MED))
    ax.text(3.6, 3.35, "HTTP", ha="center", fontsize=7, color=NAVY_MED)

    ax.annotate("", xy=(6.7, 3.2), xytext=(6.3, 3.2), arrowprops=dict(arrowstyle="<->", lw=1.2, color=AMBER))
    ax.text(6.5, 3.35, "HTTP", ha="center", fontsize=7, color=AMBER)

    ax.annotate("", xy=(5.05, 1.9), xytext=(5.05, 2.3), arrowprops=dict(arrowstyle="<->", lw=1.2, color=GREEN))
    ax.text(5.25, 2.05, "TCP/IP", fontsize=7, color=GREEN)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "deployment_diagram.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_training_curves():
    # Load actual history
    hist_file = os.path.join("reports", "bert_training_history.json")
    if os.path.exists(hist_file):
        with open(hist_file, "r") as f:
            history = json.load(f)
    else:
        history = [
            {"epoch": 1, "train_loss": 3.3734, "val_loss": 2.7039, "val_accuracy": 0.5639, "val_macro_f1": 0.3291},
            {"epoch": 2, "train_loss": 2.3464, "val_loss": 1.9956, "val_accuracy": 0.6909, "val_macro_f1": 0.4671},
            {"epoch": 3, "train_loss": 1.8925, "val_loss": 1.8248, "val_accuracy": 0.7361, "val_macro_f1": 0.5520},
        ]

    epochs = [h["epoch"] for h in history]
    train_loss = [h["train_loss"] for h in history]
    val_loss = [h["val_loss"] for h in history]
    val_acc = [h["val_accuracy"] * 100 for h in history]
    val_f1 = [h["val_macro_f1"] * 100 for h in history]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=220)

    # Loss Curve
    ax1.plot(epochs, train_loss, marker="o", color=NAVY_MED, lw=2, label="Train Loss")
    ax1.plot(epochs, val_loss, marker="s", color=TEAL_MED, lw=2, label="Validation Loss")
    ax1.set_title("Cross-Entropy Loss vs Epoch", fontsize=11, fontweight="bold", color=NAVY_DARK)
    ax1.set_xlabel("Epoch", fontsize=9)
    ax1.set_ylabel("Loss", fontsize=9)
    ax1.set_xticks(epochs)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=8.5)

    # Metric Curve
    ax2.plot(epochs, val_acc, marker="o", color=GREEN, lw=2, label="Validation Accuracy (%)")
    ax2.plot(epochs, val_f1, marker="^", color=AMBER, lw=2, label="Macro F1-Score (%)")
    ax2.set_title("Accuracy & Macro F1 vs Epoch", fontsize=11, fontweight="bold", color=NAVY_DARK)
    ax2.set_xlabel("Epoch", fontsize=9)
    ax2.set_ylabel("Percentage (%)", fontsize=9)
    ax2.set_xticks(epochs)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=8.5)

    plt.suptitle("ContractRisk AI — BERT Fine-Tuning Performance Curves (bert-base-uncased)", fontsize=12, fontweight="bold", color=NAVY_DARK, y=1.02)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "training_curves.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


def create_scoring_weights():
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=220)
    weights = [30, 35, 15, 20]
    labels = ["BERT Classifier\n(30%)", "Rule Engine\n(35%)", "RAG Precedents\n(15%)", "Qwen3 LLM\n(20%)"]
    colors = [NAVY_MED, TEAL_MED, AMBER, "#c2410c"]
    explode = (0.02, 0.05, 0.02, 0.02)

    wedges, texts, autotexts = ax.pie(
        weights, explode=explode, labels=labels, autopct="%1.0f%%",
        startangle=140, colors=colors, textprops=dict(color=SLATE_DARK, fontsize=8.5, fontweight="bold")
    )
    for at in autotexts:
        at.set_color(WHITE)
        at.set_fontsize(9)

    ax.set_title("Deterministic Hybrid Risk Scoring Weights\n(Total = 100%)", fontsize=11, fontweight="bold", color=NAVY_DARK)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "scoring_weights.png")
    plt.savefig(path, dpi=220)
    plt.close()
    print("Saved", path)


if __name__ == "__main__":
    print("Generating diagrams...")
    create_system_architecture()
    create_workflow_diagram()
    create_use_case_diagram()
    create_dfd_level0()
    create_dfd_level1()
    create_activity_diagram()
    create_sequence_diagram()
    create_erd_diagram()
    create_component_diagram()
    create_deployment_diagram()
    create_training_curves()
    create_scoring_weights()
    print("All diagrams generated successfully in", OUT_DIR)
