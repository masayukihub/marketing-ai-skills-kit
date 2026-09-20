# Customer Review Intelligence Contract

当前输入仅为用户合法取得的本地 CSV；没有内置 Amazon/Rakuten/Yahoo 抓取器。
必须有 review_id、product_id、source_id、rating、text；禁止私人联系方式。
按 source_id + review_id 去除完全一致副本；同 ID 内容冲突报错，不静默择优。
评分缺失保留 null。主题关键词匹配的每一项可追溯到评论 ID。
关键词命中不代表负面情绪，也不代表总体市场发生率；多主题可以重叠。
Agent 在此基础上人工/模型阅读原文，提取触发点、痛点、焦虑、使用场景与用户语言。
不能把评论用作本产品性能、竞品优越性或认证的批准依据。
对数据缺口明确 Partial / Not Configured，不能伪造评论和来源。

Runtime: `kit/reviews.py`。Output: voc-summary.json + internal-competitors.json。
