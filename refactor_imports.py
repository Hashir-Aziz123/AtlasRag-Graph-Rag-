import os
import shutil

# 1. Define the Mapping: { Current File : New Location }
FILE_MAPPING = {
    # The Write Path (Ingestion Services)
    "src/services/extractor.py": "src/services/ingestion/extractor.py",
    "src/services/parser.py": "src/services/ingestion/parser.py",
    "src/services/chunker.py": "src/services/ingestion/chunker.py",
    "src/services/generator.py": "src/services/ingestion/graph_writer.py",  # Renamed during move
    
    # The Read Path (Retrieval Services)
    "src/services/fetcher.py": "src/services/retrieval/fetcher.py",
    "src/services/router.py": "src/services/retrieval/router.py",
    "src/services/synthesizer.py": "src/services/retrieval/synthesizer.py",
    
    # The Domain-Agnostic Utilities (Core Infrastructure)
    "src/services/embedder.py": "src/core/embedder.py",
    "src/services/cache_manager.py": "src/core/cache_manager.py",
    "src/services/vector_store.py": "src/core/vector_store.py"
}

# 2. Define the Import String Replacements: { Old Import : New Import }
IMPORT_REPLACEMENTS = {
    # Ingestion
    "from src.services.extractor": "from src.services.ingestion.extractor",
    "import src.services.extractor": "import src.services.ingestion.extractor",
    "from src.services.parser": "from src.services.ingestion.parser",
    "import src.services.parser": "import src.services.ingestion.parser",
    "from src.services.chunker": "from src.services.ingestion.chunker",
    "import src.services.chunker": "import src.services.ingestion.chunker",
    "from src.services.generator": "from src.services.ingestion.graph_writer",
    "import src.services.generator": "import src.services.ingestion.graph_writer",
    
    # Retrieval
    "from src.services.fetcher": "from src.services.retrieval.fetcher",
    "import src.services.fetcher": "import src.services.retrieval.fetcher",
    "from src.services.router": "from src.services.retrieval.router",
    "import src.services.router": "import src.services.retrieval.router",
    "from src.services.synthesizer": "from src.services.retrieval.synthesizer",
    "import src.services.synthesizer": "import src.services.retrieval.synthesizer",
    
    # Core Infrastructure
    "from src.services.embedder": "from src.core.embedder",
    "import src.services.embedder": "import src.core.embedder",
    "from src.services.cache_manager": "from src.core.cache_manager",
    "import src.services.cache_manager": "import src.core.cache_manager",
    "from src.services.vector_store": "from src.core.vector_store",
    "import src.services.vector_store": "import src.core.vector_store"
}

# Directories to search for python files to update
TARGET_DIRECTORIES = ["src", "tests", "config"]

def create_directories():
    """Ensure the new subdirectory structure exists."""
    dirs_to_create = [
        "src/services/ingestion",
        "src/services/retrieval",
        "src/core"
    ]
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        # Create an __init__.py so Python recognizes it as a module
        init_file = os.path.join(d, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                pass

def move_files():
    """Move files to their new domain folders."""
    print("Moving files...")
    for old_path, new_path in FILE_MAPPING.items():
        if os.path.exists(old_path):
            shutil.move(old_path, new_path)
            print(f"  [+] Moved {os.path.basename(old_path)} -> {os.path.dirname(new_path)}/")
        elif os.path.exists(new_path):
            print(f"  [-] {os.path.basename(new_path)} is already in its target directory.")
        else:
            print(f"  [!] WARNING: {old_path} not found.")

def update_imports(filepath):
    """Read a file, replace old imports with new ones, and save."""
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    modified = False
    for old_str, new_str in IMPORT_REPLACEMENTS.items():
        if old_str in content:
            content = content.replace(old_str, new_str)
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    return False

def scan_and_update_codebase():
    """Walk through all target directories and apply import updates to .py files."""
    print("\nUpdating import statements across codebase...")
    updated_files_count = 0
    
    for directory in TARGET_DIRECTORIES:
        if not os.path.exists(directory):
            continue
            
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    if update_imports(filepath):
                        print(f"  [+] Updated imports in: {filepath}")
                        updated_files_count += 1
                        
    print(f"\nRefactoring complete. Successfully updated imports in {updated_files_count} files.")

if __name__ == "__main__":
    print("Initializing Service Domain Refactor...\n")
    create_directories()
    move_files()
    scan_and_update_codebase()