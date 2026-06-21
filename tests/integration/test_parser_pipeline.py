import os
import sys
import time
from typing import List, Dict, Any

# Resolve the project root directory dynamically
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

try:
    from src.services.ingestion.parser import parse_pdf
except ImportError as error:
    print(f"Architectural Error: Unable to import parse_pdf. Details: {error}")
    sys.exit(1)

def run_structural_ingestion_audit(target_pdf_path: str) -> None:
    """
    Executes an end-to-end structural parse on a target document to verify 
    the runtime integration of system binaries, layout vision models, and 
    table decomposition layers.
    """
    if not os.path.exists(target_pdf_path):
        print(f"Execution Aborted: Target file not found at '{target_pdf_path}'.")
        return

    file_size_mb = os.path.getsize(target_pdf_path) / (1024 * 1024)

    print("======================================================================")
    print("STARTING STRUCTURAL INGESTION AUDIT")
    print(f"Target Document: {os.path.basename(target_pdf_path)}")
    print(f"Target Size:     {file_size_mb:.2f} MB")
    print("======================================================================")

    start_time = time.perf_counter()
    try:
        extracted_elements: List[Dict[str, Any]] = parse_pdf(target_pdf_path)
    except Exception as runtime_error:
        print(f"\n[CRITICAL FAILURE] Pipeline execution crashed: {runtime_error}")
        return
    
    execution_duration = time.perf_counter() - start_time

    if not extracted_elements:
        print("\n[WARNING] Pipeline executed successfully but returned zero structural elements.")
        return

    structural_metrics = {
        "Title": 0,
        "NarrativeText": 0,
        "Table": 0,
        "ListItem": 0,
        "Unclassified": 0
    }
    
    table_html_validated = 0

    print("\n--- Topographic Document Stream Sample (First 15 Elements) ---")
    for index, element in enumerate(extracted_elements):
        el_type = element.get("type", "Unknown")
        text_snippet = element.get("text", "")[:60].replace("\n", " ")
        page_num = element.get("metadata", {}).get("page_number", 1)

        if el_type in structural_metrics:
            structural_metrics[el_type] += 1
        else:
            structural_metrics["Unclassified"] += 1

        if el_type == "Table":
            if "html" in element and element["html"]:
                table_html_validated += 1

        if index < 15:
            print(f"[{index:02d}][Page {page_num:02d}] Type: {el_type:<15} | Snippet: {text_snippet}...")

    if len(extracted_elements) > 15:
        print(f"... [{len(extracted_elements) - 15} more structural elements truncated from console display]")

    print("\n======================================================================")
    print("INGESTION METRICS & ARCHITECTURAL AUDIT")
    print("======================================================================")
    print(f"Total Processing Time:       {execution_duration:.3f} seconds")
    print(f"Total Structural Elements:   {len(extracted_elements)}")
    print(f"├── Document Titles:         {structural_metrics['Title']}")
    print(f"├── Narrative Content Blocks:{structural_metrics['NarrativeText']}")
    print(f"├── List Structures:         {structural_metrics['ListItem']}")
    print(f"└── Tabular Formats (Tables): {structural_metrics['Table']}")
    print(f"    └── Validated HTML Parsed: {table_html_validated} / {structural_metrics['Table']}")
    print("======================================================================")

if __name__ == "__main__":
    TARGET_SAMPLE = os.path.join(PROJECT_ROOT, "data", "raw", "sample.pdf")
    run_structural_ingestion_audit(TARGET_SAMPLE)