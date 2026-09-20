# 输入格式与数据边界

## project.json

必须：`schema_version=1.0`、安全的 `project_id`、布尔 `synthetic`、`market`、`brand.name`、`product.id/name`。

`sources` 中每项：`id`、本项目内相对 `path`、`kind`、状态。真实项目不能使用 kind=synthetic。

`facts` 中每项：`id`、`field`、`value`、`unit`（可选）、`source_id`、`evidence_location`、`status`。
status 为 confirmed/pending/conflict/unknown。已确认事实必须有非空值与来源定位。

`claims` 中每项：`id`、`text`、`fact_ids`、`source_id`、`status`、市场、适用条件和有效期。
approved / conditional 还需 approval_ref。conditional 必须带 conditions。demo_only 只能在合成项目使用。
审批标识必须对应真实人工决定；脚本只检查结构，不能证明用户输入审批真的发生。

`page_units` 中每项：稳定 `id`、section、consumer_question、headline、support、claim_ids、visual_proof、asset_path、asset_rights、alt_text。
section 为 gallery/aplus/brand/comparison/faq。资产路径为空时保留缺图；图片需明确 asset_rights=user_confirmed。支持本地 PNG/JPEG，不接受 SVG/脚本。
自由输入 headline/support 仍需人工主张审查：绑定 Claim 检查不是穷尽式自然语言法务检测。

`series_comparison`：brand、name、recommended_for、home_fit、key_difference、source_id。只准同品牌；表内每个单元格仍需复核来源的真实含义。

## CSV

参照 `examples/demo-project/` 的表头。不要附私人联系方式。

| 文件 | 核心列 |
| --- | --- |
| reviews.csv | review_id, product_id, source_id, rating, text |
| campaign.csv | row_id, channel, spend, impressions, clicks, orders, revenue, currency, tax_basis, attribution_window, period, source_id |
| creators.csv | creator_id, platform, followers, recent_views, topic_fit, quoted_cost, currency, source_id |
| competitors.csv | model, brand, target_hypothesis, source_id, status |

recent_views 以竖线分隔同类视频的播放数。topic_fit 为用户提供的 0–1 判断值，不是平台原生指标。评分 rating 可空；必须是 1–5 整数或空，不得用 0 代替未知。
CSV 输出防止以 =、+、-、@ 开始的字符串被表格程序当公式；原始输入不被修改。

## 本地 Source Adapter

当前仅加载本地 UTF-8 JSON/MD/CSV 与用户提供的 PNG/JPEG。网页、Drive、Notion、飞书连接均未捆绑。
合法取得文件后，可登记到 sources 使用。不需要、也不要把账号凭据写入项目 JSON。

可选 `review_themes`：例如 `{"操作": ["設定", "ボタン"]}`。它会替换默认主题词典，便于不同品类复用；仍然不是自动语义或情绪判断。
