# Meta Ads Creative Automation Engine — Demo

Streamlit demo of an automated creative-fatigue audit and hook-generation pipeline for a Meta Ads account.

## What It Does

- Pulls per-campaign performance (spend, CTR, frequency, CPA, days running)
- Scores each campaign's creative fatigue risk and diagnoses the root cause
- Auto-generates 3 ready-to-test hook variants + recommended creative format per flagged campaign
- Ranks the account by refresh priority so the team knows what to act on first

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## With Claude API

Add your Anthropic API key in the sidebar to score campaigns live via Claude.
Without a key, the app uses pre-scored demo data from `sample_data/sample_campaigns.json`.

## Production Architecture

In production this runs as a scheduled n8n workflow:
- **Trigger:** n8n Cron — every 6 hours
- **Input:** Meta Marketing API (spend, CTR, frequency, CPA per ad set)
- **Processing:** Claude scores fatigue risk and drafts new hook variants
- **Output:** New creative briefs pushed to Notion/Slack review queue
- **Verification:** Approved variants logged; performance re-checked next run

## Demo Limitations

- This is an MVP demo — 4 sample campaigns, pre-scored fallback data
- Production version would add: live Meta API pull, Slack/Notion push, historical trend tracking across runs
