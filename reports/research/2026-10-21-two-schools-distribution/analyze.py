"""Recompute the 105118 distributions from downloaded official PDF text.

Run with the bundled Python runtime (pdfplumber). Outputs preserve the
first-choice scope; adjustment lists are checked separately.
"""
from pathlib import Path
import hashlib
import json
import re
import statistics

import pdfplumber

ROOT = Path(__file__).resolve().parent
REPORT = ROOT.parent.parent / "2026两校麻醉专硕复试与拟录取分数分布-2026-10-21.md"


def pages(key):
    text_path = ROOT / f"{key}-extracted.txt"
    if text_path.exists():
        return text_path.read_text().split("\n\f\n")
    with pdfplumber.open(ROOT / f"{key}.pdf") as pdf:
        out = [p.extract_text() or "" for p in pdf.pages]
    text_path.write_text("\n\f\n".join(out))
    return out


def retest(key, school):
    out = {}
    for page, text in enumerate(pages(key), 1):
        for line in text.splitlines():
            if not re.search(r"\b105118\b", line):
                continue
            candidate = re.search(r"\b\d{15}\b", line)[0]
            values = re.findall(r"\b\d+\b", line.split("不区分研究方向", 1)[1])
            if school == "河北北方学院":
                political, english, subject, zero, score = map(int, values)
                assert zero == 0
            else:
                political, english, subject, score = map(int, values)
            assert political + english + subject == score
            assert candidate not in out
            out[candidate] = {
                "school": school, "year": 2026, "major_code": "105118",
                "batch": "一志愿", "score": score,
                "political": political, "english": english, "subject": subject,
                "retest_pdf_page": page,
                "special_plan_or_bonus_mark": "未标注",
            }
    return out


def attach_result(rows, key):
    found = set()
    for page, text in enumerate(pages(key), 1):
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if not re.search(r"\b105118\b", line):
                continue
            candidate = re.search(r"\b\d{15}\b", line)[0]
            score, interview, total = map(
                float, re.findall(r"\b\d+(?:\.\d+)?\b", line.split("不区分研究方向", 1)[1])
            )
            assert candidate in rows and rows[candidate]["score"] == int(score)
            # The unsuccessful Hebei rows wrap their result onto the next line.
            context = " ".join(lines[index:index + 2])
            if "拟录取" in line:
                result, reason = "拟录取", ""
            else:
                assert "不予录取" in context
                result, reason = "不予录取", "计划额满"
            assert abs(round(score / 5 * 0.7 + interview * 0.3, 2) - total) < 0.011
            rows[candidate].update(
                admit_pdf_page=page, source_result_row=int(line.split()[0]),
                interview=interview, weighted_total=total, result=result, reason=reason,
            )
            found.add(candidate)
    assert found == rows.keys(), (found ^ rows.keys())


BANDS = [(0, 299, "299及以下"), (300, 309, "300-309"), (310, 319, "310-319"),
         (320, 329, "320-329"), (330, 339, "330-339"), (340, 349, "340-349"),
         (350, 359, "350-359"), (360, 369, "360-369"), (370, 500, "370及以上")]


def metrics(rows):
    scores = sorted(r["score"] for r in rows)
    quartiles = statistics.quantiles(scores, n=4, method="inclusive")
    return {
        "n": len(scores), "min": min(scores), "max": max(scores),
        "mean": round(statistics.mean(scores), 2), "median": statistics.median(scores),
        "q1": quartiles[0], "q3": quartiles[2],
        "mean_without_one_min": round(statistics.mean(scores[1:]), 2),
        "median_without_one_min": statistics.median(scores[1:]),
        "under_320": sum(s < 320 for s in scores),
        "at_least_360": sum(s >= 360 for s in scores),
        "bands": {label: sum(lo <= s <= hi for s in scores) for lo, hi, label in BANDS},
        "scores_ascending": scores,
    }


hebei = retest("hebei_retest", "河北北方学院")
changzhi = retest("changzhi_retest", "长治医学院")
attach_result(hebei, "hebei_admit_http")
attach_result(changzhi, "changzhi_admit")
assert len(hebei) == 31 and len(changzhi) == 15
assert sum(r["result"] == "拟录取" for r in hebei.values()) == 27
assert all(r["result"] == "拟录取" for r in changzhi.values())

groups = {}
for school, rows in [("河北北方学院", hebei), ("长治医学院", changzhi)]:
    groups[school] = {
        "retest": metrics(list(rows.values())),
        "admitted": metrics([r for r in rows.values() if r["result"] == "拟录取"]),
    }

checks = {}
for key in ["hebei_adjust_retest", "hebei_adjust_vacancy", "changzhi_adjust"]:
    text = "\n".join(pages(key))
    checks[key] = {"105118_rows": sum(bool(re.search(r"\b105118\b", s)) for s in text.splitlines())}
    assert checks[key]["105118_rows"] == 0

payload = {
    "checked_date": "2026-10-21", "scope": "2026年105118麻醉学专硕一志愿；名单无专项/加分标记",
    "quartile_method": "线性插值，位置(n-1)*p，Python statistics.quantiles(method=inclusive)",
    "groups": groups, "adjustment_checks": checks,
    "candidates": [dict(candidate_id=k, **v) for k, v in hebei.items()] +
                  [dict(candidate_id=k, **v) for k, v in changzhi.items()],
}
(ROOT / "distribution.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

sources = [
    ("hebei_retest", "河北北方一志愿复试名单", "https://yjs.hebeinu.edu.cn/index.php?s=/Show/index/cid/11/id/441.html", "https://yjs.hebeinu.edu.cn/uploads/file1/20260327/69c60929a656c.pdf", "10-11"),
    ("hebei_admit_http", "河北北方一志愿复试成绩及拟录取名单", "https://yjs.hebeinu.edu.cn/index.php?s=/Show/index/cid/11/id/444.html", "https://yjs.hebeinu.edu.cn/uploads/file1/20260401/69ccee371982c.pdf", "6-7"),
    ("changzhi_retest", "长治一志愿复试名单", "https://yjsc.czmc.edu.cn/info/1035/17782.htm", "https://yjsc.czmc.edu.cn/__local/9/EB/58/E484A9D8E6B67A7069DD92443B7_B1AD70EC_4A008.pdf", "3"),
    ("changzhi_admit", "长治一志愿拟录取结果", "https://yjsc.czmc.edu.cn/info/1022/17962.htm", "https://yjsc.czmc.edu.cn/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=2039325458&wbfileid=813E3B8D8189610D35247E7F474F6538", "5-6"),
    ("hebei_adjust_retest", "河北北方临床医学调剂复试名单", "https://yjs.hebeinu.edu.cn/index.php?s=/Show/index/cid/11/id/453.html", "https://yjs.hebeinu.edu.cn/uploads/file1/20260411/69d9c67c6f694.pdf", "全本"),
    ("hebei_adjust_vacancy", "河北北方普通全日制调剂缺额", "https://yjs.hebeinu.edu.cn/index.php?s=/Show/index/cid/11/id/448.html", "https://yjs.hebeinu.edu.cn/uploads/file1/20260404/69d092d29b877.pdf", "全本"),
    ("changzhi_adjust", "长治调剂拟录取名单", "https://yjsc.czmc.edu.cn/info/1022/18172.htm", "https://yjsc.czmc.edu.cn/2026nianshuoshiyanjiushengzhaoshengkaoshidiaojikaoshengniluqumingdan.pdf", "全本"),
]
manifest = []
for key, title, page_url, pdf_url, relevant_pages in sources:
    path = ROOT / f"{key}.pdf"
    manifest.append(dict(key=key, title=title, page_url=page_url, attachment_url=pdf_url,
                         file=path.name, relevant_pages=relevant_pages,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(ROOT / "sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

md = ["# 2026年河北北方学院、长治医学院麻醉学专硕分数分布核验", "",
      "检索与原件复核日期：2026年10月21日。范围：105118麻醉学专业学位、全日制、一志愿。统计字段为初试总分（满分500），复试资格名单和拟录取结果按考生编号配对；名单中麻醉考生均未标注专项或政策加分。",
      "", "## 直接结论", "",
      "两校低分拟录取均不只有一个案例。河北北方301-319分拟录取7人，占27人的25.9%；长治294-319分拟录取5人，占15人的33.3%。但两校录取中位数分别为331、334，不能把301或294当作典型录取水平。",
      "", "河北北方有实际竞争：31人进入复试、27人拟录取，295/295/298/299分4人均因计划额满未录取。长治当年15人进复试、15人均拟录取；这说明2026年这批名单没有出现复试淘汰，不足以保证下一年过线即录。",
      "", "## 人数与总体分布", "",
      "| 学校及口径 | 人数 | 最低 | 最高 | 平均 | 中位数 | 第25百分位 | 第75百分位 |",
      "|---|---:|---:|---:|---:|---:|---:|---:|"]
for school in groups:
    for kind, label in [("retest", "进入复试"), ("admitted", "拟录取")]:
        m = groups[school][kind]
        md.append(f"| {school}·{label} | {m['n']} | {m['min']} | {m['max']} | {m['mean']:.2f} | {m['median']:g} | {m['q1']:g} | {m['q3']:g} |")
md += ["", "分位数采用线性插值（位置为(n-1)×p），用于描述这份名单，不是学校划定的分数线。拟录取不等于最终学籍录取。",
       "", "## 每个分数段进复试与拟录取人数", "",
       "| 初试分数段 | 河北北方进复试 | 河北北方拟录取 | 长治进复试 | 长治拟录取 |",
       "|---|---:|---:|---:|---:|"]
for _, _, label in BANDS:
    vals = [groups[s][kind]["bands"][label] for s in groups for kind in ["retest", "admitted"]]
    md.append(f"| {label} | " + " | ".join(map(str, vals)) + " |")
md += ["| 合计 | 31 | 27 | 15 | 15 |", "",
       "河北北方300-319分7人、320-339分8人，录取低分段有连续样本；300分以下4人全部未录。长治320分以下5人，同时360分及以上6人（40.0%），高低分跨度较大，均分受高分段影响；用中位数观察典型位置更合适。",
       "", "## 去掉一个最低分，判断是否会大变", "",
       "| 拟录取口径 | 原最低 | 删除一名最低分后的最低 | 原均分 | 删除一名最低分后的均分 | 原中位数 | 删除一名最低分后的中位数 |",
       "|---|---:|---:|---:|---:|---:|---:|"]
for school in groups:
    m = groups[school]["admitted"]
    md.append(f"| {school} | {m['min']} | {m['scores_ascending'][1]} | {m['mean']:.2f} | {m['mean_without_one_min']:.2f} | {m['median']:g} | {m['median_without_one_min']:g} |")
md += ["", "两个最低分确实不是孤例。删除一个最低分后，低分段仍然存在；但仍不能由这份历史样本计算个人下一年的录取概率。",
       "", "## 全部分数与结果（由低到高）", ""]
for school, rows in [("河北北方学院", hebei), ("长治医学院", changzhi)]:
    md += [f"### {school}", "",
           "| 初试排序 | 初试总分 | 复试成绩 | 综合成绩 | 结果 | 拟录取公示原序号 | 复试名单页 | 成绩公示页 |",
           "|---|---:|---:|---:|---|---:|---:|---:|"]
    for rank, row in enumerate(sorted(rows.values(), key=lambda r: (r["score"], r["source_result_row"])), 1):
        result = row["result"] + ("（计划额满）" if row["reason"] else "")
        md.append(f"| {rank} | {row['score']} | {row['interview']:.2f} | {row['weighted_total']:.2f} | {result} | {row['source_result_row']} | {row['retest_pdf_page']} | {row['admit_pdf_page']} |")
    md.append("")
md += ["## 调剂与专项口径核对", "",
       "河北北方4月3日普通全日制调剂缺额表、4月11日临床医学调剂复试名单中均无105118。缺额表中的麻醉为100217学硕，不能混入专硕样本。长治4月17日调剂拟录取名单中无105118。以上调剂材料作为旁证，分数统计始终采用已完整配对的一志愿样本；不以部分调剂材料推断河北北方全年所有批次没有补录。",
       "", "河北北方复试名单与拟录取名单末尾说明“*为退役大学生士兵专项计划”，31名105118考生无此标记。长治15名麻醉考生在复试备注及拟录取备注中均无专项、加分标记；该校3月23日单独加分公示只有105116眼科学考生，不是麻醉。",
       "", "## 对报考判断的含义", "",
       "- 300分附近：河北北方2026年有进复试后因计划额满未录的明确案例。长治有294、302分拟录取，但这两名只占15人的13.3%，不能据此按压线准备。",
       "- 310-319分：河北北方4人、长治2人拟录取，都有多个真实样本；两校该分段均低于录取中位数。",
       "- 330-340分：处于2026年录取群体的中间附近，可作为描述历史竞争位置的参照，不能叫下一年的安全线。",
       "- 初试高分并不意味着其他考生自动失去名额。长治402分考生和294分考生同批拟录取；应同时看进复试人数、实际名额、排序规则和复试表现。",
       "", "## 官方来源及留存原件", "",
       "页码均为PDF自然页，从1开始。长治官网在浏览检索端多次超时，但已直接下载校方PDF，并逐行配对、检查备注及原页图像；没有用机构最低分或均分替代原件。长治拟录取附件下载需要图片验证码，已完成下载；其永久来源为发布页和附件入口。",
       ""]
for key, title, page_url, pdf_url, relevant_pages in sources:
    md.append(f"- [{title}（官方发布页）]({page_url})；[原件留存](research/2026-10-21-two-schools-distribution/{key}.pdf)，相关页：{relevant_pages}。")
md += ["- [长治2026加分公示（官方）](https://yjsc.czmc.edu.cn/info/1022/17832.htm)。", "",
       "结构化明细、统计结果及校验来源见同目录distribution.json和sources.json；analyze.py可以从留存原件重新提取或从提取文本重新计算。每校复试名单与拟录取成绩公示的105118考生编号集合完全相等，初试单科之和等于总分，综合成绩符合初试70%＋复试30%公式（允许公示四舍五入误差）。", ""]
REPORT.write_text("\n".join(md))
print(json.dumps({"groups": groups, "adjustment_checks": checks, "report": str(REPORT)}, ensure_ascii=False, indent=2))
