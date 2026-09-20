# Marketing AI Skills Kit

**面向营销、电商与代理团队的本地优先 AI 工作流工具包。**

版本：`0.1.0-rc2` · 默认市场：日本 · 解释语言：中文 · 消费者文案：日语

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
| EDM | `$jp-edm` | 主题、Preheader、HTML、发送前缺口 |
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
- `LICENSE`：本次新编写的代码、文字和合成示例使用 MIT；不授予任何第三方/雇主资产的权利。

## 文档

[中文快速开始](docs/QUICK_START.zh-CN.md) · [English quickstart](docs/QUICK_START.en.md) · [输入格式](docs/INPUT_FORMAT.md) · [能力边界](docs/CAPABILITIES.md) · [发布与更新](docs/RELEASING.md) · [验证说明](docs/VALIDATION.md)
