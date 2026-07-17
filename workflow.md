# Meta Ads Creative Automation Engine — Workflow

```mermaid
graph LR
    A["Trigger: n8n Cron\nevery 6 hours"] --> B["Input: Meta Marketing API\nspend, CTR, frequency, CPA\nper ad set"]
    B --> C["Process: Claude fatigue scoring\nDiagnose root cause\nGenerate 3 new hook variants"]
    C --> D["Output: Creative brief pushed\nto Notion/Slack review queue"]
    D --> E["Verify: Approved variants logged\nPerformance re-checked next run"]
```

## Layers

| Layer | Tech |
|-------|------|
| Trigger | n8n Cron node |
| Input | Meta Marketing API |
| Processing | Claude — fatigue scoring + hook generation |
| Output | Notion/Slack review queue |
| Verification | Run-over-run performance comparison, logged |
