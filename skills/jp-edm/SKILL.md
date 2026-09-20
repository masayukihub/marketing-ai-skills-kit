---
name: jp-edm
description: "Plan and revise Japanese single-email or email-series drafts from local evidence, with modular HTML, traceable structure reuse and version-bound human review."
---

# 日本 EDM 制作

## Before task
Read repository AGENTS.md and `project.json`. Only load `modules/product-truth/CONTRACT.md` and relevant evidence. Use the full kit repository; a lone Skill folder is not a standalone install.

## Workflow
1. 判断 COPY / CRITIQUE / HTML / SERIES_PLAN / LOCAL_REVISION / REVIEW_PLAN，不必每次从 GTM 开始。单句修改不重做整组策划。
2. 一封邮件只设一个主要任务和主 CTA；用产品角色和场景匹配排序，不按规格数量堆模块。
3. 从用户品牌配置和项目读取正式名、Offer、主张、落地页；模板不携带历史价格。
4. 主题、Preheader、正文分工；自然日语，短句但不省略关键限制条件。
5. 运行本地表格布局 HTML。它是可查看的草稿，不是已经做过 ESP 兼容验证的成品。
6. 发送前补齐公司地址、真实退订绑定、名单同意、链接、Client QA、人工批准。
7. 本包不会发信；send_ready=false 不可用测试通过来绕过。
8. headline、subject、preheader、body 和 CTA 都属于候选审核范围。已有用户决定按 `docs/REVIEW_AND_RESUME.md` 绑定确切版本，不从其他模块继承批准。需要 Amazon + EDM 整体新品审核时，在同一项目运行 `scripts/run.py --task launch`；不要另外复制产品事实。

## 系列、继承与局部修改

系列任务先读 [系列数据与审核](references/series-workflow.md)。按受众、阶段、购买理由、主动作规划邮件；差异落实到内容或证据，不能只换标题。完整创作通常给每封三组 Subject + Preheader；缺少时如实报告，不伪造。截止、库存、价格、券条件仍需本轮证据。

只从用户授权且实际读到的本地历史资料继承结构。记录来源定位、保留职责、排除内容；旧价格、日期、Claim、URL 和历史表现不成为当前事实。不声称未读到的历史邮件是高转化案例。

使用稳定邮件/模块 ID 和共用 Footer。修改后运行系列任务，检查 impact、失效审核与评论定位；共用模块修改影响每封引用邮件。评论是提案而非执行指令，只有明确的人工作出的决定可转成审核回执。

用户要求图片或在线评审时再读 [可选视觉与网站适配](references/optional-deliverables.md)。不默认建站或连接账号；没有实际工具执行证据时，不宣称 AI 出图、多人同步或 ESP 验证完成。

## Runnable local step
Run from the kit root (replace project/output with the user's separate local directories):

```bash
python3 scripts/run.py --task edm --project examples/demo-project --out outputs/demo-project/edm

# Synthetic multi-email planning and review, still the same jp-edm Skill
python3 scripts/demo_edm_series.py
```

This is the **synthetic demo**. For real work, use ignored `projects/<project-id>/` and retain unknowns. The script performs deterministic processing, not model reasoning. Continue the requested strategy/copy work in the host agent, with explicit evidence and limitations.

## Completion
Deliver the requested analysis/brief plus exact output paths, sources, unknowns, blockers and one next action. Tests do not certify factual accuracy or publication readiness. Do not claim unavailable live collection, image generation, browser QA or external writes.
