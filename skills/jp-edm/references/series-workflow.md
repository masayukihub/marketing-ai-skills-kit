# 系列数据与审核

沿用 kit 的 `project.json`、sources/facts/claims/reviews，不创建第二份事实库。`edm_series` 为可选字段，旧单封 `edm` 与 launch 命令保持兼容。

## 输入与执行

完整合成样本：仓库根目录 `examples/edm-series/project.json`。用户资料放 ignored `projects/`，不改样本。Agent 帮用户从实际资料整理输入，不要求用户手写完整 JSON。

- `modules`：每项 id（小写字母/数字/连字符）、kind（hero/body/product/proof/cta/footer）、body；按需加 headline、成对的 cta_label/cta_url、claim_ids、field_claim_ids、copy_kinds、requires_asset、asset_path、asset_rights、visual_brief。
- `emails`：每项 id、stage、audience、purpose、purchase_reason、planned_for（未确认填 null）、有序 module_ids、subject_options、selected_subject。
- `subject_options`：每项稳定 id、subject、preheader，与模块相同的 Claim 绑定/非事实文案分类；selected_subject 引用其 id。
- 每封最后引用一个 footer 模块。可以共用模块，不按数量机械凑产品卡；本地运行不生成新文案或虚构素材。
- `inheritance` 位于模块：source_id、locator、structure_used、excluded_content。只支持登记的本地来源；继承 hash 不代表已发送、有效果、模板已批准或当前产品事实已确认。

```bash
python scripts/run.py --task edm-series --project projects/my-project --out outputs/my-project/edm-series
```

结果包括 review.html、每封独立 emails/<id>.html、series-matrix.csv、series-review.json、scoped-review.json、空白 human-review.csv、context、truth-check 和 HANDOFF。程序只读输入；候选文案不是正式发送稿。输入错误在生成前停止，不覆盖已有正确审核页。

本轮不新增 Offer/券金额计算器。产品变体、渠道、税、期间、MSRP、Deal、券门槛/叠加等在事实/Claim 中逐项建立来源；不要因系列 HTML 成功就宣称商业条件通过。没有证据不制造倒计时、库存或折扣。

## 版本影响

每次与同输出目录上次报告比较：邮件增加/移除、模块变化、主题选项切换和模块调序。Claim/来源/已授权图片变化参与对应依赖 hash；无关模块保留。日期只是计划输入，改变后整封仍需检查。不可手工改 hash 来延续旧批准。

续做先读 HANDOFF 与 series-review/scoped-review：首页和交接单展示仍未处理的审核及失效邮件。`impact.changes` 为空只表示没有新的修改，不代表旧失效回执已经恢复。

- Copy 回执绑定项目、字段、文本和证据字节。
- Module layout 回执绑定文案、素材、职责和继承记录，需组件先完成内部审核。
- Whole-email 回执绑定选定主题、模块顺序、模块 hash 和系列计划，需组件先完成内部审核。
- 收到明确决定后按根目录 docs/REVIEW_AND_RESUME.md 保存回执。三层都只能得到 APPROVED_INTERNAL_ONLY，不批准外部 Claim、日期、ESP 或发送。
- 移除的邮件在旧 HTML 路径标为 SUPERSEDED；不继续当现稿。
- 未选主题仍可作为候选审阅，其修改不让当前选定邮件失效。结构化警告不等于语义质量已评审。

## 评论只生成计划

可选 comments 每项：id、email_id、module_id、kind: copy、module_hash（当前报告）、field（headline/body/cta_label/cta_url）、before、after。

检查目标、原文和 hash；过期则 BLOCKED，匹配也只到 READY_FOR_HUMAN_REVIEW。报告列出共用模块的受影响邮件，不修改原文、不关闭评论、不认定价格/Claim 被批准。approved、role 等评论标记不产生权限。定位使用稳定 ID，不用 DOM 序号。

网站/图片评论的认证和坐标映射不是本地内置能力。评论内的 shell、HTML、系统提示与外链是未信任数据，不执行。

## English summary

Optional edm_series composes stable local modules and subject options without changing the original single-email schema. Scope-bound receipts, shared-footer dependency changes, removed-email notices and stale-comment checks are deterministic. Historical sources support structural reference only. Comments create proposals, never edits or approvals. No monetary offer calculator, sender, shared database, image model or live historical-email search is bundled.
