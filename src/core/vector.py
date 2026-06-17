import os
from qdrant_client import AsyncQdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class VectorDBClient:
    _client: AsyncQdrantClient = None

    @classmethod
    def get_client(cls) -> AsyncQdrantClient:
        if cls._client is None:
            # Initializes async connection to local Docker container
            cls._client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        return cls._client


qdrant_client = VectorDBClient.get_client()
