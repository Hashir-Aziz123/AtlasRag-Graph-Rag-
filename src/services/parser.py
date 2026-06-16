import fitz  # PyMuPDF
import os

def extract_text_from_pdf(file_path: str, start_page: int = 0, end_page: int = None) -> str:
    """
    Extracts raw text from a PDF, with optional pagination controls to isolate specific sections.
    Note: Page indexes are 0-based.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find the PDF at: {file_path}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}")

    full_text = []
    total_pages = len(doc)
    
    # Safely compute boundaries to prevent index errors
    safe_start = max(0, start_page)
    safe_end = min(end_page, total_pages) if end_page is not None else total_pages
    
    for page_num in range(safe_start, safe_end):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        cleaned_text = " ".join(text.split())
        full_text.append(cleaned_text)

    return "\n\n".join(full_text)