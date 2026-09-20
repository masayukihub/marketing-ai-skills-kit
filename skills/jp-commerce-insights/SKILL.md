---
name: jp-commerce-insights
description: "Analyze user-supplied Japan commerce research and review CSVs, trace VOC evidence, and prepare a content handoff. No built-in live scraping."
---

# 日本电商洞察

## Before task
Read repository AGENTS.md and `project.json`. Only load `modules/customer-review-intelligence/CONTRACT.md` and relevant evidence. Use the full kit repository; a lone Skill folder is not a standalone install.

## Workflow
1. 明确要支持的决策、品类、市场、竞品范围和资料覆盖，不默认全部市场都有数据。
2. 先核对 Product Truth，再运行本地 VOC 分析。把本地样本和联网研究分开标识。
3. 复核高频主题的原文，不把关键词匹配直接当负面情绪。
4. 输出 Purchase Trigger、Pain、Anxiety、Scenario、User Language、Evidence ID、建议动作。
5. 竞品矩阵仅作内部研究；实时关键词/价格/页面未查时标 UNKNOWN。
6. 给内容入口一个简短 Handoff：消费者问题、主信息候选、证据、禁用主张和缺口。

## Runnable local step
Run from the kit root (replace project/output with the user's separate local directories):

```bash
python3 scripts/run.py --task insights --project examples/demo-project --out outputs/demo-project/insights
```

This is the **synthetic demo**. For real work, use ignored `projects/<project-id>/` and retain unknowns. The script performs deterministic processing, not model reasoning. Continue the requested strategy/copy work in the host agent, with explicit evidence and limitations.

## Completion
Deliver the requested analysis/brief plus exact output paths, sources, unknowns, blockers and one next action. Tests do not certify factual accuracy or publication readiness. Do not claim unavailable live collection, image generation, browser QA or external writes.
