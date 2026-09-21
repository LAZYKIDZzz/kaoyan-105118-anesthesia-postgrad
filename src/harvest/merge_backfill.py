# -*- coding: utf-8 -*-
"""合并 11 个分组采集结果，回填 src/data.json。

产出：
  - src/harvest/_merged.json  : 67 所范围内院校的规范合并结果（canonical）
  - src/data.json             : 就地补充 hist / verdict / verdict_reason / sources，
                                并按判定更新 lo/avg/n/fy/basis/fs 单年快照（无法核实者保留旧值）

用法：在仓库根目录运行
  python3 src/harvest/merge_backfill.py
"""
import json
import pathlib

HARVEST = pathlib.Path(__file__).resolve().parent
ROOT = HARVEST.parent.parent
DATA = ROOT / "src" / "data.json"
MERGED = HARVEST / "_merged.json"

YEAR_KEYS = ("2024", "2025", "2026")
YEAR_FIELDS = ("fs", "fs_kind", "fs_sub", "lo", "hi", "avg", "n", "unit", "scope_note", "note")


def load_groups():
    harvest = {}
    for g in range(1, 12):
        p = HARVEST / f"group_{g:02d}.json"
        d = json.load(open(p, encoding="utf-8"))
        for s in d.get("schools", []):
            name = s["name"]
            if name in harvest:
                raise SystemExit(f"重复院校：{name}")
            harvest[name] = s
    return harvest


def primary_year(years):
    """取【最近】一个有任意数据(lo/avg/n)的年份：2026>2025>2024。
    这样单年快照始终反映最新可核实年度，而不是被更早的年份覆盖。"""
    for y in ("2026", "2025", "2024"):
        yv = years.get(y) or {}
        if any(yv.get(k) is not None for k in ("lo", "avg", "n")):
            return y, yv
    return None, None


def main():
    harvest = load_groups()
    data = json.load(open(DATA, encoding="utf-8"))

    merged = []
    counters = {"修正": 0, "确认": 0, "补充": 0, "无法核实": 0}
    in_scope_names = set(harvest.keys())
    matched = set()

    for x in data:
        name = x["name"]
        if name not in harvest:
            # 范围外院校：不加 hist，保持原样
            continue
        matched.add(name)
        h = harvest[name]
        verdict = h.get("verdict", "无法核实")
        counters[verdict] = counters.get(verdict, 0) + 1

        years = h.get("years", {})
        hist = {}
        for y in YEAR_KEYS:
            yv = years.get(y) or {}
            hist[y] = {k: yv.get(k) for k in YEAR_FIELDS}

        # 记录原始基线，便于页面展示“旧→新”
        old = {"lo": x.get("lo"), "avg": x.get("avg"), "n": x.get("n"), "fy": x.get("fy")}

        if verdict == "无法核实":
            # 保留旧快照，仅挂核对结论
            new_lo, new_avg, new_n, new_fy = old["lo"], old["avg"], old["n"], old["fy"]
            note_suffix = "（三年核对：无法核实，保留旧值）"
            basis = (x.get("basis") or "") + note_suffix
            fs_val = x.get("fs")
        else:
            y, yv = primary_year(years)
            if y is None:
                # 三年全空且无 lo/avg/n，退回保留旧值
                new_lo, new_avg, new_n, new_fy = old["lo"], old["avg"], old["n"], old["fy"]
                basis = (x.get("basis") or "") + "（三年核对：三年均无可用数据，保留旧值）"
                fs_val = x.get("fs")
            else:
                # 任一字段缺失时回退到旧值，绝不产生 null 回退
                new_lo = yv.get("lo") if yv.get("lo") is not None else old["lo"]
                new_avg = yv.get("avg") if yv.get("avg") is not None else old["avg"]
                new_n = yv.get("n") if yv.get("n") is not None else old["n"]
                new_fy = y
                parts = [f"{y}年"]
                if new_n is not None:
                    parts.append(f"录取{new_n}人")
                if new_avg is not None:
                    parts.append(f"均分{new_avg}")
                if new_lo is not None:
                    parts.append(f"最低{new_lo}")
                basis = "，".join(parts)
                note = yv.get("note") or ""
                if note:
                    basis += f"；{note}"
                if verdict == "修正":
                    basis += "（较旧库已修正）"
                elif verdict == "补充":
                    basis += "（较旧库已补充）"
                # 复试线
                if yv.get("fs") is not None:
                    fs_val = str(yv["fs"]) + (f"（{yv['fs_kind']}）" if yv.get("fs_kind") and yv["fs_kind"] != "未公布" else "")
                else:
                    fs_val = x.get("fs")

        x["hist"] = hist
        x["hist_units"] = h.get("units", [])
        x["verdict"] = verdict
        x["verdict_reason"] = h.get("verdict_reason", "")
        x["old_snapshot"] = old
        x["sources"] = h.get("sources", [])
        x["lo"] = new_lo
        x["avg"] = new_avg
        x["n"] = new_n
        x["fy"] = new_fy
        x["basis"] = basis
        if fs_val is not None:
            x["fs"] = fs_val

        merged.append({
            "name": name,
            "region": x.get("region"),
            "city": x.get("city"),
            "level": x.get("level"),
            "existing": h.get("existing"),
            "verdict": verdict,
            "verdict_reason": h.get("verdict_reason", ""),
            "old_snapshot": old,
            "new_snapshot": {"lo": new_lo, "avg": new_avg, "n": new_n, "fy": new_fy},
            "years": years,
            "units": h.get("units", []),
            "sources": h.get("sources", []),
        })

    # 写出 merged 与更新后的 data.json
    json.dump(merged, open(MERGED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"harvest 院校数: {len(harvest)}  匹配 data.json: {len(matched)}  未匹配: {in_scope_names - matched}")
    print("判定分布:", counters)
    # 列出被“修正”的院校新旧对比
    print("\n—— 判定为「修正」的院校新旧对比 ——")
    for m in merged:
        if m["verdict"] == "修正":
            o, nw = m["old_snapshot"], m["new_snapshot"]
            print(f"  {m['name']}: 旧 lo/avg/n={o.get('lo')}/{o.get('avg')}/{o.get('n')}({o.get('fy')})  ->  新 lo/avg/n={nw.get('lo')}/{nw.get('avg')}/{nw.get('n')}({nw.get('fy')})")


if __name__ == "__main__":
    main()
