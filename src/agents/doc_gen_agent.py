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


def _call_llm(prompt: str) -> dict:
    llm = LLMClient(providers=AGENT_PROVIDERS["doc_gen_agent"])

    def validate(text):
        json.loads(_clean_json_text(text))

    raw = llm.generate(prompt, validate=validate)
    return json.loads(_clean_json_text(raw))


def generate_user_stories() -> dict:
    scope = load_insight("scope")
    prompt = f"""You are a project documentation specialist. Using ONLY the
scope data below, generate Agile user stories ("As a [role], I want [goal]
so that [benefit]") for each deliverable. Use real owner names from
responsibilities where possible, not generic job titles. Do not invent
facts not present in the data.

--- SCOPE DATA ---
{json.dumps(scope, indent=2)}

Respond ONLY with valid JSON in exactly this shape:
{{"user_stories": [{{"role": "...", "goal": "...", "benefit": "..."}}]}}"""
    result = _call_llm(prompt)
    save_insight("doc_user_stories", result)
    return result


def generate_risk_register() -> dict:
    risks = load_insight("risks")
    prompt = f"""You are a project risk analyst. Using ONLY the risk data
below, build a formal risk register. For each risk, suggest one concrete
mitigation action. Do not invent new risks not present in the data.

--- RISK DATA ---
{json.dumps(risks, indent=2)}

Respond ONLY with valid JSON in exactly this shape:
{{"risk_register": [{{"risk_id": "R-1", "description": "...", "severity": "...", "impact": "...", "mitigation_suggestion": "..."}}]}}"""
    result = _call_llm(prompt)
    save_insight("doc_risk_register", result)
    return result


def generate_action_items() -> dict:
    blockers = load_insight("blockers")
    prompt = f"""You are a project coordinator. Using ONLY the blocker and
action item data below, produce one consolidated action item list,
merging blockers and action items without losing any entries.

--- BLOCKER DATA ---
{json.dumps(blockers, indent=2)}

Respond ONLY with valid JSON in exactly this shape:
{{"action_item_list": [{{"item": "...", "owner": "...", "status": "...", "source": "blocker|action_item"}}]}}"""
    result = _call_llm(prompt)
    save_insight("doc_action_items", result)
    return result