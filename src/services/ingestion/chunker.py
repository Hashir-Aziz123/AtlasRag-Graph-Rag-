from typing import List

def chunk_document(text: str, chunk_size_words: int = 250, overlap_words: int = 50) -> List[str]:
    if not text:
        return []

    words = text.split()
    chunks = []
    
    step_size = chunk_size_words - overlap_words
    
    for i in range(0, len(words), step_size):
        chunk_words = words[i : i + chunk_size_words]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)
        
        if i + chunk_size_words >= len(words):
            break
            
    return chunks

