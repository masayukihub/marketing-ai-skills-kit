# 三个合成新品案例 / Three synthetic launch cases

运行 `python scripts/demo_launch.py`。固定演示评估日为 2026-09-20，不表示任何真实产品状态在当天得到确认。

| 案例 | 输入 | 应看到 | 不能报告 |
|---|---|---|---|
| launch-complete | 两项合成事实、两项 demo-only Claim、Gallery/A+ 与 EDM 候选 | 共享证据、逐字段审核、两项缺图提示、current 合成状态 | 正式素材齐全、外宣获批或真人试用成功 |
| launch-missing | 未确认价格、缺规格/素材/CTA | unknown、不完整范围与证据缺口，下一步补来源 | 零价格、虚构日期或完整页面已交付 |
| launch-conflict | A/B 两份互相矛盾的高度草稿 | conflict、不可用 Claim、stale、只读核实动作 | 静默选较新值、自动解决冲突 |

HTML：`outputs/<case>/launch/review.html`。结构化报告：同目录的 `launch-review.json`、`truth-check.json`、`context.json` 和 `human-review.csv`。

这些案例只说明数据与审核机制，不是营销效果证据。正式图片均未提供，图像区必须保留显著缺失标识。不要把案例里的 synthetic=true 删掉用作自己的项目。

English: complete means complete textual fixture inputs, not final imagery or approval. Missing inputs stay unknown. Conflicting drafts do not resolve by recency. Each example remains synthetic and non-publishable; human usability testing is a separate gate.
