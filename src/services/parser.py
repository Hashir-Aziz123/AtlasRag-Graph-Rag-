import fitz  # PyMuPDF
import os
from pathlib import Path
from config.settings import settings

def extract_text_from_pdf(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find the PDF at: {file_path}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}")

    full_text = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        cleaned_text = " ".join(text.split())
        full_text.append(cleaned_text)

    return "\n\n".join(full_text)

