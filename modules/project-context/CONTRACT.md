# Project Context Contract

本地项目入口是 project.json。它不依赖私人 GitHub、飞书或历史聊天。
manifest/source 修改时间不自动成为 state_as_of。freshness 在读取时动态计算。
未知/过期不阻塞只读草稿准备，但禁止自动进入外部发布或正式写回。
每个项目/任务用独立输出目录；run.json 不匹配时拒绝复用。
source snapshot 用 SHA-256 识别 new/changed/removed；它只是变化检测，不生成已批准记忆。
No-change 时 source_delta 三个数组为空。输入状态不被自动更新。
新会话只读 AGENTS、单个 Skill、project.json、上次 HANDOFF；避免全仓库载入。

Runtime: `kit/context.py`。Outputs: context.json / run.json / HANDOFF.md。
