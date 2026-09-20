---
name: influencer-marketing
description: "Evaluate creator candidates from user-supplied evidence, filter by audience/platform, draft briefs and estimate historical CPV without contacting anyone."
---

# KOL 合作策划

## Before task
Read repository AGENTS.md and `project.json`. Only load `modules/product-truth/CONTRACT.md` and relevant evidence. Use the full kit repository; a lone Skill folder is not a standalone install.

## Workflow
1. 确定目标、市场、平台、预算、人群与内容适配标准，不只看粉丝。
2. 读取本地候选与样本播放。匹配评分是人的判断，不冒充可观测事实。
3. 用近期同类型视频中位播放评估，注明样本数量；历史 CPV 不是预测结果。
4. 未联网核实的合作历史、粉丝量、联系方式不能编造；不用虚构美元价格表当日本报价标准。
5. 给出真实卖点、演示任务、禁区、CTA、Disclosure、创作者发挥空间。
6. 商业合作披露规则需按执行地和平台查当前官方说明，不能把单一国家规则当全球规则。
7. 合同、素材二次使用、排他期和报价单独确认。不会自动邀约、发邮件或代签。

## Runnable local step
Run from the kit root (replace project/output with the user's separate local directories):

```bash
python3 scripts/run.py --task influencer --project examples/demo-project --out outputs/demo-project/influencer
```

This is the **synthetic demo**. For real work, use ignored `projects/<project-id>/` and retain unknowns. The script performs deterministic processing, not model reasoning. Continue the requested strategy/copy work in the host agent, with explicit evidence and limitations.

## Completion
Deliver the requested analysis/brief plus exact output paths, sources, unknowns, blockers and one next action. Tests do not certify factual accuracy or publication readiness. Do not claim unavailable live collection, image generation, browser QA or external writes.
