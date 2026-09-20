---
name: jp-edm
description: "Draft Japanese email strategy, subject, preheader and responsive HTML using local evidence; keep legal, asset and sending approvals explicit."
---

# 日本 EDM 制作

## Before task
Read repository AGENTS.md and `project.json`. Only load `modules/product-truth/CONTRACT.md` and relevant evidence. Use the full kit repository; a lone Skill folder is not a standalone install.

## Workflow
1. 判断 COPY / CRITIQUE / HTML / LOCAL_REVISION，不必每次从 GTM 开始。
2. 一封邮件只设一个主要任务和主 CTA；用产品角色和场景匹配排序，不按规格数量堆模块。
3. 从用户品牌配置和项目读取正式名、Offer、主张、落地页；模板不携带历史价格。
4. 主题、Preheader、正文分工；自然日语，短句但不省略关键限制条件。
5. 运行本地表格布局 HTML。它是可查看的草稿，不是已经做过 ESP 兼容验证的成品。
6. 发送前补齐公司地址、真实退订绑定、名单同意、链接、Client QA、人工批准。
7. 本包不会发信；send_ready=false 不可用测试通过来绕过。
8. headline、subject、preheader、body 和 CTA 都属于候选审核范围。已有用户决定按 `docs/REVIEW_AND_RESUME.md` 绑定确切版本，不从其他模块继承批准。需要 Amazon + EDM 整体新品审核时，在同一项目运行 `scripts/run.py --task launch`；不要另外复制产品事实。

## Runnable local step
Run from the kit root (replace project/output with the user's separate local directories):

```bash
python3 scripts/run.py --task edm --project examples/demo-project --out outputs/demo-project/edm
```

This is the **synthetic demo**. For real work, use ignored `projects/<project-id>/` and retain unknowns. The script performs deterministic processing, not model reasoning. Continue the requested strategy/copy work in the host agent, with explicit evidence and limitations.

## Completion
Deliver the requested analysis/brief plus exact output paths, sources, unknowns, blockers and one next action. Tests do not certify factual accuracy or publication readiness. Do not claim unavailable live collection, image generation, browser QA or external writes.
