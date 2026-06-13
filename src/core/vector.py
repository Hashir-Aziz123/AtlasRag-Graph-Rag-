import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class VectorDBClient:
    _client: QdrantClient = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        if cls._client is None:
            # Initializes connection to local Docker container
            cls._client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        return cls._client

# Singleton client instance export
qdrant_client = VectorDBClient.get_client()