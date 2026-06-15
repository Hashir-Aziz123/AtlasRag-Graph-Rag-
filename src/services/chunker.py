from typing import List

def chunk_document(text: str, chunk_size_words: int = 250, overlap_words: int = 50) -> List[str]:
    if not text:
        return []

    words = text.split()
    chunks = []
    
    # Step through the list of words, moving forward by (chunk_size - overlap) each time
    step_size = chunk_size_words - overlap_words
    
    for i in range(0, len(words), step_size):
        # Grab the slice of words for this chunk
        chunk_words = words[i : i + chunk_size_words]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)
        
        # If we've reached the end of the document, stop
        if i + chunk_size_words >= len(words):
            break
            
    return chunks

