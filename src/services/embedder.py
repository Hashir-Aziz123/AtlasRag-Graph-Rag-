from fastembed import TextEmbedding
from config.settings import settings

embedding_model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)

def generate_embedding(text: str) -> list[float]:
    """
    Converts a string of text into a vector based on the configured model.
    """
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()