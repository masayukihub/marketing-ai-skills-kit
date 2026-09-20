# 中文快速开始

## 环境

Python 3.10+。核心运行不需要 pip 安装任何库。可选：Codex 用于阅读 Skill 后执行策略/文案任务；Git 和 GitHub CLI 仅在创建远程仓库时需要。

## 第一次

```bash
python scripts/install.py
python scripts/doctor.py
python scripts/demo.py
```

`LOCAL_RUNTIME_READY` 只证明本包组件与示例可用，不代表宿主 Agent、外部模型、浏览器或邮箱已测试。

查看：

- `outputs/demo-project/insights/review.html`：VOC 样本与证据。
- `outputs/demo-project/content/review.html`：完整页面草稿，含品牌和同品牌对比。
- `outputs/demo-project/campaign/review.html`：汇总 KPI。
- `outputs/demo-project/edm/email.html`：600px 上限邮件草稿。
- `outputs/demo-project/influencer/review.html`：虚构候选筛选。

## 日亚只补 A+

```bash
python scripts/run.py --task content --scope aplus --project examples/demo-project --out outputs/demo-project/aplus-only
```

不会声称 Gallery 已生产。输出目录仍需人工核对实际资产。

## 真实项目

将 `config/brand.example.json` 复制为 `config/brand.local.json`，填写品牌名、公司名和市场。

```bash
python scripts/new_project.py --id my-product --brand-file config/brand.local.json
```

在生成的项目中填 JSON 和 CSV。`project.json` 是执行时生效的品牌配置；品牌模板只用于创建项目，不会隐式覆盖现有项目。

## 下次继续

让 Codex 读项目目录、对应输出的 `HANDOFF.md`、`context.json`、`run.json`，再说明只要改哪部分。
同一数据再次运行时来源差异应为空；这不代表程序批准了事实，也不会写回你的原资料。

## 常见报错

- `source ... missing`：补齐登记的文件，不要把 source_id 删除来绕过审计。
- `Locally modified skill`：本地 Skill 有编辑，安装器不覆盖。先比较差异再处理。
- `Output belongs to another project/task`：给当前项目/任务换独立输出目录。
- `UNREVIEWED_CHANGE`：发行白名单与文件不同；先审核差异，再显式更新白名单。
- `NOT_REVIEWED / ASSET_NOT_READY`：是正确的未审核/缺素材状态，不要改成 PASS。
# 新品组合流程（v0.2）

先运行 `python scripts/demo_launch.py`，打开 `outputs/launch-complete/launch/review.html`。用同一个入口比较 launch-missing 与 launch-conflict，理解不确定信息的呈现方式。

在 Codex 中打开完整仓库，用 [新品任务卡](TASK_CARDS.md) 提供目标和本地文件；Agent 协助建立项目、登记来源和编写候选，不需要你先手填整个 JSON。先完成来源复核，再使用 `python scripts/run.py --task launch --project projects/my-launch --out outputs/my-launch/launch`。

这是内部审核包，不是 Amazon 上传包或可发送邮件。缺图仍会显著显示；本地 Python 不调用模型，策略/文案由宿主 Codex 完成。模型服务有自己的账户、费用和数据处理规则。

后续使用精确项目别名继续；审核决定按 [审核与续做](REVIEW_AND_RESUME.md) 记录。固定版本更新和回滚见 [发布说明](RELEASING.md)。
