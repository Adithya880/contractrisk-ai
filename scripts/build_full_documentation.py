"""
ContractRisk AI — Complete Technical Documentation Generator
Compiles all 15 sections, 12 high-resolution architecture diagrams, dynamic Table of Contents,
and professional styling into ContractRisk_AI_Complete_Technical_Documentation.pdf.
"""

import os
import sys
sys.path.insert(0, ".")
import json
import tempfile
from pathlib import Path
import pymupdf

from scripts.sections_content import (
    get_section_1_html,
    get_section_2_html,
    get_section_3_html,
    get_section_4_html,
    get_section_5_html,
    get_section_6_html,
    get_section_7_html,
    get_section_8_html,
    get_section_9_html,
    get_section_10_html,
    get_section_11_html,
    get_section_12_html,
    get_section_13_html,
    get_section_14_html,
    get_section_15_html,
)

OUTPUT_PDF = "ContractRisk_AI_Complete_Technical_Documentation.pdf"
DIAGRAMS_DIR = os.path.join("reports", "diagrams")

# Color Constants
C_NAVY_DARK = (15/255, 39/255, 68/255)     # #0f2744
C_NAVY_MED = (30/255, 58/255, 138/255)     # #1e3a8a
C_TEAL_DARK = (15/255, 118/255, 110/255)   # #0f766e
C_TEAL_MED = (13/255, 148/255, 136/255)    # #0d9488
C_TEAL_LIGHT = (20/255, 184/255, 166/255)  # #14b8a6
C_SLATE_DARK = (30/255, 41/255, 59/255)    # #1e293b
C_SLATE_MED = (71/255, 85/255, 105/255)    # #475569
C_SLATE_LIGHT = (241/255, 245/255, 249/255)# #f1f5f9
C_WHITE = (1.0, 1.0, 1.0)
C_GOLD = (245/255, 158/255, 11/255)       # #f59e0b
C_BORDER = (203/255, 213/255, 225/255)    # #cbd5e1

A4_WIDTH = 595.3
A4_HEIGHT = 841.9
MARGIN = 48.0
CONTENT_WIDTH = A4_WIDTH - (2 * MARGIN)

HTML_STYLE = """
<style>
body {
    font-family: sans-serif;
    color: #1e293b;
    font-size: 9.0pt;
    line-height: 1.42;
    margin: 0;
    padding: 0;
}
h1 {
    color: #0f2744;
    font-size: 18pt;
    font-weight: bold;
    margin-top: 0;
    margin-bottom: 5pt;
    border-bottom: 2pt solid #0d9488;
    padding-bottom: 3pt;
}
h2 {
    color: #1e3a8a;
    font-size: 12pt;
    font-weight: bold;
    margin-top: 10pt;
    margin-bottom: 4pt;
    border-bottom: 1pt solid #cbd5e1;
    padding-bottom: 2pt;
}
h3 {
    color: #0f766e;
    font-size: 10pt;
    font-weight: bold;
    margin-top: 8pt;
    margin-bottom: 2.5pt;
}
p {
    margin-top: 0;
    margin-bottom: 5pt;
    text-align: justify;
}
ul, ol {
    margin-top: 0;
    margin-bottom: 5pt;
    padding-left: 14pt;
}
li {
    margin-bottom: 2pt;
}
b, strong {
    color: #0f2744;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 5pt;
    margin-bottom: 7pt;
    font-size: 8.0pt;
}
th {
    background-color: #0f2744;
    color: #ffffff;
    font-weight: bold;
    padding: 3.5pt 4.5pt;
    border: 1px solid #0f2744;
    text-align: left;
}
td {
    padding: 3.5pt 4.5pt;
    border: 1px solid #cbd5e1;
    text-align: left;
    vertical-align: top;
}
tr:nth-child(even) td {
    background-color: #f8fafc;
}
.callout {
    background-color: #f0fdfa;
    border-left: 3pt solid #0d9488;
    padding: 5pt 7pt;
    margin: 5pt 0;
    border-radius: 2pt;
}
.callout-warn {
    background-color: #fffbeb;
    border-left: 3pt solid #f59e0b;
    padding: 5pt 7pt;
    margin: 5pt 0;
    border-radius: 2pt;
}
.callout-crit {
    background-color: #fef2f2;
    border-left: 3pt solid #ef4444;
    padding: 5pt 7pt;
    margin: 5pt 0;
    border-radius: 2pt;
}
code {
    font-family: monospace;
    font-size: 8.0pt;
    background-color: #f1f5f9;
    padding: 1pt 2.5pt;
    border-radius: 2pt;
    color: #0f2744;
}
pre {
    font-family: monospace;
    font-size: 7.5pt;
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    padding: 5pt;
    margin: 4pt 0;
    border-radius: 2pt;
    line-height: 1.25;
}
.badge {
    display: inline-block;
    padding: 1pt 3pt;
    border-radius: 2pt;
    font-size: 7.0pt;
    font-weight: bold;
    color: white;
}
.badge-high { background-color: #ef4444; }
.badge-med { background-color: #f59e0b; }
.badge-low { background-color: #10b981; }
</style>
"""


def create_cover_page():
    """Generate high-impact navy & teal cover page."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)

    # 1. Full Navy Background
    page.draw_rect(pymupdf.Rect(0, 0, A4_WIDTH, A4_HEIGHT), color=C_NAVY_DARK, fill=C_NAVY_DARK)

    # 2. Modern Geometric Accents
    page.draw_rect(pymupdf.Rect(0, 0, A4_WIDTH, 8), color=C_GOLD, fill=C_GOLD)
    page.draw_rect(pymupdf.Rect(0, 8, A4_WIDTH, 14), color=C_TEAL_MED, fill=C_TEAL_MED)

    # Decorative frame lines
    page.draw_line(pymupdf.Point(36, 46), pymupdf.Point(559, 46), color=C_TEAL_DARK, width=1.0)
    page.draw_line(pymupdf.Point(36, 795), pymupdf.Point(559, 795), color=C_TEAL_DARK, width=1.0)
    page.draw_line(pymupdf.Point(36, 46), pymupdf.Point(36, 795), color=C_TEAL_DARK, width=1.0)
    page.draw_line(pymupdf.Point(559, 46), pymupdf.Point(559, 795), color=C_TEAL_DARK, width=1.0)

    # Inner subtle corner brackets
    page.draw_line(pymupdf.Point(42, 52), pymupdf.Point(85, 52), color=C_GOLD, width=1.5)
    page.draw_line(pymupdf.Point(42, 52), pymupdf.Point(42, 95), color=C_GOLD, width=1.5)
    page.draw_line(pymupdf.Point(553, 789), pymupdf.Point(510, 789), color=C_GOLD, width=1.5)
    page.draw_line(pymupdf.Point(553, 789), pymupdf.Point(553, 746), color=C_GOLD, width=1.5)

    # 3. Header Tag
    page.insert_text(pymupdf.Point(55, 105), "BTECH COMPUTER SCIENCE & ENGINEERING FINAL PROJECT",
                     fontsize=9.5, fontname="hebo", color=C_GOLD)
    page.insert_text(pymupdf.Point(55, 122), "ACADEMIC TECHNICAL DOCUMENTATION & SYSTEM SPECIFICATION",
                     fontsize=8.0, fontname="helv", color=C_TEAL_LIGHT)

    # 4. Main Project Title
    page.insert_text(pymupdf.Point(55, 205), "CONTRACTRISK AI",
                     fontsize=34, fontname="hebo", color=C_WHITE)

    # Accent divider under title
    page.draw_line(pymupdf.Point(55, 224), pymupdf.Point(340, 224), color=C_TEAL_MED, width=3.0)
    page.draw_line(pymupdf.Point(345, 224), pymupdf.Point(420, 224), color=C_GOLD, width=3.0)

    # Subtitle
    sub1 = "Intelligent Multi-Stage Contract Risk Analysis, Semantic"
    sub2 = "Clause Classification & Grounded Scenario Prediction"
    page.insert_text(pymupdf.Point(55, 252), sub1, fontsize=13.5, fontname="hebo", color=C_SLATE_LIGHT)
    page.insert_text(pymupdf.Point(55, 272), sub2, fontsize=13.5, fontname="hebo", color=C_SLATE_LIGHT)

    # 5. Core Highlights Pill Box
    pill_box = pymupdf.Rect(55, 310, 540, 580)
    page.draw_rect(pill_box, color=C_NAVY_MED, fill=(20/255, 45/255, 80/255), width=1.0)
    
    page.insert_text(pymupdf.Point(70, 335), "VERIFIED SYSTEM ARCHITECTURE & AI MODEL SPECIFICATIONS", fontsize=9.0, fontname="hebo", color=C_GOLD)
    
    specs = [
        ("• Clause Classifier:", "Fine-Tuned BERT (bert-base-uncased, 41 Multi-Class Categories)"),
        ("• Classification Metrics:", "71.86% Test Accuracy | 0.5115 Macro F1 | 1,418 Held-Out Clauses"),
        ("• Dense Semantic Embedder:", "SentenceTransformers (all-MiniLM-L6-v2, 384 Dimensions, L2 Normalized)"),
        ("• Vector Search Store:", "FAISS IndexFlatIP (9,447 Pre-Indexed Historical Benchmark Precedents)"),
        ("• Local Generative Reasoning:", "Qwen3 4B Instruct 2507 GGUF (Q4_K_M) via LM Studio (100% On-Premises)"),
        ("• Deterministic Risk Core:", "Hybrid Formula: 30% BERT + 35% Rules + 15% RAG + 20% LLM"),
        ("• Legal Heuristic Rules:", "16 Risk Domains with Asymptotic Severity Score Aggregation"),
        ("• Enterprise Persistence:", "PostgreSQL 15+ Relational Database & SQLAlchemy 2.x ORM (7 Tables)"),
        ("• Frontend Application:", "Streamlit 1.65 (5-State Terminal Workflow, 8-Stage Real Progress View)"),
        ("• Execution Performance:", "0.750s Warm End-to-End Analysis | 20/20 Green Automated Tests")
    ]
    y_pos = 360
    for label, val in specs:
        page.insert_text(pymupdf.Point(70, y_pos), label, fontsize=8.0, fontname="hebo", color=C_TEAL_LIGHT)
        page.insert_text(pymupdf.Point(220, y_pos), val, fontsize=7.8, color=C_WHITE)
        y_pos += 21

    # 6. Metadata Footer Block
    meta_box = pymupdf.Rect(55, 605, 540, 755)
    page.draw_rect(meta_box, color=(25/255, 55/255, 95/255), fill=(18/255, 42/255, 74/255), width=0.8)

    meta_items = [
        ("Document Classification:", "Official BTech Project Technical Documentation & Viva Reference"),
        ("Target Examination:", "Final Year BTech Computer Science & Engineering Degree Evaluation"),
        ("Software Release:", "Production Release Phase 8.2.1 / Performance Optimized Pipeline"),
        ("Development Host:", "ASUS TUF Gaming F15 (NVIDIA GeForce RTX 3050 Laptop GPU, 16 GB RAM)"),
        ("Publication Date:", "October 2026 | Antigravity AI Systems"),
        ("Project Repository:", "AI CLAUSE ANALYSER / ContractRisk AI")
    ]
    y_meta = 630
    for label, val in meta_items:
        page.insert_text(pymupdf.Point(70, y_meta), label, fontsize=7.8, fontname="hebo", color=C_GOLD)
        page.insert_text(pymupdf.Point(220, y_meta), val, fontsize=7.8, color=C_SLATE_LIGHT)
        y_meta += 20

    # Bottom Branding
    page.insert_text(pymupdf.Point(55, 780), "CONFIDENTIAL & PROPRIETARY — FOR ACADEMIC & TECHNICAL EXAMINATION ONLY",
                     fontsize=7.2, fontname="helv", color=C_TEAL_DARK)

    return doc


def render_html_story(html_content):
    """Render HTML content into a memory PyMuPDF document."""
    full_html = HTML_STYLE + html_content
    story = pymupdf.Story(full_html)
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    writer = pymupdf.DocumentWriter(tmp_path)
    def rectfn(rect_num, filled):
        mediabox = pymupdf.Rect(0, 0, A4_WIDTH, A4_HEIGHT)
        rect = pymupdf.Rect(MARGIN, MARGIN + 10, A4_WIDTH - MARGIN, A4_HEIGHT - MARGIN - 10)
        return mediabox, rect, pymupdf.Identity

    story.write(writer, rectfn)
    writer.close()

    doc = pymupdf.open(tmp_path)
    mem_doc = pymupdf.open()
    mem_doc.insert_pdf(doc)
    doc.close()
    
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return mem_doc


def create_figure_page(fig_num, fig_title, img_filename, explanation_bullets, width=470, height=310):
    """Create a standardized high-resolution figure plate page."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)

    # Figure Header
    page.insert_text(pymupdf.Point(MARGIN, 62), f"FIGURE {fig_num}: {fig_title.upper()}",
                     fontsize=11.5, fontname="hebo", color=C_NAVY_DARK)
    page.draw_line(pymupdf.Point(MARGIN, 70), pymupdf.Point(A4_WIDTH - MARGIN, 70), color=C_TEAL_MED, width=1.5)

    # Insert Image
    img_path = os.path.join(DIAGRAMS_DIR, img_filename)
    if os.path.exists(img_path):
        x_left = MARGIN + (CONTENT_WIDTH - width) / 2
        img_rect = pymupdf.Rect(x_left, 82, x_left + width, 82 + height)
        # Background card for image
        card_rect = pymupdf.Rect(img_rect.x0 - 4, img_rect.y0 - 4, img_rect.x1 + 4, img_rect.y1 + 4)
        page.draw_rect(card_rect, color=C_BORDER, fill=C_SLATE_LIGHT, width=0.8)
        page.insert_image(img_rect, filename=img_path)

    # Caption Box below image
    y_caption = 82 + height + 16
    caption_box = pymupdf.Rect(MARGIN, y_caption, A4_WIDTH - MARGIN, y_caption + 22)
    page.draw_rect(caption_box, color=C_TEAL_DARK, fill=(240/255, 253/255, 250/255), width=0.8)
    page.insert_text(pymupdf.Point(MARGIN + 10, y_caption + 14), 
                     f"Figure {fig_num} Architecture & Model Description: {fig_title}", 
                     fontsize=8.5, fontname="hebo", color=C_TEAL_DARK)

    # Bullet point explanations
    y_text = y_caption + 36
    for bullet in explanation_bullets:
        # Draw small square bullet
        page.draw_rect(pymupdf.Rect(MARGIN + 4, y_text + 2, MARGIN + 8, y_text + 6), color=C_TEAL_MED, fill=C_TEAL_MED)
        page.insert_textbox(pymupdf.Rect(MARGIN + 14, y_text - 1, A4_WIDTH - MARGIN - 4, y_text + 45),
                            bullet, fontsize=8.0, color=C_SLATE_DARK, fontname="helv")
        y_text += 26

    return doc


def build_table_of_contents(toc_data, fig_data):
    """Build a professional Table of Contents page."""
    html = """
    <h1>Table of Contents</h1>
    <p>This technical report provides exhaustive documentation of the ContractRisk AI architecture, algorithms, datasets, performance benchmarks, and software models.</p>
    <table>
        <tr><th>Sec.</th><th>Documentation Section Title</th><th>Category</th><th>Page</th></tr>
    """
    for num, title, cat, page in toc_data:
        html += f"""
        <tr>
            <td style="font-weight:bold; color:#0f2744;">{num}</td>
            <td style="font-weight:bold;">{title}</td>
            <td style="color:#0f766e;">{cat}</td>
            <td style="font-weight:bold; text-align:right; color:#1e3a8a;">{page}</td>
        </tr>
        """
    html += "</table>"
    html += """
    <h2>List of Embedded Architecture & UML Diagrams</h2>
    <table>
        <tr><th>Figure</th><th>Diagram Name</th><th>System Model Component</th><th>Page</th></tr>
    """
    for fig_num, name, comp, page in fig_data:
        html += f"""
        <tr>
            <td style="font-weight:bold; color:#0f2744;">{fig_num}</td>
            <td style="font-weight:bold;">{name}</td>
            <td style="color:#0f766e;">{comp}</td>
            <td style="font-weight:bold; text-align:right; color:#1e3a8a;">{page}</td>
        </tr>
        """
    html += "</table>"
    return render_html_story(html)


def apply_header_footer(doc, toc_entries):
    """Apply running top headers and bottom footers with exact dynamic page numbering."""
    total_pages = len(doc)
    
    # Page 1 is cover: leave intact
    for page_num in range(1, total_pages):
        page = doc[page_num]
        p_num_display = page_num + 1

        # Determine current section based on page ranges
        sec_title = "Technical Report"
        for title, start_p, end_p in toc_entries:
            if start_p <= p_num_display <= end_p:
                sec_title = title
                break

        # Running Top Header
        page.insert_text(pymupdf.Point(MARGIN, 34), "CONTRACTRISK AI — TECHNICAL DOCUMENTATION & SYSTEM ARCHITECTURE",
                         fontsize=7.2, fontname="hebo", color=C_NAVY_MED)
        page.insert_text(pymupdf.Point(A4_WIDTH - MARGIN - 170, 34), sec_title[:36],
                         fontsize=7.2, fontname="helv", color=C_SLATE_MED)
        page.draw_line(pymupdf.Point(MARGIN, 40), pymupdf.Point(A4_WIDTH - MARGIN, 40),
                       color=C_BORDER, width=0.6)

        # Running Bottom Footer
        page.draw_line(pymupdf.Point(MARGIN, A4_HEIGHT - 36), pymupdf.Point(A4_WIDTH - MARGIN, A4_HEIGHT - 36),
                       color=C_BORDER, width=0.6)
        page.insert_text(pymupdf.Point(MARGIN, A4_HEIGHT - 24), "BTech Final Project — Confidential & Proprietary",
                         fontsize=7.0, fontname="helv", color=C_SLATE_MED)
        page.insert_text(pymupdf.Point(A4_WIDTH/2 - 25, A4_HEIGHT - 24), f"Page {p_num_display} of {total_pages}",
                         fontsize=7.8, fontname="hebo", color=C_NAVY_DARK)
        page.insert_text(pymupdf.Point(A4_WIDTH - MARGIN - 105, A4_HEIGHT - 24), "Antigravity AI Systems",
                         fontsize=7.0, fontname="helv", color=C_SLATE_MED)


def main():
    print("=" * 65)
    print("CONTRACTRISK AI — DOCUMENTATION PDF BUILD PIPELINE")
    print("=" * 65)

    # 1. Generate Cover Page
    print("[1/5] Generating Executive Cover Page...")
    cover_doc = create_cover_page()

    # 2. Render Text Sections and Build Figure Plates
    print("[2/5] Compiling Technical Sections & Figure Plates...")
    
    sections_order = [
        ("Section 1: Project Overview", get_section_1_html()),
        ("Section 2: Technology Stack", get_section_2_html()),
        ("Section 3: System Architecture", get_section_3_html()),
        # Insert Figure 1
        ("FIGURE_PLATE_1", None),
        ("Section 4: End-to-End Workflow", get_section_4_html()),
        # Insert Figure 2
        ("FIGURE_PLATE_2", None),
        ("Section 5: Module Explanation", get_section_5_html()),
        ("Section 6: Dataset & Training", get_section_6_html()),
        # Insert Figure 3 & Figure 4
        ("FIGURE_PLATE_3", None),
        ("FIGURE_PLATE_4", None),
        ("Section 7: ML & AI Workflow", get_section_7_html()),
        ("Section 8: Risk Examples", get_section_8_html()),
        ("Section 9: Database Design", get_section_9_html()),
        # Insert Figure 5
        ("FIGURE_PLATE_5", None),
        ("Section 10: API & Frontend", get_section_10_html()),
        ("Section 11: System Models", get_section_11_html()),
        # Insert Figures 6 to 12
        ("FIGURE_PLATE_6", None),
        ("FIGURE_PLATE_7", None),
        ("FIGURE_PLATE_8", None),
        ("FIGURE_PLATE_9", None),
        ("FIGURE_PLATE_10", None),
        ("FIGURE_PLATE_11", None),
        ("FIGURE_PLATE_12", None),
        ("Section 12: Testing & Perf", get_section_12_html()),
        ("Section 13: Limitations", get_section_13_html()),
        ("Section 14: Viva Preparation", get_section_14_html()),
        ("Section 15: Glossary", get_section_15_html()),
    ]

    # Pre-render all content blocks
    rendered_blocks = []
    for item_name, html_data in sections_order:
        if html_data is not None:
            doc_block = render_html_story(html_data)
            rendered_blocks.append((item_name, doc_block))
        else:
            # Figure plate generation
            if item_name == "FIGURE_PLATE_1":
                doc_fig = create_figure_page(
                    1, "Complete System Architecture Diagram", "arch_diagram.png",
                    [
                        "<b>Presentation Tier:</b> Streamlit 5-state terminal frontend executing over HTTP port 8501.",
                        "<b>API Gateway Tier:</b> FastAPI on Uvicorn (port 8000) managing async endpoints and dependency singletons.",
                        "<b>AI Inference Core:</b> GPU-accelerated PyTorch BERT, Heuristic Rule Engine, SentenceTransformer, and FAISS.",
                        "<b>Local LLM Subsystem:</b> Qwen3 4B Instruct running locally in LM Studio at port 1234 without cloud exposure.",
                        "<b>Persistence Tier:</b> PostgreSQL 15+ relational database holding complete 7-table analysis audit records."
                    ], width=470, height=295
                )
            elif item_name == "FIGURE_PLATE_2":
                doc_fig = create_figure_page(
                    2, "Complete End-to-End Pipeline Execution Flow", "workflow_diagram.png",
                    [
                        "<b>Sequential 12-Stage Pipeline:</b> Ingests binary files, segments text, and conducts hybrid evaluations.",
                        "<b>Batched Inference:</b> BERT classification and FAISS vector retrieval run in single GPU tensor batches.",
                        "<b>Conditional Qwen3 Routing:</b> Routine low-risk clauses bypass LLM evaluation (0 Qwen calls).",
                        "<b>Deterministic Aggregation:</b> Static weighted formula calculates final risk score and maps to risk levels.",
                        "<b>Atomic Persistence:</b> Database flush commits all 7 tables in a single ACID transaction."
                    ], width=460, height=335
                )
            elif item_name == "FIGURE_PLATE_3":
                doc_fig = create_figure_page(
                    3, "BERT Fine-Tuning Performance Curves (bert-base-uncased)", "training_curves.png",
                    [
                        "<b>Training Loss Trajectory:</b> Rapidly converged from 3.3734 (Epoch 1) to 1.8925 (Epoch 3).",
                        "<b>Validation Accuracy:</b> Reached 73.61% validation accuracy and 71.86% final held-out test accuracy.",
                        "<b>Macro F1 Metric:</b> Improved from 0.3291 to 0.5520, balancing minority classes via weighted CrossEntropy.",
                        "<b>Hardware Execution:</b> 10.39 minutes total fine-tuning duration on NVIDIA RTX 3050 Laptop GPU (FP16)."
                    ], width=470, height=210
                )
            elif item_name == "FIGURE_PLATE_4":
                doc_fig = create_figure_page(
                    4, "Deterministic Hybrid Risk Scoring Weights", "scoring_weights.png",
                    [
                        "<b>Rule Engine (35%):</b> Highest weight ensures explicit legal loopholes and statutory traps are penalized.",
                        "<b>BERT Classifier (30%):</b> High weight anchors contextual legal domain understanding.",
                        "<b>Local Qwen3 LLM (20%):</b> Moderate weight contributes qualitative real-world exposure assessment.",
                        "<b>RAG Benchmark (15%):</b> Calibrates risk against 9,447 historical precedent clauses.",
                        "<b>Strict Static Constraints:</b> Weights do not shift dynamically, ensuring consistent auditability."
                    ], width=360, height=270
                )
            elif item_name == "FIGURE_PLATE_5":
                doc_fig = create_figure_page(
                    5, "Entity Relationship Diagram (ERD) — PostgreSQL Schema", "erd_diagram.png",
                    [
                        "<b>documents & clauses:</b> 1-to-N relationship linking raw file metadata to extracted section text.",
                        "<b>clauses & risk_assessments:</b> 1-to-1 relationship mapping clauses to hybrid score breakdowns.",
                        "<b>risk_assessments & rule_matches / evidence:</b> 1-to-N relationships recording specific triggers and citations.",
                        "<b>contract_summaries:</b> Document-level aggregation holding overall score and clause risk counts.",
                        "<b>Referential Integrity:</b> Foreign keys enforce ON DELETE CASCADE across all child records."
                    ], width=470, height=305
                )
            elif item_name == "FIGURE_PLATE_6":
                doc_fig = create_figure_page(
                    6, "UML Use Case Diagram — System Actor Interactions", "use_case_diagram.png",
                    [
                        "<b>Primary Actor:</b> Contract Reviewer / Legal Analyst uploading agreements and inspecting risk.",
                        "<b>Core Use Cases:</b> Document Upload, Analysis Trigger, Real-Time Progress, Executive Dashboard.",
                        "<b>Grounded Scenario Reading:</b> Accessing single synthesized future scenario prediction.",
                        "<b>Boundary Enforcement:</b> Streamlit state machine prevents concurrent conflicting analysis runs."
                    ], width=450, height=270
                )
            elif item_name == "FIGURE_PLATE_7":
                doc_fig = create_figure_page(
                    7, "Data Flow Diagram (DFD Level 0) — Context Diagram", "dfd_l0_diagram.png",
                    [
                        "<b>External Entity (User):</b> Submits PDF/DOCX contracts and receives risk assessments and scenarios.",
                        "<b>Process 0 (ContractRisk AI):</b> Central hybrid intelligence system executing analysis core.",
                        "<b>Data Store (PostgreSQL):</b> Two-way communication storing analysis artifacts and querying history.",
                        "<b>Data Isolation:</b> No external data flows leave the local system boundary."
                    ], width=470, height=220
                )
            elif item_name == "FIGURE_PLATE_8":
                doc_fig = create_figure_page(
                    8, "Data Flow Diagram (DFD Level 1) — Decomposed System Flow", "dfd_l1_diagram.png",
                    [
                        "<b>Process 1.0 (Ingest):</b> Extracts and normalizes text into Segmented Clauses.",
                        "<b>Process 2.0 (BERT):</b> Emits predicted clause categories and softmax confidences.",
                        "<b>Process 3.0 (Rules):</b> Evaluates heuristic patterns and cross-clause contradictions.",
                        "<b>Process 4.0 & 5.0 (RAG & Scorer):</b> Retrieves precedents from FAISS (D1) and synthesizes hybrid scores.",
                        "<b>Process 6.0 (Persistence):</b> Commits records to PostgreSQL (D2) and streams results to UI."
                    ], width=470, height=295
                )
            elif item_name == "FIGURE_PLATE_9":
                doc_fig = create_figure_page(
                    9, "UML Activity Diagram — Analysis Execution Logic", "activity_diagram.png",
                    [
                        "<b>Start Node:</b> User uploads file and initiates analysis.",
                        "<b>Decision Node:</b> Evaluates whether a clause contains detected risk signals.",
                        "<b>Deep LLM Branch:</b> Risky candidate clauses routed to Qwen3 for scenario prediction.",
                        "<b>Fast-Pass Branch:</b> Routine low-risk clauses bypass LLM, maintaining sub-second performance.",
                        "<b>Merge Node:</b> Aggregates hybrid scores, commits single-transaction DB write, and displays results."
                    ], width=430, height=340
                )
            elif item_name == "FIGURE_PLATE_10":
                doc_fig = create_figure_page(
                    10, "UML Sequence Diagram — Client-Server Call Chain", "sequence_diagram.png",
                    [
                        "<b>Call 1 & 2:</b> Streamlit submits multipart file to FastAPI POST /api/v1/analyze.",
                        "<b>Call 3 & 4:</b> ContractRiskAnalyzer runs batched BERT tensor pass and vectorized FAISS search.",
                        "<b>Call 5 & 6:</b> Conditional deep analysis query dispatched to local Qwen3 via LM Studio HTTP API.",
                        "<b>Call 7 & 8:</b> Summary aggregated and single-transaction commit executed on PostgreSQL.",
                        "<b>Call 9 & 10:</b> 200 OK JSON AnalysisResponse returned and rendered in Streamlit."
                    ], width=470, height=310
                )
            elif item_name == "FIGURE_PLATE_11":
                doc_fig = create_figure_page(
                    11, "UML Component Diagram — Modular Subsystem Structure", "component_diagram.png",
                    [
                        "<b>Frontend Component:</b> Streamlit views interacting with REST API controllers.",
                        "<b>Document Processing Component:</b> PyMuPDF and ClauseSegmenter constructing clause models.",
                        "<b>Analyzer Facade:</b> Unifies BERT Classifier, Rule Engine, FAISS Index, and Qwen3 Generator.",
                        "<b>Repository Component:</b> Encapsulates PostgreSQL database operations via SQLAlchemy ORM."
                    ], width=450, height=280
                )
            elif item_name == "FIGURE_PLATE_12":
                doc_fig = create_figure_page(
                    12, "UML Deployment Diagram — Local Host Topology", "deployment_diagram.png",
                    [
                        "<b>Host Device:</b> ASUS TUF Gaming F15 running Windows 11 64-bit.",
                        "<b>Streamlit Runtime:</b> Python 3.11 web app listening on HTTP port 8501.",
                        "<b>FastAPI Gateway:</b> Uvicorn web server listening on HTTP port 8000.",
                        "<b>LM Studio Server:</b> Local OpenAI-compatible server on HTTP port 1234 offloaded to GPU.",
                        "<b>PostgreSQL Server:</b> Relational database listening on TCP port 5432."
                    ], width=460, height=255
                )
            rendered_blocks.append((item_name, doc_fig))

    # 3. Calculate Page Ranges for Table of Contents
    print("[3/5] Computing Dynamic Page Numbers & Assembling Document...")
    
    # Page 1 is Cover
    # Page 2 is Table of Contents
    # Real content starts on Page 3
    fig_meta = {
        "FIGURE_PLATE_1": ("Figure 1", "Complete System Architecture Diagram", "5-Tier System Topology"),
        "FIGURE_PLATE_2": ("Figure 2", "Complete End-to-End Pipeline Execution Flow", "12-Stage Data Workflow"),
        "FIGURE_PLATE_3": ("Figure 3", "BERT Fine-Tuning Performance Curves", "Loss, Accuracy & Macro F1"),
        "FIGURE_PLATE_4": ("Figure 4", "Deterministic Hybrid Risk Scoring Weights", "Formula Weight Breakdown"),
        "FIGURE_PLATE_5": ("Figure 5", "Entity Relationship Diagram (ERD)", "PostgreSQL 7-Table Schema"),
        "FIGURE_PLATE_6": ("Figure 6", "UML Use Case Diagram", "User & System Boundary"),
        "FIGURE_PLATE_7": ("Figure 7", "Data Flow Diagram (DFD Level 0)", "Context Level Flow"),
        "FIGURE_PLATE_8": ("Figure 8", "Data Flow Diagram (DFD Level 1)", "Decomposed System Processes"),
        "FIGURE_PLATE_9": ("Figure 9", "UML Activity Diagram", "Analysis Execution Logic"),
        "FIGURE_PLATE_10": ("Figure 10", "UML Sequence Diagram", "Client-Server Call Chain"),
        "FIGURE_PLATE_11": ("Figure 11", "UML Component Diagram", "Subsystem Modular Architecture"),
        "FIGURE_PLATE_12": ("Figure 12", "UML Deployment Diagram", "Host & Process Topology"),
    }
    current_page = 3
    toc_data = []
    fig_toc_data = []
    section_page_ranges = []

    # Map section titles for TOC
    sec_meta = {
        "Section 1: Project Overview": ("1.0", "Project Overview", "Foundations"),
        "Section 2: Technology Stack": ("2.0", "Technology Stack", "Architecture"),
        "Section 3: System Architecture": ("3.0", "Complete System Architecture", "Architecture"),
        "FIGURE_PLATE_1": ("Fig 1", "System Architecture Diagram", "Diagram Plate"),
        "Section 4: End-to-End Workflow": ("4.0", "Complete End-to-End Workflow", "Workflow"),
        "FIGURE_PLATE_2": ("Fig 2", "Pipeline Execution Flowchart", "Diagram Plate"),
        "Section 5: Module Explanation": ("5.0", "Individual Module Explanation", "Implementation"),
        "Section 6: Dataset & Training": ("6.0", "Dataset, Model Training & Hyperparameters", "Machine Learning"),
        "FIGURE_PLATE_3": ("Fig 3", "BERT Fine-Tuning Performance Curves", "Diagram Plate"),
        "FIGURE_PLATE_4": ("Fig 4", "Hybrid Risk Scoring Weights Chart", "Diagram Plate"),
        "Section 7: ML & AI Workflow": ("7.0", "Machine Learning & AI Workflow", "Machine Learning"),
        "Section 8: Risk Examples": ("8.0", "Risk Assessment Real-World Examples", "Case Study"),
        "Section 9: Database Design": ("9.0", "Database Design & PostgreSQL Schema", "Persistence"),
        "FIGURE_PLATE_5": ("Fig 5", "Entity Relationship Diagram (ERD)", "Diagram Plate"),
        "Section 10: API & Frontend": ("10.0", "API & Frontend Workflow", "Implementation"),
        "Section 11: System Models": ("11.0", "System Model Preparation (UML & Requirements)", "Software Models"),
        "FIGURE_PLATE_6": ("Fig 6", "UML Use Case Diagram", "Diagram Plate"),
        "FIGURE_PLATE_7": ("Fig 7", "Data Flow Diagram Level 0", "Diagram Plate"),
        "FIGURE_PLATE_8": ("Fig 8", "Data Flow Diagram Level 1", "Diagram Plate"),
        "FIGURE_PLATE_9": ("Fig 9", "UML Activity Diagram", "Diagram Plate"),
        "FIGURE_PLATE_10": ("Fig 10", "UML Sequence Diagram", "Diagram Plate"),
        "FIGURE_PLATE_11": ("Fig 11", "UML Component Diagram", "Diagram Plate"),
        "FIGURE_PLATE_12": ("Fig 12", "UML Deployment Diagram", "Diagram Plate"),
        "Section 12: Testing & Perf": ("12.0", "Performance & Testing Report", "Verification"),
        "Section 13: Limitations": ("13.0", "Limitations & Future Enhancements", "Evaluation"),
        "Section 14: Viva Preparation": ("14.0", "Viva Preparation & Project Questions", "Academic Defense"),
        "Section 15: Glossary": ("15.0", "Technical Glossary", "Reference"),
    }

    for name, block in rendered_blocks:
        b_len = len(block)
        start_p = current_page
        end_p = current_page + b_len - 1
        
        if name in sec_meta and not name.startswith("FIGURE_PLATE"):
            num, title, cat = sec_meta[name]
            toc_data.append((num, title, cat, f"Page {start_p}"))
            section_page_ranges.append((f"{num} {title}", start_p, end_p))
        elif name.startswith("FIGURE_PLATE"):
            num, title, cat = sec_meta[name]
            section_page_ranges.append((title, start_p, end_p))
            if name in fig_meta:
                f_num, f_name, f_comp = fig_meta[name]
                fig_toc_data.append((f_num, f_name, f_comp, f"Page {start_p}"))

        current_page += b_len

    # Generate Table of Contents
    toc_doc = build_table_of_contents(toc_data, fig_toc_data)

    # 4. Final Document Concatenation
    print("[4/5] Merging Cover, Table of Contents, Sections and Diagrams...")
    final_doc = pymupdf.open()
    
    # Add Cover
    final_doc.insert_pdf(cover_doc)
    # Add Table of Contents
    final_doc.insert_pdf(toc_doc)
    # Add All Content Blocks
    for name, block in rendered_blocks:
        final_doc.insert_pdf(block)

    # 5. Apply Headers & Footers
    print(f"[5/5] Applying Running Headers, Footers & Numbering across {len(final_doc)} pages...")
    apply_header_footer(final_doc, section_page_ranges)

    # Save to disk
    final_doc.save(OUTPUT_PDF, deflate=True)
    final_doc.close()
    
    print("=" * 65)
    print(f"[SUCCESS] Complete Documentation Generated: {OUTPUT_PDF}")
    print(f"Total Page Count: {current_page - 1} pages")
    print(f"Output File Size: {os.path.getsize(OUTPUT_PDF) / (1024*1024):.2f} MB")
    print("=" * 65)


if __name__ == "__main__":
    main()
