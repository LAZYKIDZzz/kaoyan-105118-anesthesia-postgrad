# 105118 麻醉学专硕 · 择校资料库

麻醉学专业学位硕士（105118）考研择校资料的静态站点，覆盖 94 所招生院校的 **2024—2026** 三年复试线、录取均分与人数、差额复试比及分档报考建议，并标注每所院校的**省份与所在城市**。全部页面为纯静态 HTML，可离线打开。

## 在线访问

部署完成后访问：

```
https://lazykidzzz.github.io/kaoyan-105118-anesthesia-postgrad/
```

| 路径 | 页面 | 说明 |
| --- | --- | --- |
| `/` | 择校速查 | **主页**。搜索、排序、档位筛选 94 所院校，支持按省份 / 城市检索与排序 |
| `/nav.html` | 资料导航 | 全部页面入口 |
| `/decision-mobile.html` | 报考决策表 | 手机版，含冲稳保梯度建议 |
| `/tier350.html` | **350 分以下择校分析** | 录取最低分 ≤ 350 的 67 所院校，按均分分四阶梯，含「分数带宽」指标与逐校点评 |
| `/tier350-strategy.html` | **报考组合与实操策略** | 三套冲稳保组合、复试规则核查清单、专项与调剂通道、就业门槛 |
| `/ranking.html` | 专业排名 | 33 所院校学科实力分档（A+ / A / B+ / B） |
| `/glossary.html` | 概念与术语 | 复试线、差额复试比、A/B 区等概念解释 |
| `/sources.html` | 数据来源与口径 | 档位划分标准、各校复试比例公开原文 |

配套的文字报告收录在 `reports/`，索引见 [`reports/README.md`](./reports/README.md)：

| 文档 | 内容 |
| --- | --- |
| `01-350分以下择校总报告.md` | 方法论、四阶梯全景、五个跨院校关键发现、三套组合方案、风险清单 |
| `02-分阶梯院校深度点评.md` | 67 所院校逐校独立点评 |
| `03-B区·专项计划与调剂通道.md` | B 区红利实测、专项计划分数线规则、调剂时间表与信号解读 |
| `04-岗位端验证-就业门槛与地域.md` | 从 2026 年真实招聘公告反推学历门槛、规培与英语要求、地域黏性 |

## 目录结构

```
.
├── docs/                      # GitHub Pages 发布目录
│   ├── index.html             # 主页：择校速查
│   ├── nav.html               # 资料导航
│   ├── decision-mobile.html   # 报考决策表（手机版）
│   ├── tier350.html           # 350 分以下择校分析（交互）
│   ├── tier350-strategy.html  # 报考组合与实操策略
│   ├── ranking.html           # 专业排名
│   ├── glossary.html          # 概念与术语
│   └── sources.html           # 数据来源与口径
├── reports/                   # 分析报告（Markdown）
├── src/                       # 数据与生成脚本
│   ├── data.json              # 院校数据源（94 条，含 region 省份与 city 城市）
│   └── build*.py              # 各页面与报告的生成脚本
├── *.xlsx                     # 表格源文件
└── *.html                     # 根目录留存的原始中文名页面
```

`docs/` 下的页面使用英文文件名，避免中文路径在 URL 中被编码成难以分享的长串；根目录保留中文名原件，便于本地直接打开。`docs/index.html` 与 `docs/decision-mobile.html` 比根目录原件多一个「返回导航页」入口，由 `src/sync_docs.py` 在生成后自动注入。

## 数据说明

- **来源**：各院校研究生院、附属医院及省级教育考试院公开发布的招生目录、复试细则与拟录取名单。
- **口径**：档位按 2025 年录取平均分划分（S ≥ 375 / A 365–374 / B 355–364 / C 345–354 / D < 345），而非复试线。理由与各校复试比例原文见 `sources.html`。
- **地区与城市**：`地区` 为院校所属省级行政区，`城市` 为院校所在（主校区 / 研究生培养）地级市，直辖市两者同名。个别院校多校区办学（如滨州医学院在烟台、滨州两地），城市列取考研院校代码库口径的主校区城市，实际培养校区请以当年招生简章为准。
- **局限**：表格留空表示未检索到可核验的公开数据，**不代表 0 分或未招生**。招生计划通常含推免，统考名额需另行扣减。
- **免责**：本资料仅供择校初筛，报考前请以目标院校当年官方公告为准。

## 部署

推送到 `main` 分支后由 GitHub Actions 自动部署（工作流见 `.github/workflows/deploy-pages.yml`），发布目录为 `docs/`。

首次使用需在仓库 **Settings → Pages → Build and deployment** 中把 **Source** 设为 **GitHub Actions**；未启用前工作流会在部署步骤失败，启用后在 Actions 页面重跑一次即可。此后每次推送自动更新。

## 本地预览

任选一种方式在项目根目录启动一个静态服务器：

```bash
python3 -m http.server 8000 --directory docs
```

然后打开 <http://localhost:8000>。

<details>
<summary>重新生成页面数据</summary>

表格与部分页面由 `src/` 下的脚本生成，数据源为 `src/data.json`：

```bash
python3 src/build1_三年数据统计表.py   # 三年数据统计表 xlsx
python3 src/build2_报考决策表.py       # 报考决策表 xlsx
python3 src/build3_手机版.py           # 决策表手机版 html
python3 src/build4_择校速查编辑版.py   # 择校速查 html
python3 src/sync_docs.py              # 同步上面两个 html 到 docs/（注入返回导航入口）
python3 src/build5_排名页.py           # 专业排名 html（读 docs/index.html 内嵌数据）
python3 src/build6_来源页.py           # 数据来源页 html（同上）
python3 src/build7_阶梯分析.py         # 350 分分析页 + 策略页 html
python3 src/build8_报告生成.py         # 分阶梯院校深度点评 md
```

`build7` 与 `build8` 共用同一份逐校点评文本（维护在 `build7_阶梯分析.py` 的 `NOTES` 字典中），因此网页与报告的院校点评不会出现两处不一致。

> 顺序有依赖：`sync_docs.py` 必须在 `build3` / `build4` 之后、`build5` / `build6` 之前运行——后两者从 `docs/index.html` 读取内嵌数据。`build7` 直接写入 `docs/`。

更新后请同步 `docs/` 下的对应页面。

</details>
