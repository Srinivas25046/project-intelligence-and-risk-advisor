from dotenv import load_dotenv
load_dotenv()
import json
from src.llm.client import LLMClient
from src.insights_store import load_insight, save_insight
from src.agents.config import AGENT_PROVIDERS


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def generate_documentation() -> dict:
    scope = load_insight("scope")
    risks = load_insight("risks")
    blockers = load_insight("blockers")

    prompt = f"""You are a project documentation specialist. Using the structured
project data below (already extracted from project documents), generate:

1. User stories in standard Agile format ("As a [role], I want [goal] so that [benefit]")
   for each deliverable in the scope data.
2. A formal risk register combining the risk data into a structured table format.
3. A consolidated action item list combining blockers and action items.

Do not invent new facts — only rephrase and structure what's given below.

--- SCOPE DATA ---
{json.dumps(scope, indent=2)}

--- RISK DATA ---
{json.dumps(risks, indent=2)}

--- BLOCKER DATA ---
{json.dumps(blockers, indent=2)}

Respond ONLY with valid JSON in exactly this shape:
{{
  "user_stories": [{{"role": "...", "goal": "...", "benefit": "..."}}],
  "risk_register": [{{"risk_id": "R-1", "description": "...", "severity": "...", "impact": "...", "mitigation_suggestion": "..."}}],
  "action_item_list": [{{"item": "...", "owner": "...", "status": "...", "source": "blocker|action_item"}}]
}}"""

    llm = LLMClient(providers=AGENT_PROVIDERS["doc_gen_agent"])

    def validate(text):
        json.loads(_clean_json_text(text))

    raw = llm.generate(prompt, validate=validate)
    result = json.loads(_clean_json_text(raw))
    save_insight("documentation", result)
    return result


if __name__ == "__main__":
    doc = generate_documentation()
    print(json.dumps(doc, indent=2))