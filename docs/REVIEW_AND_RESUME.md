# 精确审核与项目续做 / Exact review and resume

## 审核不是外部批准

每次运行生成结构化 `scoped-review.json`；新品入口还生成 `launch-review.json` 和空白决定的 `human-review.csv`。`READY_FOR_HUMAN_REVIEW` 仅表示可以审阅，不表示所有事实、素材或渠道已通过。

每项 `item_id` 稳定对应一个文案字段或素材。fingerprint 绑定项目身份、市场、候选内容、关联 facts/claims、相关来源字节，以及素材字节/授权和所支持的文案。变更相关输入使旧签字变为 `STALE_REVIEW`；其他单元保持原状态。不以整个项目文件的修改时间一刀切撤销所有审批。

`APPROVED_INTERNAL_ONLY` 只表示当前具体版本完成内部范围审核，不会改变 facts、claims、publication_ready 或 send_ready。

## 如何记录人工作出的决定

1. 人在 HTML/CSV 中检查原文、实际图片、Source 和限制条件；在 CSV 填决定或向 Codex 明确提供 item ID 与决定。
2. Codex 只能将这次明确给出的决定，转写成项目 `reviews` 数组中的回执。未列项目不处理；不得自己填写审核者、日期或 APPROVE。
3. 从本次结构化输出复制 item_id 和 fingerprint，不重新计算“一个可通过的 Hash”。保留历史回执，新回执追加；每项最后一条是当前人工作出的决定。

回执字段：`project_id`、`item_id`、`fingerprint`、`decision`、`reviewer`、`reviewed_at`（真实审核日期，YYYY-MM-DD）、`evidence_checked`（布尔）。允许决定：`APPROVE`、`REJECT`、`NEED_MORE_EVIDENCE`、`KEEP_AS_HYPOTHESIS`。

这是本地声明记录，不是身份认证/电子签名服务。来源真实性、审核者身份和权限由项目负责人核实。没有合法证据、权利或可用 Claim 时，APPROVE 也会返回 `APPROVAL_BLOCKED`。根本没有 Source 的事实文案不能靠填布尔值批准。

文案 owner 可指定 `field_claim_ids`（字段名 → Claim ID 数组），否则沿用单元 `claim_ids`。确实不表达事实的文字可由人标为 `copy_kinds: {"cta_label":"non_factual"}`；这种分类进入指纹，仍需具名人审。不得用它遮掩事实性 headline、性能或价格。

## Next Action

旧 `state.next_action` 保留作背景。新增可选 `state.next_actions` 每项含：`id`、`text`、`priority`（p0/p1/p2）、`kind`（audit/source_refresh/review_preparation/execution）、可选 `tasks`、`blocked_by`、`requires_human_approval`。

字符串 Blocker 保持兼容；结构化 Blocker 用 `id/text/tasks/status`，默认 open，resolved 只表示输入声明。未知依赖报错。筛选任务相关动作后按优先级和 ID 排序；未解决依赖、需要人工批准、状态过期/未知或执行型动作会返回不可执行及原因。没有可行动作时退回只读审核准备，不代替人批准。

`state_as_of` 由真实状态复核决定；创建 manifest 或生成 HTML 不刷新它。`freshness_days` 是非负天数，运行时每天重算；未来日期为 unknown。

## English summary

Copy and asset receipts are exact, scoped internal reviews. They never grant external claim or publication approval. The last human receipt for an item wins; changes to content, evidence, relevant claims or assets invalidate that item, not unrelated items. Agents must not invent reviewer names, dates or decisions. Aliases identify projects only. Unknown/ambiguous names never create a project. Stale state allows audits, source refresh and review preparation, not execution.
