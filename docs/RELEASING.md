# 发布、更新与回滚

## 初次创建 GitHub 仓库

当前包没有 Git 历史。维护者需在自己的电脑安装 Git 和 GitHub CLI，并执行 `gh auth login`。
无需把登录 Token 发给任何人。

```bash
# 先查看计划，不会联网创建
python scripts/bootstrap_github.py --repo YOUR_OWNER/marketing-ai-skills-kit --dest ../marketing-ai-skills-kit-repo

# 确认目标后执行：只创建私有仓库
python scripts/bootstrap_github.py --repo YOUR_OWNER/marketing-ai-skills-kit --dest ../marketing-ai-skills-kit-repo --apply
```

脚本先运行检查和测试，按精确文件白名单复制到全新目录，创建独立初始提交，然后用 `gh repo create --private` 推送。
它不 Fork、不复制旧 .git、不改原仓库权限，也不会自动设为 Public。目标已存在时停止，不强推。
创建成功后尝试设为 Template；权限不足会报告，私有状态不变。

## 转为 Public 之前

人工确认：公司/雇主允许分享相应方法和内容；新文件的许可明确；没有未经授权的第三方模板/字体/图片/代码；合成数据有标签；元数据、截图和文档无内部信息。
本包 MIT 只覆盖本次新编写内容，不会把未验证的原仓库和第三方内容自动重新授权。
检查 Git 历史中只有新发行内容，再通过 GitHub Settings 明确改变可见性。
**不要把原工作仓库当作公开模板。新仓库脱敏不等于原仓库曾公开的信息已消失。**

## 更新流程：单向、需审核

1. 在维护环境查看原方法更新，形成有限的变更提案，不自动复制源目录。
2. 把通用化且权利明确的改动放进当前发行目录。公司事实、账户配置、项目状态不进入这里。
3. 运行测试、脱敏检查、Demo 和实际视觉检查。
4. 将获准的新发行文件逐个写入 `distribution/allowlist.txt` 并明确 stage 相应文件；查看 `python scripts/lock_distribution.py` 输出的 added/changed/removed。未跟踪文件、日志和用户资料不能自动加入，不能通过遍历整个工作区重建白名单。
5. 人工审查后运行 `python scripts/lock_distribution.py --write`，作为 PR 的一部分审核。
6. `python scripts/build_release.py --dest ../clean-export-vNEXT`。任何 Hash 不同即拒绝导出。
7. 在发行仓库走 PR、CI；通过真人试用、权利与公开审核后，再由明确授权的维护者创建固定版本 Tag/Release。用户按版本更新，然后重跑 install.py。本次候选不会自动发布。

## v0.2.0-rc1 候选包

```bash
python scripts/lock_distribution.py --check
python scripts/build_release.py --dest ../clean-export-v0.2.0-rc1 --zip ../marketing-ai-skills-kit-0.2.0-rc1.zip
```

生成 ZIP 与 `.zip.sha256`；导出目录和压缩包必须未存在。ZIP 只含白名单字节，排序、时间戳和权限固定。`kit.json` 是版本源；runtime、运行回执与 manifest 应一致。构建成功只表示本地候选生成，不代表已有 GitHub Release、试用通过或允许 Public。

发行代码需使用 Python 3.10+。本地 data schema 保持 1.0；新增字段可选，旧五个入口和旧项目不必迁移。没有新字段的项目保持保守候选状态。

## 用户的固定版本升级

从可信渠道取得 ZIP 和独立核对的 SHA-256。校验值只能证明拿到的是同一包，不能自动证明发布者可信。首次从旧版本升级时，可在新包的独立解压目录运行新版 updater，target 指向旧安装；不要把新包直接覆盖进去。

```bash
python scripts/update.py --zip RELEASE.zip --sha256 EXPECTED_SHA256 --target KIT_DIRECTORY
```

默认只检查，输出 from/to version、文件改动和 plan_sha256。检查计划后明确执行：

```bash
python scripts/update.py --zip RELEASE.zip --sha256 EXPECTED_SHA256 --target KIT_DIRECTORY --apply --expected-plan PLAN_SHA256
```

本地被修改的发行文件、新文件碰撞、版本/Python 不兼容、Hash 错误、越界路径或旧计划会停止。更新和恢复只处理 manifest 管理的运行文件；projects、outputs、品牌配置、凭据、Git 元数据和 Global Skills 不被修改。`.kit-backups/` 保存被替换的旧运行文件以供恢复，不能进入发行包。更新后运行 doctor、tests 和 install.py；安装器也会拒绝覆盖手工修改的 Skill 镜像。

需要回滚时使用保留的旧 ZIP 和 checksum，先加 `--rollback` 预览，再以相同参数和对应 plan 明确 apply。本地修改冲突仍停止，不靠“回滚”强制覆盖。恢复失败时保留备份并先排查，不删用户项目。

## 上游安全同步

维护环境的安全同步提案必须先审查并合并，才能成为正式同步入口；当前包不依赖任何未合并分支或私有目录。只接受通用化的逻辑、契约和合成测试，经单独 PR 审核。维护者的 source→target 映射、关键词和审批回执不得随包提供。

私有的 source→target 映射和公司定制 deny-patterns 应保留在维护者私有目录；不要发布它们来泄露被隐藏的项目名。

## 回滚

分发固定版本而非无条件跟踪源仓库 main。升级前保留旧安装包；安装器不覆盖用户修改过的 Skill。
用户数据始终在 ignored projects/outputs 内。回滚程序不应恢复或覆盖真实产品数据。

## 自动检查的边界

Scanner 只能检查模式和路径，无法识别所有商业秘密。发行白名单和人工审查必须同时保留。
CI 使用只读权限；不向 fork PR 注入 Secret，不自动部署、不自动把仓库设为公开。

## 建库后核验（rc2）

创建后会核对私有可见性、仓库身份、远程 main 与本地 HEAD，并查询该提交的 push CI。
CI 尚未开始或进行中时，退出码为 3，不代表建库失败，也不代表 CI 通过。不要重复建库或强推；只做只读复查：

```bash
python scripts/verify_github.py --repo YOUR_OWNER/marketing-ai-skills-kit --checkout ../marketing-ai-skills-kit-repo
```

只有 `all_remote_checks_passed: true` 才表示远程提交与所查工作流均已验证。模板开关单独报告，不把它当作 CI。
没有 GitHub CLI 时明确停止。脚本不会把当前会话的 GitHub 连接凭据复制到本机。
