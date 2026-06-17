import time
import os
from src.workers.tasks import process_pdf_task
from config.settings import settings

def run_celery_test():
    file_name = "sample.pdf"
    target_pdf = settings.RAW_DATA_DIR / file_name
    
    if not target_pdf.exists():
        print(f" Source file not found: {target_pdf}")
        return

    print(f"[*] Dispatching PDF processing task to Celery...")
    print(f"    Target: {target_pdf}")
    
    task = process_pdf_task.delay(str(target_pdf), start_page=4, end_page=6)
    
    print(f"[*] Task successfully dispatched to Redis.")
    print(f"    Task ID: {task.id}")
    print("[*] Polling worker status...\n")
    

    while True:
        if task.ready():
            break
        print(f"    Status: {task.status}...")
        time.sleep(2)
        
    print("\n[*] Task Execution Complete.")
    
    if task.successful():
        result = task.result
        print(f"    Result: {result['message']}")
    else:
        print(f"     Task Failed.")
        print(f"    Error: {task.info}")

if __name__ == "__main__":
    run_celery_test()