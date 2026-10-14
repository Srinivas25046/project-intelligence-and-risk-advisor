"""
Design notes
------------
* Priority is derived from the risk agent's SEVERITY so the matrix never
  contradicts the Risks tab or the health score:
      high   + probability x impact >= 55  -> Critical
      high   (otherwise)                   -> High
      medium                               -> Moderate
      low                                  -> Low
* probability / impact come from the risk agent (0-100). If a saved
  risks.json predates those fields, deterministic severity-based values
  are used instead, so older data still plots.
* Tooltips always show the TRUE probability/impact. Only the marker
  position is nudged by the anti-collision pass.
"""

import hashlib
import math
import textwrap

import plotly.graph_objects as go

PRIORITY_ORDER = ["Critical", "High", "Moderate", "Low"]
PRIORITY_COLORS = {
    "Critical": "#EF4444",
    "High": "#F59E0B",
    "Moderate": "#818CF8",
    "Low": "#22C55E",
}
CRITICAL_SCORE_THRESHOLD = 55  # (probability x impact) / 100

_SEVERITY_DEFAULTS = {"high": (72, 78), "medium": (50, 52), "low": (24, 26)}


# --------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------
def _clamp(value, lo=0.0, hi=100.0):
    return max(lo, min(hi, value))


def _normalise_severity(raw) -> str:
    token = str(raw or "medium").lower().split("|")[0].strip()
    if token == "critical":
        token = "high"
    return token if token in _SEVERITY_DEFAULTS else "medium"


def _as_percentage(value, fallback):
    """Accepts 72, '72', '72%' or 0.72 and returns a 0-100 float."""
    try:
        number = float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return fallback
    if 0 < number <= 1:
        number *= 100
    return _clamp(number)


def _fallback_scores(severity: str, description: str):
    base_p, base_i = _SEVERITY_DEFAULTS[severity]
    digest = int(hashlib.md5(description.encode("utf-8")).hexdigest(), 16)
    return (
        _clamp(base_p + (digest % 15) - 7),
        _clamp(base_i + ((digest // 15) % 15) - 7),
    )


def prepare_risks(raw_risks: list) -> list:
    prepared = []
    for index, risk in enumerate(raw_risks or [], start=1):
        description = str(risk.get("description", "")).strip()
        severity = _normalise_severity(risk.get("severity"))
        fb_p, fb_i = _fallback_scores(severity, description)
        probability = _as_percentage(risk.get("probability"), fb_p)
        impact = _as_percentage(risk.get("impact"), fb_i)
        score = probability * impact / 100

        if severity == "high":
            priority = "Critical" if score >= CRITICAL_SCORE_THRESHOLD else "High"
        elif severity == "medium":
            priority = "Moderate"
        else:
            priority = "Low"

        prepared.append({
            "id": f"RSK-{index:02d}",
            "description": description,
            "severity": severity,
            "priority": priority,
            "probability": round(probability),
            "impact": round(impact),
            "score": round(score),
            "mitigation": str(risk.get("mitigation", "") or "").strip(),
            "source": str(risk.get("evidence_source", "") or "").strip(),
            "category": str(risk.get("likely_impact", "") or "").strip(),
        })
    return prepared


# --------------------------------------------------------------------------
# Anti-collision
# --------------------------------------------------------------------------
def spread_points(points, min_dist=8.0, iterations=120, lo=4.0, hi=96.0):
    """
    Pushes overlapping points apart until every pair is at least `min_dist`
    away (or the iteration budget runs out). Deterministic: identical input
    always gives identical output.
    Returns (new_points, n_moved, n_clusters).
    """
    original = [tuple(p) for p in points]
    pts = [[p[0], p[1]] for p in points]

    for _ in range(iterations):
        moved = False
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx, dy = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
                dist = math.hypot(dx, dy)
                if dist >= min_dist:
                    continue
                if dist < 1e-6:                      # exactly stacked
                    angle = i * 2.399963 + j         # golden-angle fan-out
                    dx, dy, dist = math.cos(angle), math.sin(angle), 1.0
                push = (min_dist - dist) / 2 + 0.02
                ux, uy = dx / dist, dy / dist
                pts[i][0] -= ux * push
                pts[i][1] -= uy * push
                pts[j][0] += ux * push
                pts[j][1] += uy * push
                moved = True
        for p in pts:
            p[0], p[1] = _clamp(p[0], lo, hi), _clamp(p[1], lo, hi)
        if not moved:
            break

    n_moved = sum(
        1 for o, p in zip(original, pts) if math.hypot(o[0] - p[0], o[1] - p[1]) > 0.5
    )

    # clusters = groups of >=2 points that overlapped in their ORIGINAL positions
    parent = list(range(len(original)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(len(original)):
        for j in range(i + 1, len(original)):
            if math.hypot(original[i][0] - original[j][0],
                          original[i][1] - original[j][1]) < min_dist:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(len(original)):
        groups.setdefault(find(i), []).append(i)
    n_clusters = sum(1 for members in groups.values() if len(members) > 1)

    return [tuple(p) for p in pts], n_moved, n_clusters


# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------
def _wrap(text: str, width=48) -> str:
    return "<br>".join(textwrap.wrap(text, width)) if text else "—"


def build_matrix_figure(risks: list, display_xy: list, active_priority="All"):
    fig = go.Figure()

    # zones
    fig.add_shape(type="rect", x0=60, y0=60, x1=100, y1=100, layer="below",
                  fillcolor="rgba(239,68,68,0.09)", line=dict(width=0))
    fig.add_shape(type="rect", x0=0, y0=0, x1=40, y1=40, layer="below",
                  fillcolor="rgba(34,197,94,0.08)", line=dict(width=0))
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=100,
                  line=dict(color="rgba(148,163,184,0.25)", width=1, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=100, y0=50, y1=50,
                  line=dict(color="rgba(148,163,184,0.25)", width=1, dash="dot"))
    fig.add_annotation(x=99, y=99, text="CRITICAL HAZARD ZONE", showarrow=False,
                       xanchor="right", yanchor="top",
                       font=dict(size=10, color="rgba(248,113,113,0.85)"))
    fig.add_annotation(x=1, y=1, text="LOW PRIORITY ZONE", showarrow=False,
                       xanchor="left", yanchor="bottom",
                       font=dict(size=10, color="rgba(74,222,128,0.8)"))

    # one trace per priority keeps the legend complete even when a
    # priority currently has no risks or is filtered out
    for priority in PRIORITY_ORDER:
        selected = [
            (r, xy) for r, xy in zip(risks, display_xy)
            if r["priority"] == priority and active_priority in ("All", priority)
        ]
        fig.add_trace(go.Scatter(
            x=[xy[0] for _, xy in selected],
            y=[xy[1] for _, xy in selected],
            mode="markers+text",
            name=priority,
            text=[r["id"] for r, _ in selected],
            textposition="top center",
            textfont=dict(size=11, color="#E2E8F0"),
            marker=dict(size=17, color=PRIORITY_COLORS[priority],
                        line=dict(width=2, color="rgba(255,255,255,0.85)")),
            customdata=[[
                _wrap(r["description"]), r["priority"], r["probability"],
                r["impact"], _wrap(r["mitigation"]), r["source"] or "—",
            ] for r, _ in selected],
            hovertemplate=(
                "<b>%{text}</b> · %{customdata[1]}<br>"
                "%{customdata[0]}<br><br>"
                "Probability: <b>%{customdata[2]}%</b> &nbsp; "
                "Impact: <b>%{customdata[3]}%</b><br>"
                "Mitigation: %{customdata[4]}<br>"
                "Source: %{customdata[5]}"
                "<extra></extra>"
            ),
        ))

    axis_common = dict(range=[0, 100], zeroline=False, showline=True,
                       linecolor="rgba(148,163,184,0.4)",
                       gridcolor="rgba(148,163,184,0.12)",
                       tickfont=dict(color="#94A3B8", size=10))
    fig.update_layout(
        height=540,
        margin=dict(t=20, b=30, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title=dict(text="Probability →", font=dict(color="#94A3B8", size=12)), **axis_common),
        yaxis=dict(title=dict(text="Impact →", font=dict(color="#94A3B8", size=12)), **axis_common),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0,
                    font=dict(color="#CBD5E1", size=12)),
        hoverlabel=dict(bgcolor="#141B2D", bordercolor="#2D3652",
                        font=dict(color="#E2E8F0", size=12)),
    )
    return fig


# --------------------------------------------------------------------------
# Streamlit tab
# --------------------------------------------------------------------------
def render_risk_matrix_tab(risks_payload):
    import streamlit as st  # imported lazily so the helpers above stay testable without Streamlit

    risks = prepare_risks((risks_payload or {}).get("risks", []))
    if not risks:
        st.info("No risks available yet. Run the analysis to populate the matrix.")
        return

    counts = {p: sum(1 for r in risks if r["priority"] == p) for p in PRIORITY_ORDER}
    cards = [
        ("Total Risks", len(risks), "#F1F5F9"),
        ("Critical", counts["Critical"], PRIORITY_COLORS["Critical"]),
        ("High Severity", counts["High"], PRIORITY_COLORS["High"]),
        ("Moderate", counts["Moderate"], PRIORITY_COLORS["Moderate"]),
        ("Low Severity", counts["Low"], PRIORITY_COLORS["Low"]),
    ]
    for column, (label, value, color) in zip(st.columns(5), cards):
        column.markdown(
            f'<div class="stat-card"><div class="stat-label">{label}</div>'
            f'<div class="stat-value" style="color:{color};">{value}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='margin-top:1.4rem;'><span style='font-size:1.15rem; font-weight:700; "
        "color:#F1F5F9;'>Risk Priority Matrix</span> "
        "<span style='background:rgba(34,197,94,0.15); color:#4ADE80; padding:2px 10px; "
        "border-radius:6px; font-size:0.72rem; font-weight:600; margin-left:8px;'>"
        "Anti-Collision Active</span></div>"
        "<div style='color:#94A3B8; font-size:0.9rem; margin-bottom:0.6rem;'>"
        "Probability vs. impact distribution with intelligent collision dispersion. "
        "Hover a marker for details.</div>",
        unsafe_allow_html=True,
    )

    active = st.radio(
        "Filter by priority", ["All"] + PRIORITY_ORDER,
        horizontal=True, key="risk_matrix_filter", label_visibility="collapsed",
    )

    # positions are computed on ALL risks so markers don't jump when filtering
    display_xy, _, n_clusters = spread_points(
        [(r["probability"], r["impact"]) for r in risks]
    )
    st.plotly_chart(build_matrix_figure(risks, display_xy, active), use_container_width=True)

    plotted = len(risks) if active == "All" else counts[active]
    st.caption(f"{plotted} plotted · {n_clusters} overlapping cluster(s) spread apart")

    with st.container(border=True):
        st.markdown("**Risk details**")
        st.dataframe(
            [{
                "ID": r["id"], "Priority": r["priority"],
                "Probability %": r["probability"], "Impact %": r["impact"],
                "Score": r["score"], "Risk": r["description"],
                "Mitigation": r["mitigation"] or "—",
            } for r in risks if active in ("All", r["priority"])],
            use_container_width=True, hide_index=True,
        )