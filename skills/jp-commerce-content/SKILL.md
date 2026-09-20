---
name: jp-commerce-content
description: "Plan Amazon Japan Gallery/A+ and source-linked copy review; orchestrate an Amazon plus EDM launch review package from local product evidence."
---

# 日本电商内容生成

## Before task
Read repository AGENTS.md and `project.json`. Only load `modules/amazon-listing-creative/CONTRACT.md` and relevant evidence. Use the full kit repository; a lone Skill folder is not a standalone install.

## Workflow
For a new-product Amazon + EDM request, read `docs/TASK_CARDS.md` and `docs/REVIEW_AND_RESUME.md` from the kit root. Use `scripts/run.py --task launch`; this remains the content entrypoint, not a new Skill. Extract only candidate context until the user confirms facts/claims. For standalone Amazon work keep the existing content task.

1. 判断 full / gallery / aplus，完整请求不能只交九宫格或 Gallery。
2. 读取 Product Truth、Claim 状态、官方素材授权；品牌名来自项目，不预设任何公司。
3. 先定消费者问题和 Page Story Spine，再分配 Gallery / A+ / Brand / Series / FAQ。
4. Brand Promise、产品哲学和信任证据分开；系列对比先写推荐人群与适用条件。
5. 每项日语文案绑定证据和视觉证明方式，不用装饰画面替代机制表达。
6. 运行本地审阅 HTML，再在可用浏览器核对 1440 / 390；没运行则写 NOT_RUN。
7. 实际图片生成需要宿主的图片工具及用户许可；本包不含图片模型。缺图不能说“已出图”。
8. 只改用户指定单元，保留已批准文件；本地输出始终不等于 Amazon 可发布。
9. 审核 headline/support 等全部自由文案，不把有效 Claim 列表误当整页通过。具名 Human Review 回执绑定当前 fingerprint；旧回执失效不能自动重新批准。图片缺失只交规划稿。

## Runnable local step
Run from the kit root (replace project/output with the user's separate local directories):

```bash
python3 scripts/run.py --task content --project examples/demo-project --out outputs/demo-project/content
```

This is the **synthetic demo**. For real work, use ignored `projects/<project-id>/` and retain unknowns. The script performs deterministic processing, not model reasoning. Continue the requested strategy/copy work in the host agent, with explicit evidence and limitations.

## Completion
Deliver the requested analysis/brief plus exact output paths, sources, unknowns, blockers and one next action. Tests do not certify factual accuracy or publication readiness. Do not claim unavailable live collection, image generation, browser QA or external writes.
