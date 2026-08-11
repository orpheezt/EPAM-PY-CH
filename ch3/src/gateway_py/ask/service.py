from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from ..embeddings import FastEmbedEmbeddings
from .errors import HFInferenceError
from .schemas import AskResponse
from .settings import AskSettings

SYSTEM_PROMPT = """You are a technical AI assistant specializing in MLIR Linalg Dialect & Lowering Pipelines (Bufferization / Tensor-to-MemRef).

Answer the question strictly based ONLY on the provided context.
Rules:
1. Every answer MUST cite the source document name(s) in brackets, for example: [03_one_shot_bufferize.md].
2. If the provided context is empty, missing, or does NOT contain enough relevant information to answer the question accurately, respond with EXACTLY this sentence and NOTHING else:
"I am sorry, but the provided documentation does not contain enough information to answer this question."
3. Do NOT make up any details or use external knowledge not present in the context."""


class AskService:
    def __init__(self, settings: AskSettings | None = None) -> None:
        self.settings = settings or AskSettings()

    def _get_vector_store(self) -> QdrantVectorStore:
        if self.settings.qdrant_url:
            client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key or None,
            )
        else:
            client = QdrantClient(path=str(self.settings.qdrant_path))

        return QdrantVectorStore(
            client=client,
            collection_name=self.settings.collection_name,
            embedding=FastEmbedEmbeddings(),
        )

    def _generate_hf_response(
        self, prompt: str, formatted_context: str, question: str
    ) -> str:
        client = InferenceClient(
            model=self.settings.hf_model, token=self.settings.hf_token
        )
        try:
            completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Context:\n{formatted_context}\n\nQuestion: {question}",
                    },
                ],
                max_tokens=500,
                temperature=0.01,
            )
            return (completion.choices[0].message.content or "").strip()
        except HfHubHTTPError:
            try:
                res = client.text_generation(
                    prompt, max_new_tokens=500, temperature=0.01
                )
                return res.strip()
            except HfHubHTTPError as exc:
                raise HFInferenceError(
                    f"HuggingFace Inference API error: {exc}"
                ) from exc

    async def ask(self, question: str) -> AskResponse:
        vector_store = self._get_vector_store()
        retriever = vector_store.as_retriever(
            search_kwargs={
                "k": self.settings.top_k,
                "score_threshold": self.settings.score_threshold,
            }
        )
        context_docs: list[Document] = retriever.invoke(question)

        match context_docs:
            case []:
                return AskResponse(
                    answer=self.settings.fallback_response,
                    sources=[],
                    context_docs=[],
                )
            case docs:
                sources = sorted(
                    {
                        doc.metadata.get("source", "unknown")
                        for doc in docs
                        if doc.metadata.get("source")
                    }
                )
                context_snippets = [doc.page_content for doc in docs]

        hf_token = self.settings.hf_token
        if not hf_token or hf_token.startswith("your_"):
            return AskResponse(
                answer=(
                    f"Retrieved context from {sources}. "
                    "(Set HF_TOKEN to generate full LLM response with HuggingFace Inference API)"
                ),
                sources=sources,
                context_docs=context_snippets,
            )

        formatted_context = "\n\n".join(
            f"--- Document Source: [{doc.metadata.get('source', 'unknown')}] ---\n{doc.page_content}"
            for doc in context_docs
        )

        prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{formatted_context}\n\nQuestion: {question}\n\nAnswer:"
        answer_text = self._generate_hf_response(prompt, formatted_context, question)

        return AskResponse(
            answer=answer_text,
            sources=sources,
            context_docs=context_snippets,
        )
