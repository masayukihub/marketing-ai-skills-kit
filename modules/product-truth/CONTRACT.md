# Product Truth Contract

保留 Product / Variant / Bundle / Claim / Evidence / Market / Validity 的区别。
`confirmed` 只表示输入中的事实声明；程序只校验来源链接结构，不替人验证来源真实性。
产品事实需非空值、source_id、evidence_location。未知不得填 0。
Approved Claim 需已确认的事实、来源及 approval_ref；conditional 还需 conditions。
已过有效期、地区不符、draft/prohibited 的主张不能进入可用主张列表。
外部对比、定价、软件规划、兼容性和性能条件必须单独审核。
Demo 的 demo_only 主张不能进入真实项目。最终 publication_ready 始终为 false。

Runtime: `kit/truth.py`。Input: `project.json`。Output: `truth-check.json`。
