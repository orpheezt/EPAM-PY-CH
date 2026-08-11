from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings


class FastEmbedEmbeddings(Embeddings):
    """Clean FastEmbed Embeddings implementation using fastembed directly."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, emb)) for emb in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(map(float, next(iter(self.model.embed([text])))))
