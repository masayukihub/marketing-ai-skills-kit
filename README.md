# Marketing AI Skills Kit

**面向营销、电商与代理团队的本地优先 AI 工作流工具包。**

版本：`0.2.0-rc2`（候选） · 默认市场：日本 · 解释语言：中文 · 消费者文案：日语

## 新品内容：一个资料源，一份审核包

面向会用 Codex 的营销人。本版将现有 Amazon 内容与 EDM 串为一条本地流程，不新增第六个 Skill：

**用户资料 → 候选事实/假设/建议/缺口 → Amazon 页面规划 + EDM 草稿 → 统一 Human Review**

```bash
python scripts/demo_launch.py
```

打开 `outputs/launch-complete/launch/review.html`。另外两个案例展示资料缺失与来源冲突。三者均为虚构数据；“资料完整”指文本证据齐全，不代表已提供正式图片或取得任何批准。

在 Codex 中打开整个仓库，然后说：

```text
使用 $jp-commerce-content，按 docs/TASK_CARDS.md 的新品任务卡处理我的本地资料。
目标是 Amazon Japan 页面规划和一封新品 EDM。
先整理候选事实、假设、建议和缺口，保留来源，不自动批准事实或 Claim。
输出一个中文审核首页、日语内容草稿与下一步；缺图保留明确占位。
```

[新品任务卡](docs/TASK_CARDS.md) · [审核与继续](docs/REVIEW_AND_RESUME.md) · [三套案例](examples/LAUNCH_CASES.md) · [真人试用说明](docs/PILOT.md)

不是某家品牌的工作空间副本，也不是一包只有提示词的目录。它包含 **5 个任务 Skill、4 个方法模块、可执行 Python 处理流程、虚构 Demo、审阅 HTML 和测试**。

## 先看结果，再接入自己的资料

已安装 Python 3.10+：

```bash
# macOS / Linux：安装仓库内 Skill、环境检查并跑五个 Demo
bash scripts/install.sh
```

Windows PowerShell：

```powershell
.\scripts\install.ps1
```

也可以跨平台直接执行：

```bash
python scripts/install.py
python scripts/doctor.py
python scripts/demo.py
```

Demo 不连接账号、不发送数据、不调用模型 API。打开 `outputs/demo-project/content/review.html` 和 `outputs/demo-project/edm/email.html` 查看结果。

**注意：本地 Demo 不等于免费使用 AI。** 本包不收费调用任何接口，但你使用的 Codex、其他模型或可选图片工具有各自的账户、权限与费用。

## 五个入口

| 我想做什么 | 在 Codex 中使用 | 本地处理结果 |
| --- | --- | --- |
| 调研 / VOC | `$jp-commerce-insights` | 去重、评分、可追溯主题、内部竞品数据 |
| 日亚内容 | `$jp-commerce-content` | 页面规划、品牌区、同品牌对比、图文审核表、HTML |
| 活动 / GTM / 复盘 | `$jp-marketing-campaign` | 可复算指标、口径检查、渠道表、复盘草稿 |
| EDM | `$jp-edm` | 单封/系列规划、模块化 HTML、继承记录、版本化审核与发送前缺口 |
| KOL | `$influencer-marketing` | 条件筛选、中位播放、历史 CPV、候选表 |

安装后，在 Codex 中打开**整个仓库目录**并开始新线程。示例：

```text
使用 $jp-commerce-content，读取 examples/demo-project。
先运行本地内容流程，再检查整页结构、品牌介绍、系列比较和文案与画面的对应关系。
缺少图片时保留占位，不能声称已经生成正式图片。输出中文审阅结论。
```

不要只下载某一个 Skill 文件夹；当前发行版的 Skill 共用仓库内脚本。默认不写入个人全局 Skill 目录。

## 能做什么，不能承诺什么

| 能力 | 本版状态 |
| --- | --- |
| 本地 JSON / Markdown / CSV 输入 | 已实现 |
| 五类任务的本地数据处理与草稿输出 | 已实现，可测试 |
| Agent 按 Skill 进行策略判断和文案创作 | 需要用户的宿主 Agent；不内置模型客户端 |
| 本地来源变更检测、下次会话 Handoff | 已实现，不自动批准记忆 |
| 新品统一审核包、精确别名、分任务 Next Action | 已实现；只生成内部审核稿 |
| 自由文案逐字段审核、Hash 绑定的局部审批失效 | 已实现；语义与证据真实性仍需人工 |
| HTML 草稿与文案/图片检查清单 | 已实现 |
| AI 产品图或场景图生成 | 未捆绑；需单独接入工具 |
| Amazon / 乐天 / Yahoo 实时抓评论 | 未捆绑；接受合法取得的本地文件 |
| 飞书 / Notion / Drive OAuth | 未捆绑；无隐藏账号依赖 |
| Amazon 上传包 / ESP 发送 / 自动发布 | 不提供 |
| 真实产品真实性、图文语义、法务保证 | 不由程序自动认证 |

示例品牌、产品、评论、KOL、商业指标均为**合成数据**。图片区域是明确标识的占位，不是 AI 出图，更不是官方产品资产。

## 使用自己的品牌

```bash
# 复制 config/brand.example.json 为 config/brand.local.json 并填写
python scripts/new_project.py --id my-product --brand-file config/brand.local.json
python scripts/run.py --task content --project projects/my-product --out outputs/my-product/content
```

填写 `projects/my-product/project.json`，把来源文件放在同一目录并登记 source ID。`projects/`、`outputs/`、`.env`、本地品牌配置均默认忽略。不要把真实资料写进公开 `examples/`。

## 核心保留方法

Product Truth 与 Claim 分离；Gallery 与 A+ 分工；品牌承诺与产品哲学分离；内部竞品研究与同品牌选型分离；文案与实际图片逐项核对；比率按分子分母汇总；事实、假设、建议分开。

## 维护与分发

- `distribution/manifest.json`：可发行文件的精确 SHA-256 白名单。
- `scripts/build_release.py`：仅导出审查过的文件，不复制 Git 历史。
- `scripts/bootstrap_github.py`：在本机经认证的 GitHub CLI 下建立**全新私有模板仓库**。
- `scripts/sanitize_check.py`：模式扫描，不能替代人工保密与权利审查。
- `distribution/allowlist.txt`：维护者明确列出的可发行文件；未跟踪文件与日志不能自动加入。
- `scripts/update.py`：校验固定版本 ZIP 和 SHA-256，预览升级/回滚，保护用户修改和数据。
- `LICENSE`：本次新编写的代码、文字和合成示例使用 MIT；不授予任何第三方/雇主资产的权利。

## 文档

[中文快速开始](docs/QUICK_START.zh-CN.md) · [English quickstart](docs/QUICK_START.en.md) · [输入格式](docs/INPUT_FORMAT.md) · [能力边界](docs/CAPABILITIES.md) · [发布与更新](docs/RELEASING.md) · [验证说明](docs/VALIDATION.md)
