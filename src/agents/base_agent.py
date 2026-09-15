import json
from src.rag.vector_store import search
from src.llm.client import LLMClient
from src.agents.config import AGENT_PROVIDERS


class BaseAgent:
    agent_name: str = None
    retrieval_query: str = None
    additional_queries: list[str] = []
    additional_filters: list[dict] = []
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
        json.loads(self._clean_json_text(text))

    def run(self) -> dict:
        context = self.retrieve_context()
        prompt = self.build_prompt(context)
        raw_response = self.llm.generate(prompt, validate=self._validate_json)
        return self._parse_json(raw_response)

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(self._clean_json_text(text))
        except json.JSONDecodeError:
            print(f"[{self.agent_name}] Failed to parse JSON. Raw output:")
            print(text)
            return {"error": "invalid_json", "raw": text}