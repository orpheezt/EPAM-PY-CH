class AskError(Exception):
    """Base exception for Ask module."""


class VectorStoreError(AskError):
    """Raised when vector store interaction fails."""


class HFInferenceError(AskError):
    """Raised when HuggingFace Inference API call fails."""
