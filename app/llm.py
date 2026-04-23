import logging
from typing import Dict, Iterable, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.utils import settings


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a precise and helpful question answering assistant.
Use only the retrieved context to answer the question.
If the answer is not present in the context, say that the information is not available in the provided documents.
Always keep the answer concise, factual, and grounded in the context."""


class LLMService:
    """Wraps LLM provider configuration and response generation."""

    def __init__(self) -> None:
        if settings.llm_provider.lower() != "groq":
            raise ValueError(
                "Only the 'groq' provider is implemented by default. "
                "Set LLM_PROVIDER=groq and provide GROQ_API_KEY."
            )
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for LLM calls.")

        self.client = ChatOpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            model=settings.llm_model,
            temperature=settings.temperature,
            streaming=True,
        )

    @staticmethod
    def _build_context(documents: Iterable[dict]) -> str:
        """Format retrieved chunks into a source-aware prompt block."""
        context_parts: List[str] = []
        for idx, document in enumerate(documents, start=1):
            source = document["metadata"].get("source", "unknown")
            chunk_id = document["metadata"].get("chunk_id", "n/a")
            content = document["content"]
            context_parts.append(
                f"[Context {idx} | Source: {source} | Chunk: {chunk_id}]\n{content}"
            )
        return "\n\n".join(context_parts)

    def build_messages(
        self,
        query: str,
        documents: List[dict],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> List:
        """Combine system prompt, memory, context, and query into chat messages."""
        context = self._build_context(documents)
        user_prompt = (
            f"Retrieved context:\n{context}\n\n"
            f"Question:\n{query}\n\n"
            "Answer the question using the retrieved context and cite the source paths when helpful."
        )

        messages: List = [SystemMessage(content=SYSTEM_PROMPT)]

        for item in chat_history or []:
            if item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item["role"] == "assistant":
                messages.append(AIMessage(content=item["content"]))

        messages.append(HumanMessage(content=user_prompt))
        return messages

    def generate_answer(
        self,
        query: str,
        documents: List[dict],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate a grounded answer from the LLM."""
        logger.info("Generating LLM response for query")
        messages = self.build_messages(query, documents, chat_history)
        response = self.client.invoke(messages)
        return response.content

    async def stream_answer(
        self,
        query: str,
        documents: List[dict],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ):
        """Yield tokens from the LLM for streaming API responses."""
        logger.info("Streaming LLM response for query")
        messages = self.build_messages(query, documents, chat_history)
        async for chunk in self.client.astream(messages):
            if chunk.content:
                yield chunk.content
