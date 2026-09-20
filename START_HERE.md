# 从这里开始

## 只想先看看

新品首选：`python scripts/demo_launch.py`，打开 `outputs/launch-complete/launch/review.html`。使用自己的资料时，让 Codex 按 `docs/TASK_CARDS.md` 引导输入；不要把 demo 改成真实项目。

已有 Python 3.10+：运行 `python scripts/demo.py`。打开 `outputs/demo-project/content/review.html`。
没有 Python：需要先安装 Python。这个工具包不自动安装系统软件，也不更改你的账户配置。

## 希望在 Codex 中使用

运行 `python scripts/install.py`，把整个目录作为项目打开，然后新开线程。
只选择一个业务入口，不必读完全部技术文件。参考 README 的五个入口表。

## 希望接入真实产品

复制品牌配置模板，运行 `scripts/new_project.py`。
在新生成的 `projects/<id>/` 填自己的证据、文案和已授权素材。
初始状态故意是 unknown / draft；不要从 Demo 复制虚构事实。

## 希望分享给他人

先阅读 `docs/RELEASING.md`。发布包与真实用户输入分开。
不要上传 outputs、projects、登录文件、原工作仓库历史或含内部数据的截图。
