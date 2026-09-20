# Amazon Page Creative Contract

## Page Story Spine
What is it → Why care → How it works → Evidence → Fit → Which model → Why brand.
Gallery 服务快速购买判断；A+ 展开机制、依据和异议，不机械重复 Gallery。
Brand Promise 是品牌长期承诺；Product Philosophy 是这款产品的设计取舍；两者不混为一谈。
品牌信任只能用真实来源；不虚构销量、奖项、媒体背书或生态兼容。

## Comparison
Internal competitor matrix 可以支持研究，但绝不自动放入消费者 A+。
本实现的系列对比只接受同品牌及有来源的型号；优先 recommended_for / home_fit / key_difference。
平台实际准入、模块、图片尺寸及文案规则在生产前查当前 Amazon 官方资料。

## Copy ↔ Render
每单元绑定 consumer_question、headline、support、claim_ids、visual_proof、asset_path。
审核检查：图是否支持该句；是否暗示新功能；产品外观是否正确；手机上是否读得到。
PASS/WEAK/FAIL 是人或实际视觉审查结果；填写字段不自动 PASS。
没有真实图时是 MISSING；没有视觉审核时是 NOT_REVIEWED。
数值性能用真实测试证据，不能靠夸张场景“证明”。遮文字测试只用于视觉方向提示，不当成技术验证。

## Delivery
full 至少含 Gallery 与 A+；aplus-only 保留 Gallery，不把九宫格探索冒充 A+ 成品。
本地 runtime 输出 Page Plan、Copy-Visual Review CSV 和 review.html。
它不生成 AI 图片、不模拟已经运行的原生产器、不导出 Amazon 上传包。
真实图片只接受用户提供、确认授权的 PNG/JPEG；仍需外观与语义检查。

Runtime: `kit/creative.py`。
