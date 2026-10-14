import json
from src.rag.vector_store import search, get_chunks_by_filename
from src.llm.client import LLMClient
from src.agents.config import AGENT_PROVIDERS
from src.ingestion.manifest import load_last_batch


class BaseAgent:
    agent_name: str = None
    retrieval_query: str = None
    additional_queries: list[str] = []
    additional_filters: list[dict] = []
    always_include_latest_batch: bool = True
    system_instructions: str = None

    def __init__(self):
        providers = AGENT_PROVIDERS[self.agent_name]
        self.llm = LLMClient(providers=providers)

    def retrieve_context(self, top_k: int = 8) -> str:
        results = search(self.retrieval_query, top_k=top_k)
        chunks = results["documents"][0]
        sources = [m.get("filename", "unknown") for m in results["metadatas"][0]]

        seen = set(chunks)
        combined = list(zip(chunks, sources))

        for extra_query in self.additional_queries:
            extra = search(extra_query, top_k=top_k)
            for chunk, meta in zip(extra["documents"][0], extra["metadatas"][0]):
                if chunk not in seen:
                    seen.add(chunk)
                    combined.append((chunk, meta.get("filename", "unknown")))

        for where_filter in self.additional_filters:
            filtered = search(self.retrieval_query, top_k=20, where=where_filter)
            for chunk, meta in zip(filtered["documents"][0], filtered["metadatas"][0]):
                if chunk not in seen:
                    seen.add(chunk)
                    combined.append((chunk, meta.get("filename", "unknown")))

        # Always include every file from the most recent ingestion batch, so new
        # information can never be crowded out by older, larger documents.
        if self.always_include_latest_batch:
            for filename in load_last_batch():
                batch_chunks, batch_metas = get_chunks_by_filename(filename)
                for chunk, meta in zip(batch_chunks, batch_metas):
                    if chunk not in seen:
                        seen.add(chunk)
                        combined.append((chunk, meta.get("filename", "unknown")))

        return "\n\n".join(f"[Source: {src}]\n{chunk}" for chunk, src in combined)

    def build_prompt(self, context: str) -> str:
        return f"""{self.system_instructions}

Below is retrieved content from project documents. Base your answer only
on this content — do not invent information that isn't present here.

--- RETRIEVED CONTENT ---
{context}
--- END CONTENT ---

Respond ONLY with valid JSON. No markdown code fences, no preamble, no explanation outside the JSON."""

    @staticmethod
    def _clean_json_text(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        return cleaned.strip()

    def _validate_json(self, text: str) -> None:
        # Raises if the response is not a JSON object. LLMClient treats that
        # as a failed provider and moves on to the next one in the chain.
        parsed = json.loads(self._clean_json_text(text))
        if not isinstance(parsed, dict):
            raise ValueError("Expected a JSON object")

    def run(self) -> dict:
        context = self.retrieve_context()
        prompt = self.build_prompt(context)
        # validate= is what makes a malformed answer fall through to the next
        # provider instead of being accepted. If every provider fails this
        # raises, and the caller keeps the previous saved insight.
        raw_response = self.llm.generate(prompt, validate=self._validate_json)
        return json.loads(self._clean_json_text(raw_response))