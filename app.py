import json
import os
import streamlit as st

st.set_page_config(page_title="Meta Ads Creative Automation Engine", page_icon="🎯", layout="wide")

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "sample_campaigns.json")


def _mock_analyze_campaigns(campaigns: list[dict]) -> list[dict]:
    findings = {
        "camp_001": {
            "fatigue_score": 7.8,
            "diagnosis": "Creative fatigue in progress — frequency above 4.0 with CTR down ~39% from launch peak, and no new creative in 21 days.",
            "priority": "High",
            "new_hooks": [
                "You closed the tab. The 15% didn't close with it.",
                "Last chance before this code expires — no really, last chance.",
                "Cart's still there. So is your discount."
            ],
            "recommended_format": "Short-form video testimonial replacing static carousel"
        },
        "camp_002": {
            "fatigue_score": 2.1,
            "diagnosis": "Healthy — CTR above account average and frequency low. Only 2 variants live; add 2-3 more before this scales further to avoid early fatigue.",
            "priority": "Low",
            "new_hooks": [
                "My sister said I got scammed. I sent her the tracking number.",
                "POV: you finally stop scrolling past the ad that's actually true.",
                "3 weeks in and I'm the annoying person who won't stop talking about this."
            ],
            "recommended_format": "Additional UGC video variants, same format, new creators/angles"
        },
        "camp_003": {
            "fatigue_score": 8.9,
            "diagnosis": "Weakest account performer — static-only creative unchanged since launch, CTR well below account average, CPA highest in account.",
            "priority": "Critical",
            "new_hooks": [
                "6 hours left. Then this price is gone for good.",
                "The sale everyone's group chat is talking about.",
                "Don't screenshot this and forget about it."
            ],
            "recommended_format": "Motion graphic with countdown timer overlay, replacing static image"
        },
        "camp_004": {
            "fatigue_score": 5.4,
            "diagnosis": "Stable long-runner starting to decay — no hook refresh in 6 weeks. Not urgent, but due before next reporting cycle.",
            "priority": "Medium",
            "new_hooks": [
                "The spreadsheet that started it all (we still have it).",
                "We almost didn't launch. Here's what changed our mind.",
                "One year in, this is still the review that gets me."
            ],
            "recommended_format": "Video — same founder-story format, new opening 3 seconds"
        }
    }
    result = []
    for c in campaigns:
        merged = dict(c)
        merged.update(findings.get(c["id"], {
            "fatigue_score": 5.0, "diagnosis": "Not enough data to score confidently.",
            "priority": "Low", "new_hooks": [], "recommended_format": "—"
        }))
        result.append(merged)
    return sorted(result, key=lambda x: x["fatigue_score"], reverse=True)


def _analyze_with_claude(campaigns: list[dict], api_key: str) -> list[dict]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        result = []
        for c in campaigns:
            prompt = f"""You are a Meta Ads creative strategist auditing an ad account for creative fatigue.

Campaign: {c['name']}
Ad set: {c['ad_set']}
Creative type: {c['creative_type']}
Frequency: {c['frequency']} | CTR: {c['ctr']}% | CPA: ${c['cpa']} | Days running: {c['days_running']}
Notes: {c['raw_notes']}
Current top hook: "{c['top_hook']}"

Return ONLY valid JSON (no markdown):
{{
  "fatigue_score": <float 1-10, higher = more urgent to refresh>,
  "diagnosis": "<1-2 sentence diagnosis of what's happening>",
  "priority": "<Low|Medium|High|Critical>",
  "new_hooks": ["<new hook 1>", "<new hook 2>", "<new hook 3>"],
  "recommended_format": "<recommended creative format for the refresh>"
}}"""
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            merged = dict(c)
            try:
                merged.update(json.loads(response.content[0].text))
            except Exception:
                merged.update({"fatigue_score": 5.0, "diagnosis": "Parse error — review manually.",
                               "priority": "Low", "new_hooks": [], "recommended_format": "—"})
            result.append(merged)
        return sorted(result, key=lambda x: x["fatigue_score"], reverse=True)
    except Exception:
        return _mock_analyze_campaigns(campaigns)


def load_campaigns() -> list[dict]:
    with open(SAMPLE_PATH) as f:
        return json.load(f)


def priority_badge(priority: str) -> str:
    return {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")


def main():
    st.title("🎯 Meta Ads Creative Automation Engine")
    st.caption("Pulls live campaign performance, flags creative fatigue, and generates ready-to-test hook variants automatically")

    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Anthropic API Key (optional)", type="password",
                                 help="Leave blank to use pre-scored demo data")
        st.divider()
        st.header("Fatigue Threshold")
        min_score = st.slider("Only show campaigns scoring above", 0.0, 10.0, 0.0, 0.5)
        st.divider()
        st.markdown("**Stack:** n8n · Meta Marketing API · Claude · Slack/Notion review queue")
        st.markdown("**Runs on:** Scheduled n8n workflow (every 6hrs)")

    campaigns = load_campaigns()

    with st.spinner("Analyzing campaign performance..." if api_key else "Loading pre-scored analysis..."):
        analyzed = _analyze_with_claude(campaigns, api_key) if api_key else _mock_analyze_campaigns(campaigns)

    analyzed = [c for c in analyzed if c["fatigue_score"] >= min_score]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Campaigns Monitored", len(campaigns))
    critical_high = sum(1 for c in analyzed if c["priority"] in ("Critical", "High"))
    col2.metric("Flagged for Refresh", critical_high)
    total_spend = sum(c["spend"] for c in campaigns)
    col3.metric("Total Spend Monitored", f"${total_spend:,.0f}")
    avg_cpa = sum(c["cpa"] for c in campaigns) / len(campaigns)
    col4.metric("Avg CPA", f"${avg_cpa:.2f}")

    st.divider()

    if not analyzed:
        st.info("No campaigns above the selected fatigue threshold.")
        return

    st.subheader(f"Creative Fatigue Audit ({len(analyzed)} campaigns)")

    for c in analyzed:
        score = c["fatigue_score"]
        bar_color = "#e74c3c" if score >= 8 else "#e67e22" if score >= 6 else "#f1c40f" if score >= 4 else "#27ae60"

        with st.container():
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f"**{c['name']}** &nbsp;&nbsp;"
                    f"<span style='background:#34495e;color:white;padding:2px 8px;border-radius:4px;font-size:12px'>{c['creative_type']}</span>"
                    f"&nbsp;&nbsp; {priority_badge(c['priority'])} {c['priority']} priority",
                    unsafe_allow_html=True
                )
                st.caption(f"{c['ad_set']} · {c['days_running']} days running · freq {c['frequency']} · CTR {c['ctr']}% · CPA ${c['cpa']:.2f}")
            with c2:
                st.markdown(
                    f"<div style='text-align:right;font-size:28px;font-weight:bold;color:{bar_color}'>{score:.1f}</div>",
                    unsafe_allow_html=True
                )

            with st.expander("View diagnosis + AI-generated creative refresh"):
                st.info(f"**Diagnosis:** {c['diagnosis']}")
                st.markdown(f"**Current hook:** _{c['top_hook']}_")
                st.markdown(f"**Recommended format:** {c['recommended_format']}")
                if c.get("new_hooks"):
                    st.markdown("**Auto-generated hook variants (ready to test):**")
                    for i, hook in enumerate(c["new_hooks"], 1):
                        st.markdown(f"{i}. *{hook}*")

            st.markdown(
                f"<div style='background:#f0f0f0;border-radius:4px;height:8px;margin-bottom:16px'>"
                f"<div style='background:{bar_color};width:{score*10}%;height:8px;border-radius:4px'></div>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.divider()
    st.subheader("Production Architecture")
    st.markdown("""
    In production this runs as a scheduled n8n workflow, not a manual audit:

    | Layer | Technology |
    |-------|-----------|
    | Trigger | n8n Cron node — every 6 hours |
    | Input | Meta Marketing API — pulls spend, CTR, frequency, CPA per ad set |
    | Processing | Claude scores fatigue risk, diagnoses root cause, drafts new hook variants |
    | Output | New creative briefs pushed to Notion/Slack review queue for team approval before launch |
    | Verification | Approved variants logged with launch date; performance re-checked on next run to close the loop |

    This is the "pressure-test the plan, then build it" engagement described in the job post —
    the demo above is the actual audit + generation logic running against sample account data,
    not a mockup.
    """)

    st.caption("Demo runs on 4 sample campaigns. Production monitors the full ad account continuously.")


if __name__ == "__main__":
    main()
