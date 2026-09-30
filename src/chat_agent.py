import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import json
from dotenv import load_dotenv
load_dotenv()

from src.rag.vector_store import search
from src.insights_store import load_insight
from src.llm.client import LLMClient
from src.agents.config import AGENT_PROVIDERS


def build_project_brief() -> str:
    try:
        scope = load_insight("scope")
        risks = load_insight("risks")
        blockers = load_insight("blockers")
        health = load_insight("health_score")
    except FileNotFoundError as e:
        return f"(Project brief unavailable: {e})"

    return f"""PROJECT BRIEF (already-extracted summary, always available):
Goals: {scope.get('project_goals')}
Deliverables: {scope.get('deliverables')}
Top risks: {[r['description'] for r in risks.get('risks', [])]}
Delivery forecast: {risks.get('delivery_forecast')}
Active blockers: {[b['description'] for b in blockers.get('blockers', [])]}
Health score: {health.get('overall_health_score')}/100 ({health.get('breakdown')})
"""


class ChatAssistant:
    def __init__(self):
        self.llm = LLMClient(providers=AGENT_PROVIDERS["chat_agent"])
        self.history = []  # list of (role, content) tuples
        self.project_brief = build_project_brief()

    def _retrieve_for_question(self, question: str, top_k: int = 5) -> str:
        results = search(question, top_k=top_k)
        chunks = results["documents"][0]
        sources = [m.get("filename", "unknown") for m in results["metadatas"][0]]
        return "\n\n".join(f"[Source: {src}]\n{c}" for c, src in zip(chunks, sources))

    def _build_prompt(self, question: str) -> str:
        retrieved = self._retrieve_for_question(question)
        history_text = "\n".join(f"{role}: {content}" for role, content in self.history[-6:])

        return f"""You are a project intelligence assistant. Answer the team's question
using ONLY the information below. If the answer isn't available in this
information, say so honestly rather than guessing.

{self.project_brief}

RELEVANT DOCUMENT EXCERPTS FOR THIS QUESTION:
{retrieved}

CONVERSATION SO FAR:
{history_text}

QUESTION: {question}

Answer conversationally, in plain text (not JSON). Be concise and specific."""

    def ask(self, question: str) -> str:
        prompt = self._build_prompt(question)
        try:
            answer = self.llm.generate(prompt)
        except Exception as e:
            answer = (
                "I couldn't reach any AI provider just now (all 3 are currently "
                "unavailable or rate-limited). Please try asking again in a moment."
            )
            print(f"[ChatAssistant] All providers failed: {e}")
        self.history.append(("User", question))
        self.history.append(("Assistant", answer))
        return answer


if __name__ == "__main__":
    assistant = ChatAssistant()
    print("Project Intelligence Assistant ready. Type 'exit' to quit.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        answer = assistant.ask(question)
        print(f"\nAssistant: {answer}\n")