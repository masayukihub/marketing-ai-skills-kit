# 验证

```bash
python scripts/doctor.py
python scripts/sanitize_check.py
python -m unittest discover -s tests -v
python scripts/install.py
python scripts/install.py --check
python scripts/demo.py
python scripts/demo.py
python scripts/verify_nochange.py
python scripts/demo_launch.py
python scripts/demo_launch.py
python scripts/demo_edm_series.py
python scripts/demo_edm_series.py
python scripts/verify_nochange.py --launch --series
python scripts/lock_distribution.py --check
python scripts/build_release.py --dest ../clean-export-test
```

测试覆盖事实与主张、未知值、输入转义、路径安全、隐私扫描、合成数据隔离、Gallery/A+ 范围、品牌比较、文案/实图待审状态、比例算法、KOL 条件、幂等运行、输出隔离、安装覆盖保护和白名单发行。

GitHub CI 已配置 Linux/macOS/Windows 与 Python 3.10/3.12 矩阵。**配置存在不代表远程 CI 已经执行。** 实际结果以远程 run 记录为准。

可选浏览器检查：在 1440px 和 390px 打开 content/review.html 与 edm/email.html，检查横向溢出、文字、图片、表格和跳转。它只验证本地草稿，不等于 Amazon Seller Central 或 ESP 的最终渲染。

不要把单元测试通过、图片文件存在或字段齐全当成人工视觉/事实审批。

v0.2 additionally tests scoped copy/asset review invalidation, evidence expiry/conflicts, exact project aliases, launch/standalone parity, and checksum-pinned updates with local-edit protection and user-data-preserving rollback. Three synthetic launch cases cover complete textual evidence, missing evidence and contradictory evidence; none represents a real user pilot or a finished visual asset.

Human pilot acceptance is tracked separately in `docs/PILOT.md`. No unattended process may mark that acceptance complete. Privacy scans cover the exact release allowlist; confidential meaning and third-party rights still require human review.
