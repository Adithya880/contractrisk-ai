import os
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import pymupdf

PDF_PATH = "ContractRisk_AI_Complete_Technical_Documentation.pdf"

def verify():
    assert os.path.exists(PDF_PATH), f"{PDF_PATH} does not exist!"
    doc = pymupdf.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Total Pages: {total_pages}")
    
    # 1. Check images
    total_images = 0
    pages_with_images = []
    for i, page in enumerate(doc):
        imgs = page.get_images()
        if imgs:
            total_images += len(imgs)
            pages_with_images.append((i + 1, len(imgs)))
    
    print(f"Total Embedded Images: {total_images}")
    print(f"Pages with Images: {pages_with_images}")
    
    # 2. Check headings on pages
    print("\n--- Section Headings Discovery Across Pages ---")
    sections_found = {}
    for i, page in enumerate(doc):
        text = page.get_text()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            if line.startswith(("1. Project Overview", "2. Technology Stack", "3. Complete System Architecture",
                               "4. Complete End-to-End Workflow", "5. Individual Module Explanation",
                               "6. Dataset, Model Training", "7. Machine Learning",
                               "8. Risk Assessment Real-World", "9. Database Design",
                               "10. API & Frontend Workflow", "11. System Model Preparation",
                               "12. Performance & Testing", "13. Limitations",
                               "14. Viva Preparation", "15. Technical Glossary",
                               "Table of Contents", "FIGURE")):
                if line not in sections_found:
                    sections_found[line] = i + 1
                    print(f"Page {i+1}: {line[:60]}")
    
    # 3. Check Table of Contents text on Page 2
    toc_page = doc[1]
    print("\n--- Table of Contents Text on Page 2 ---")
    print(toc_page.get_text()[:400])

    doc.close()
    print("\nVerification Complete!")

if __name__ == "__main__":
    verify()
