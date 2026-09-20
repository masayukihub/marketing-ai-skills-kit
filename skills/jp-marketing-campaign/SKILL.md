---
name: jp-marketing-campaign
description: "Plan GTM and marketing campaigns; compute auditable KPI summaries from local CSVs and produce prioritized actions without external publishing."
---

# 日本营销活动策划与复盘

## Before task
Read repository AGENTS.md and `project.json`. Only load `modules/project-context/CONTRACT.md` and relevant evidence. Use the full kit repository; a lone Skill folder is not a standalone install.

## Workflow
1. 选择 PLAN / READINESS / EXECUTION / REVIEW，避免小需求触发整套流程。
2. 明确目标、受众、价值理由、渠道角色、主 CTA、阶段和 KPI 口径。
3. 检查产品、Offer、库存、日期、Claim、链接、法务缺口；未确认不能写成确定。
4. 使用本地脚本算比率；币种、税口径、归因窗、周期不一致时报错，不混算。
5. 区分规模和效率，相关性不当因果；ROAS 不写成利润 ROI。
6. 给出继续/调整/停止/测试建议，附依据、Owner、截止条件与成功指标；不要自动发短链或写平台。

## Runnable local step
Run from the kit root (replace project/output with the user's separate local directories):

```bash
python3 scripts/run.py --task campaign --project examples/demo-project --out outputs/demo-project/campaign
```

This is the **synthetic demo**. For real work, use ignored `projects/<project-id>/` and retain unknowns. The script performs deterministic processing, not model reasoning. Continue the requested strategy/copy work in the host agent, with explicit evidence and limitations.

## Completion
Deliver the requested analysis/brief plus exact output paths, sources, unknowns, blockers and one next action. Tests do not certify factual accuracy or publication readiness. Do not claim unavailable live collection, image generation, browser QA or external writes.
