from src.insights_store import load_insight, save_insight

SEVERITY_WEIGHT = {"high": 15, "medium": 8, "low": 3}


def score_scope_clarity(scope: dict) -> int:
    fields = ["project_goals", "deliverables", "milestones", "responsibilities"]
    populated = sum(1 for f in fields if scope.get(f))
    return round((populated / len(fields)) * 100)


def score_timeline_risk(risks: dict) -> int:
    score = 100
    for risk in risks.get("risks", []):
        severity = risk.get("severity", "medium").lower()
        score -= SEVERITY_WEIGHT.get(severity, 8)
    return max(score, 0)


def score_blocker_load(blockers: dict) -> int:
    num_blockers = len(blockers.get("blockers", []))
    score = 100 - (num_blockers * 12)
    return max(score, 0)


def compute_health_score() -> dict:
    scope = load_insight("scope")
    risks = load_insight("risks")
    blockers = load_insight("blockers")

    scope_clarity = score_scope_clarity(scope)
    timeline_risk = score_timeline_risk(risks)
    blocker_load = score_blocker_load(blockers)

    overall = round(
        (scope_clarity * 0.2) + (timeline_risk * 0.4) + (blocker_load * 0.4)
    )

    result = {
        "overall_health_score": overall,
        "breakdown": {
            "scope_clarity": scope_clarity,
            "timeline_risk": timeline_risk,
            "blocker_load": blocker_load,
        },
        "rationale": (
            f"Scope clarity is {scope_clarity}/100 based on how completely scope "
            f"fields were extracted. Timeline risk is {timeline_risk}/100, reduced by "
            f"{len(risks.get('risks', []))} identified risk(s). Blocker load is "
            f"{blocker_load}/100, reduced by {len(blockers.get('blockers', []))} active blocker(s)."
        ),
    }
    save_insight("health_score", result)
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(compute_health_score(), indent=2))