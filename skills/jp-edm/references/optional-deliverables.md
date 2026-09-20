# 可选视觉与在线评审

核心包没有图像模型、登录账号、云数据库或网站部署器。只有用户要求且宿主确有工具/授权时才接入；不要新建空适配器或把缺失能力报为完成。

## 整封视觉

区分 HTML 实渲染截图、AI 场景/创意参考、分层生产稿。截图不是 AI 生成图；只有 Hero 不算整篇。为全部有序模块（含 CTA、条款和 Footer）建覆盖清单。

正式产品、Logo、UI、包装与安装关系使用授权资产；AI 只负责许可范围内的场景层；日语、价格、优惠和链接保留可编辑内容层。缺资产时输出明确的规划稿，不生成近似产品补空位。

可选 edm_series.visuals 每项：email_id、kind（html_render/ai_concept）、fingerprint（当前整封）、有序 module_ids、path（项目内 PNG/JPEG）、sha256、asset_rights（user_confirmed）。AI 参考还需 generation_record 指向实际工具记录；不能编造模型或生成来源。

程序检查文件存在、大小/头部签名、SHA-256、当前内容 hash、声明覆盖顺序和授权声明。最多返回 FILE_CHECKED_REVIEW_REQUIRED：**不解码像素、不识别画面真实覆盖、不证明模型生成来源、不授予使用权、不自动批准成图**。需要实际图片查看和人工检查；不能把改标签的截图当成 AI 全篇交付。分段图本轮由获准工具组装成整篇候选后再登记，分段内容/接缝另行检查。

文案、来源、素材、调序或 Footer 改变后，旧图标记 STALE_VISUAL，重制受影响层/段并核对全篇。更新 HTML 不会自动改栅格图。

## 浏览器与邮件客户端

按任务检查桌面和 320/375/390/414/768px，记录真实环境与未测项。程序 PASS 不代替浏览器检查。浏览器正常不等于 ESP 或收件客户端兼容，退订、名单同意与发送仍是独立 Gate。

## 网站评审

沿用用户指定的既有网站与访问范围。先确认宿主支持部署、认证、共享持久化与版本冲突控制；没有则交本地 HTML，不承诺多人同步。浏览器 localStorage 不是共享评论数据库。

意见绑定项目/邮件/模块/版本；图上意见还需资产 hash。采用前核对原文，保留冲突和历史，不能只关闭意见而不保存修改。原始邮件、个人地址、专属退订/跟踪 URL 和用户数据不进入公共示例或公共评审站。建站、上线、开放权限与 ESP 发送分别需要授权。

English: image generation, browser/ESP QA, authenticated shared comments and hosting remain explicit optional integrations. Metadata/file checks never imply pixel, provenance or human approval. The standalone package remains useful without connecting an account.
