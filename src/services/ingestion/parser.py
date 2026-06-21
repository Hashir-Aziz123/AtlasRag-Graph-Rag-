import logging
import os
from typing import List, TypedDict, Optional

logger = logging.getLogger(__name__)

IGNORED_ELEMENT_TYPES = frozenset({"Header", "Footer", "PageBreak", "PageNumber"})

class ElementMetadata(TypedDict):
    page_number: Optional[int]
    filename: Optional[str]

class ParsedElement(TypedDict, total=False):
    type: str
    text: str
    metadata: ElementMetadata
    html: str  

def parse_pdf(file_path: str) -> List[ParsedElement]:
    """
    Ingests a PDF and performs visual layout analysis and OCR.
    Extracts structural elements (Titles, Tables, Text) while preserving their topological order.
    """
    file_basename = os.path.basename(file_path)
    logger.info(f"Initiating visual layout analysis for: {file_basename}")
    
    try:
        # Lazy import prevents heavy ML library initialization unless this function is actually called
        from unstructured.partition.pdf import partition_pdf
        
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            infer_table_structure=True,
            languages=["eng"] 
        )
        
        parsed_elements: List[ParsedElement] = []
        
        for el in elements:
            element_type = type(el).__name__
            
            if element_type in IGNORED_ELEMENT_TYPES:
                continue
            
            element_text = str(el).strip()
            if not element_text:
                continue
                
            element_data: ParsedElement = {
                "type": element_type, 
                "text": element_text,
                "metadata": {
                    "page_number": getattr(el.metadata, "page_number", None),
                    "filename": getattr(el.metadata, "filename", None)
                }
            }
            
            if element_type == "Table":
                text_as_html = getattr(el.metadata, "text_as_html", None)
                if text_as_html:
                    element_data["html"] = text_as_html
                    
            parsed_elements.append(element_data)

        logger.info(f"Successfully mapped and extracted {len(parsed_elements)} structural elements from {file_basename}.")
        return parsed_elements

    except Exception as e:
        logger.error(f"Failed to parse PDF {file_basename}. Error: {str(e)}", exc_info=True)
        raise