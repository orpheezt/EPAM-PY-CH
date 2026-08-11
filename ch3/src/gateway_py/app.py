from fastapi import FastAPI

from .modules import install_modules

app = FastAPI(
    title="MLIR Linalg RAG API Gateway",
    description="FastAPI gateway exposing ask/ RAG endpoint backed by HuggingFace Inference API & Qdrant",
    version="0.1.0",
)

install_modules(app)
