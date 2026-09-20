# -*- coding: utf-8 -*-
"""
生成《分阶梯院校深度点评》报告（reports/02），复用 build7 中的逐校点评，避免两处内容不一致。
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("b7", ROOT / "src" / "build7_阶梯分析.py")
b7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b7)

TIER_HOWTO = {
    1: "**怎么用这一档**：只在你估分稳定在 355 以上、或本科背景与科研经历明显强于平均时才考虑。"
       "把其中一两所放在「冲刺位」，绝不要当作唯一目标。",
    2: "**怎么用这一档**：这是 350 分考生应该花最多时间研究的区间。建议从中挑 2—3 所作为主力，"
       "并按地域缩小到 1—2 个省份，避免复习后期精力分散。",
    3: "**怎么用这一档**：估分 340 上下的理性落点。挑选时优先看容量（≥ 20 人）与分数带宽（越小越可预测），"
       "而不是校名。",
    4: "**怎么用这一档**：以保上岸为第一目标时的落点。B 区院校（国线 284）与 211 院校（延边、江南、青海、石河子、西藏）"
       "是本档两个主要取向，前者求稳、后者求名头。",
}

rows = b7.build_rows()
out = [
    "# 分阶梯院校深度点评 · 350 分以下麻醉学专硕（105118）",
    "",
    "> 配套文档：《350 分以下择校总报告》《B 区·专项计划与调剂通道》《岗位端验证》  ",
    "> 数据来源：本项目 `src/data.json`（各院校研究生院公开招生目录、复试细则与拟录取名单）  ",
    "> 范围口径：录取最低分 ≤ 350；若缺最低分数据，则取录取均分 ≤ 350",
    "",
    "---",
    "",
    "## 阅读说明",
    "",
    "每所院校给出四个数字与一段独立点评：",
    "",
    "| 指标 | 含义 | 怎么读 |",
    "| --- | --- | --- |",
    "| **最低分** | 公开录取名单中的最低初试分 | 决定该校是否进入本报告范围；**不等于你的目标分** |",
    "| **均分** | 录取考生的平均初试分 | 真实的竞争中枢 |",
    "| **带宽** | 均分 − 最低分 | 越大说明录取分越离散，低分窗口越可能来自专项计划或扩招末位 |",
    "| **人数** | 录取规模 | 低于 3 人时，前三个数字的统计意义都很弱 |",
    "",
    "**点评为逐校人工分析，不使用模板句式。** 凡涉及 2026 年复试规则、招生计划的表述，均来自院校公开文件或权威转载；"
    "凡来自考研机构口径的信息，文中已注明。",
    "",
    "---",
    "",
]

TIER_TITLE = {
    1: "阶梯一 · 窗口档（均分 ≥ 358）",
    2: "阶梯二 · 匹配档（均分 348 — 358）",
    3: "阶梯三 · 稳健档（均分 340 — 348）",
    4: "阶梯四 · 保底档（均分 < 340）",
}

idx = 0
for t in (1, 2, 3, 4):
    group = [r for r in rows if r["tier"] == t]
    out += [
        f"## {TIER_TITLE[t]}",
        "",
        f"共 **{len(group)} 所**。{b7.TIERS[t]['desc']}",
        "",
        TIER_HOWTO[t],
        "",
    ]
    for r in group:
        idx += 1
        lo = r["lo"] if r["lo"] else "—"
        band = r["band"] if r["band"] is not None else "—"
        n = r["n"] if r["n"] else "—"
        out += [
            f"### {idx}. {r['name']}",
            "",
            f"`{r['level']}` · {r['region']} ｜ 最低 **{lo}** ｜ 均分 **{r['avg']}** ｜ 带宽 **{band}** ｜ 录取 **{n}** 人",
            "",
            r["note"] or "（暂无点评）",
            "",
        ]
        if r["basis"]:
            out += [f"<sub>数据依据：{r['basis']}</sub>", ""]
    out += ["---", ""]

out += [
    "## 附：未纳入范围的院校",
    "",
    "以下院校因「均分高于 350」或「缺少分数数据」未进入本报告，但它们仍可能是 350 分左右考生的可及目标，"
    "仅因数据缺口而被排除，列出以免误读为「考不上」：",
    "",
]
try:
    import json
    alld = json.load(open(ROOT / "src" / "data.json", encoding="utf-8"))
    scope = {r["name"] for r in rows}
    gaps = [x for x in alld if x["name"] not in scope and not x.get("lo")]
    for x in sorted(gaps, key=lambda y: -(y.get("avg") or 0)):
        avg = x.get("avg") or "—"
        out.append(f"- **{x['name']}**（{x['region']} · {x['level']}）均分 {avg}，缺最低分数据")
except Exception as e:  # pragma: no cover
    out.append(f"- （读取失败：{e}）")

out += [
    "",
    "> 说明：上表院校中有相当一部分（如新乡医学院、广西医科大学、郑州大学、东南大学、南京大学、同济大学、"
    "南华大学等）在检索中被提及为麻醉学招生单位，但公开渠道未获得可核对的录取分数，因此无法纳入量化分档。"
    "如需扩展范围，应先补齐这些院校的最低分与均分数据。",
    "",
]

dest = ROOT / "reports" / "02-分阶梯院校深度点评.md"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text("\n".join(out), encoding="utf-8")
print(f"已生成 {dest} （{len(rows)} 所院校，{sum(1 for r in rows if r['note'])} 条点评）")
