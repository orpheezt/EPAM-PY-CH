from pathlib import Path

from pydantic import Field

from ..config import SettingsSection


class AskSettings(SettingsSection):
    enabled: bool = True

    # HF Inference API Configuration
    hf_token: str = Field(default="", validation_alias="HF_TOKEN")
    hf_model: str = Field(
        default="Qwen/Qwen2.5-72B-Instruct", validation_alias="HF_MODEL"
    )

    # Qdrant Configuration
    base_dir: Path = Path(__file__).resolve().parents[3]
    qdrant_url: str = Field(default="", validation_alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", validation_alias="QDRANT_API_KEY")
    qdrant_path: Path = base_dir / "qdrant_db"
    collection_name: str = "mlir_linalg_docs"

    # Retrieval parameters
    top_k: int = 3
    score_threshold: float = 0.60
    fallback_response: str = (
        "I am sorry, but the provided documentation does not contain enough "
        "information to answer this question."
    )
