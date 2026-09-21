# -*- coding: utf-8 -*-
"""
生成 350 分以下择校分析页面：
  docs/tier350.html           —— 全景分析（可筛选 / 可排序 / 逐校点评）
  docs/tier350-strategy.html  —— 报考组合与实操策略

数据源：src/data.json
范围口径：录取最低分 ≤ 350，或（无最低分数据但）录取均分 ≤ 350
"""
import json
import pathlib
import html

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data.json"
DOCS = ROOT / "docs"

# ---------------------------------------------------------------- 阶梯定义
TIERS = {
    1: {
        "code": "T1",
        "name": "阶梯一 · 窗口档",
        "sub": "均分 ≥ 358 ｜ 350 分可搏，但中枢竞争在 358 以上",
        "desc": "这一档的共同特征是：最低录取分确实落到了 350 以下，但录取均分明显更高。"
                "换句话说，窗口真实存在，只是窗口很窄——需要靠复试、靠年份运气、靠名额变化去撬。"
                "本档 17 所院校中有 6 所是 985、3 所是 211 或双一流，平台价值最高，风险也最高。",
        "tone": "risk",
    },
    2: {
        "code": "T2",
        "name": "阶梯二 · 匹配档",
        "sub": "均分 348 — 358 ｜ 350 分的主战场",
        "desc": "350 分考生最应该把注意力放在这一档。均分与你的目标分基本重合，"
                "意味着你不是在赌运气，而是在一个相对公平的赛场里靠复试取胜。"
                "本档既有武汉大学、兰州大学这样的 985，也有温州医科大学、广州医科大学这类省级龙头。",
        "tone": "core",
    },
    3: {
        "code": "T3",
        "name": "阶梯三 · 稳健档",
        "sub": "均分 340 — 348 ｜ 有一定安全垫",
        "desc": "如果你的初试估分在 340 上下，这一档是理性的落点。"
                "录取均分低于 350，说明你的目标分本身就高于中枢，报考时拥有真实的位次优势。"
                "注意大连医科大学（48 人）、延安大学（29 人）、山东第二医科大学（30 人）这类大容量院校。",
        "tone": "safe",
    },
    4: {
        "code": "T4",
        "name": "阶梯四 · 保底档",
        "sub": "均分 < 340 ｜ 含 B 区低分通道",
        "desc": "以保上岸为第一目标时的落点。包含大量 B 区院校（国家线 284）、"
                "若干 211（延边大学、江南大学、青海大学、石河子大学、西藏大学）以及 985 的极低门槛入口（厦门大学）。"
                "本档最大容量院校为新疆医科大学（62 人）与内蒙古医科大学（43 人）。",
        "tone": "floor",
    },
}

# ---------------------------------------------------------------- 逐校点评
NOTES = {
    # ============================== 阶梯一 ==============================
    "浙江大学": "全国录取均分最高的梯队（383 分），却挂着 328 的最低分——55 分的带宽是全表最悬殊的之一。"
              "6 人的容量加上浙大自身推免占比偏高，统考实际可竞争力的位次极少。328 这个数字几乎可以断定是专项计划"
              "或个别年份的末位现象，不具备可复制性。以 350 分报考浙大，本质是在为极小概率付费。",
    "南方医科大学": "华南地区龙头，检索显示其省人民医院临床学院录取均分高达 402。25 人容量不算小，但 378 的均分说明中枢竞争极激烈，"
                 "344 的最低分与均分相差 34 分。若目标锁定华南，更务实的做法是把它当冲刺位、把广州医科大学（354）当主力位。",
    "吉林大学": "985 平台 + 28 人容量，但均分 375。校线仅 320 左右，与实录取分之间拉开 49 分——这是「校线低、录取高」最典型的样本之一。"
             "对 350 分考生来说，校线不构成机会，375 才是真相。此外吉大三个附属医院（白求恩第一/二/三临床医学院）分列招生，"
             "报考时必须明确到具体学院，否则报名单位一错，分数再高也无用。",
    "西安交通大学": "10 人容量、均分 374、最低 347。347 与 350 只差 3 分，是「卡线可及」里最紧的一个。西北地区 985 医学平台，"
                 "就业辐射陕甘宁。适合分数稳定在 345 以上且愿意承担风险的考生——但 10 人容量意味着任何一年缩招，门槛都会立刻跳升。",
    "福建医科大学": "福建省内绝对龙头，34 人容量是阶梯一里最大的之一。均分 369、最低 345、带宽 24 分，分数分布相对集中。"
                 "对明确要在福建就业的考生，「省属龙头 + 容量充足」比跨省冲 985 更有实际价值。",
    "南京医科大学": "江苏医学第一梯队（省属重点，非 211 但业内地位高）。34 人容量、均分 367、最低 329，带宽 38 分说明年份波动明显。"
                 "江苏医疗市场对南医大认可度极高，省内就业优势显著。350 分属于边缘可搏，建议与苏州大学、南通大学、江苏大学组成省内梯度。",
    "上海交通大学": "临床医学学科评估 A+，全国顶级平台。15 人容量、均分 366、最低 334。上交医学院对本科出身、科研经历、"
                 "临床技能的敏感度极高，初试只是入场券。以 350 分报考，通常需要复试表现极其亮眼才有胜算。",
    "山东大学": "带宽只有 15 分，是全表最紧凑的院校之一——说明录取分数高度集中在 350—370 区间，不存在真正的低分窗口。"
             "349 的最低分仅比 350 低 1 分，严格说是「名义在范围内、实质不在」。7 人容量偏少，报考性价比取决于能否稳定考到 360 以上。",
    "哈尔滨医科大学": "46 人容量是阶梯一里最大的。东北麻醉学科传统强校，均分 363、最低 341、带宽 22 分，分数结构健康。"
                 "对黑吉辽及周边省份就业辐射力强。345 分以上的考生可以认真考虑：这是「高容量 + 中等门槛」的合理组合，代价是接受地域限制。",
    "中国医科大学": "全表带宽最大的一所（58 分）：均分 363，最低却到 305。42 人容量，2026 年专硕计划较上年明显扩招（不同来源口径为 29—33 人）。"
                 "2026 年复试线 305 分，但单科线 45/170 偏高，需要留意单科短板。305 的最低分很可能是扩招末位或专项计划，不能直接当目标；"
                 "不过扩招确实给了分数线下行空间。建议定位为「扩招红利 + 大容量」的冲击位，目标分定在 340 以上更稳。",
    "河北医科大学": "2026 年专硕计划 45 人，较上年 22 人翻倍（+105%），且公开信息显示无推免挤压——扩招幅度在全表里最突出。"
                 "但均分 362 说明河北考生基数大、一志愿长期爆满：执行国家线（294）意味着过线就能进复试，"
                 "可实际录取均分高出国家线近 70 分。省级龙头，临床医学学科评估 C+。适合作为华北考生主力的「扩招 + 高容量」选择，目标分建议 355 以上。",
    "宁波大学": "双一流（非 211 但有牌面），13 人容量、均分 362、最低 307，带宽 55 分。依托宁波市医疗资源，长三角就业。"
             "如此大的带宽说明录取分数离散度很高，307 这类低分大概率来自专项计划或个别年份。"
             "浙江考生若冲不上浙大与温医大，宁大提供的是「双一流名头 + 长三角」组合，但必须正视 362 的均分。",
    "华中科技大学": "同济医学院平台，临床医学学科评估 A，麻醉在重症与器官移植方向有特色。但 8 人容量 + 带宽仅 17 分，"
                 "录取高度集中在 355—375 区间，几乎没有低分空间。345 的最低分与 350 仅差 5 分。"
                 "以 350 分报考华科属于低概率事件，建议仅在估分稳定 360 以上时考虑。",
    "安徽医科大学": "47 人容量是阶梯一中最大的之一，均分 360、最低 308、带宽 52 分。安徽省内医学龙头。"
                 "值得特别注意的是，检索显示其安庆医学中心等合作附属单位录取均分只有 300 出头，而本部竞争激烈——"
                 "这是「考得好不如报得好」最典型的样本。报考时务必锁定到具体培养单位。",
    "南昌大学": "61 人容量，是全表第二大招生规模（仅次于新疆医科大学）。211 平台、均分 359、最低 327、带宽 32 分。"
             "江西唯一 211，省内就业垄断性强。大容量叠加中等门槛，意味着分数分布宽、机会窗口相对真实——"
             "对 350 分考生而言，这是「211 名头 + 超大容量」的三重划算项，值得列为主力候选。",
    "川北医学院": "四川省属医科，22 人容量、均分 359、最低 331。川渝医疗市场竞争激烈，川北医学院（南充）在川东北地市三甲有稳定输送渠道。"
               "均分 359 对其省属定位而言偏高，反映四川考生基数庞大。适合明确要留在川东北就业的考生。",
    "首都医科大学": "北京医学第二极（临床医学学科评估 A-），双一流。12 人容量、均分 358、带宽仅 16 分，分数高度集中——"
                 "这意味着没有低分机会，342 是实打实的下限。附属医院（宣武、天坛、朝阳等）资源顶级，北京市场认可度极高。"
                 "350 分报考属于贴线，需要复试表现稳健。",

    # ============================== 阶梯二 ==============================
    "苏州大学": "211 + 苏州区位，长三角医疗资源密集。13 人容量、均分 356、最低 320、带宽 36 分。附属第一医院为省内顶级。"
             "320 的低分窗口确实存在，但 36 分的带宽也说明年份波动不小，不能把 320 当预期。江苏考生冲不上南医大时，苏大是优质备选。",
    "湖州师范学院": "带宽仅 9 分（全表最小），但均分 356 却只有 5 人容量。师范院校办的医学，录取分数反而高且高度集中，"
                 "说明报考群体多为本地定向、竞争相对封闭。5 人容量容错率极低，对 350 分考生并不友好，除非有明确的地域绑定或导师联系。",
    "广东医科大学": "31 人容量、均分 354、最低 327。这所学校的复试规则需要特别预警：2026 年公开复试办法明确"
                 "临床医学专业学位按 1:2 差额复试，且复试基本分数线就是国家 A 类线（294）。"
                 "入门槛很低但淘汰率极高，属于典型的「易进难出」——327 的最低录取分正说明被刷掉的恰是低分考生。复试能力偏弱的考生慎选。",
    "广州医科大学": "广东省属重点，呼吸与危重症学科全国领先。27 人容量、均分 354、最低 313、带宽 41 分。珠三角就业优势极强。"
                 "检索显示该校 2026 年麻醉学有调剂名额，说明一志愿存在缺额或结构缺口。"
                 "对目标锁定珠三角的考生，这是「地域 + 平台」性价比很高的一所。",
    "兰州大学": "985 平台，16 人容量、均分 354、最低 334、带宽 20 分，分数结构健康。甘肃属 B 区省份，但兰大作为自划线院校执行自己的校线。"
             "这是「985 名头 + 350 分真正可及」最现实的组合之一：均分 354 意味着 350 分考生在这里是有竞争力的。"
             "对想在学历层次上不留遗憾的考生，兰大值得优先评估。",
    "暨南大学": "211、侨校，医学部在广东属第二梯队。14 人容量、均分 354、最低 323。2026 年复试办法明确：临床医学类专硕按教育部公布的"
             "临床医学类考生进入复试要求执行；少骨计划与士兵计划在 A 线基础上总分上调 15 分。珠三角就业。性价比不错，主要制约是容量偏小。",
    "海南医科大学": "海南省属，属 B 区（国家线 284），但均分 353——说明「B 区 + 海南气候与政策」吸引了大量生源，B 区红利被部分抹平。"
                 "9 人容量偏小，带宽 15 分紧凑。检索显示该校药学、公卫、基础医学有大量调剂缺额，但麻醉学未列其中，"
                 "说明麻醉一志愿基本能满足。优势是 B 区国线，短板是容量小、均分不低。",
    "武汉大学": "985 医学部（原湖北医科大学）平台，19 人容量、均分 352、最低 336、带宽 16 分紧凑。"
             "这是阶梯二里最值得注意的一所：同为湖北 985，武大均分 352 比华中科技大学（362）低 10 分，容量还大出一倍多。"
             "对想要 985 学历的 350 分考生，武大医学部是本档的优先项，需留意其复试对科研与英语的要求。",
    "温州医科大学": "信息量最大的一所。47 人容量、均分 351、最低 295、带宽 56 分。麻醉学是国家级一流本科专业建设点，"
                 "拥有浙江省麻醉学重点实验室，附属第一、第二医院年麻醉量超 10 万例。"
                 "关键公开数据：2026 年麻醉学专硕复试线为 350 分（第一临床医学院）；2026 年拟招专硕 39 人（一临床 19 / 二临床 20），"
                 "其中推免与「5+3」一体化占约 10 人，统考约 28—29 人；2026 年第二临床医学院麻醉学拟录取名单初试分集中在 353—382 之间。"
                 "解读：350 分的复试线 + 351 的录取均分，意味着 350 分考生恰好卡在「有资格进场、但必须靠复试取胜」的位置。"
                 "295 的最低分极可能来自专项计划或研究生培养基地，不能作为目标分。整体是「专业实力强 + 招生体量大 + 地处浙江」的均衡选择。",
    "山西医科大学": "山西医学龙头，31 人容量、均分 351、带宽 17 分紧凑。华北老牌医学院，省内就业强势。"
                 "分数分布集中说明竞争充分、无捡漏空间，但要的是可预测性——这一点对求稳考生反而是优点。适合山西及周边省份作为主力位。",
    "西北民族大学": "B 区省属，公开复试办法明确：一志愿复试基本线即 B 类国家线（284），临床医学 1051 按教育部临床医学专业学位分数线执行，"
                 "不进行破格复试。但招生仅 2 人，均分 350 的样本量太小，参考价值有限。"
                 "适合具备少数民族政策资格、或愿意接受极小容量的 B 区求稳考生。",
    "昆明医科大学": "云南省医学龙头，42 人容量、均分 349、最低 305、带宽 44 分。云南属 B 区。"
                 "「B 区国线（284）+ 42 人容量 + 均分 349」的组合对 340 分左右的考生相当友好，是本档里容量与平台最均衡的选择之一。"
                 "带宽 44 分说明存在真实的低分录取，但逐年核实是否为专项计划仍然必要。",
    "蚌埠医科大学": "原蚌埠医学院，安徽省属，29 人容量、均分 349、最低 323、带宽 26 分。"
                 "检索显示其非直属医院专硕录取均分约 330，明显低于本部——再次印证同一学校不同培养单位差异巨大。"
                 "安徽考生冲不上安医大时的务实选项。",
    "贵州医科大学": "贵州省医学龙头（B 区），21 人容量、均分 349。疼痛医学方向是特色：检索显示其麻醉学院疼痛方向 2026 年录取 6 人、"
                 "均分 338，明显低于麻醉方向。这个方向差异意味着校内存在「换赛道」降门槛的空间，值得关注。",
    "成都医学院": "四川省属，14 人容量、均分 349。前身为第三军医大学成都军医学院，临床资源依托成都军区总医院系统，成都市域就业。"
               "本项目数据中缺少该校的最低录取分，无法评估分数波动，报考前需自行核实。",

    # ============================== 阶梯三 ==============================
    "绍兴文理学院": "5 人容量、带宽 11 分，均分 346。浙江地方院校的录取分却逼近 350，说明浙江整体分数水位偏高，"
                 "地方院校也不便宜。容量太小，容错率低，适合有明确绍兴或浙东地域规划的考生。",
    "江苏大学": "江苏综合类大学，8 人容量、均分 345，镇江区位。检索显示该校 2026 年麻醉学开放调剂。"
             "对江苏考生而言是合理的保底位，但招生量偏小，需接受不确定性。",
    "山东第一医科大学": "原泰山医学院与山东省医学科学院合并组建，28 人容量、均分 344、最低 297、带宽 47 分。"
                    "济南为主校区，处于扩招与整合期，分数波动较大。山东省内医疗资源丰富且竞争激烈，山一大属省内第二梯队，对 340 分左右考生友好。",
    "杭州师范大学": "仅 3 人容量，均分 344。杭州区位加附属医院。容量过小意味着实际录取波动会非常剧烈，"
                 "不建议作为主报考目标，除非已有明确的导师定向联系。",
    "遵义医科大学": "原遵义医学院，贵州省属（B 区），24 人容量、均分 343、最低 310、带宽 33 分。"
                 "红色老校，临床医学底蕴扎实。B 区国线叠加 300—340 的分数段，是西南地区性价比突出的选择。",
    "沈阳医学院": "8 人容量、均分 343。沈阳市属院校，东北地区分数水位相对较低。可视为中国医科大学的低配替代选项，"
               "适合明确要留在辽宁就业的考生。",
    "山东第二医科大学": "原潍坊医学院，30 人容量、均分 342、带宽仅 16 分。容量大且分数高度集中，是可预测性最好的选择之一，"
                   "适合以「稳定上岸」为第一目标的考生。临床麻醉培养扎实，就业以地市三甲为主。",
    "宁夏医科大学": "B 区省份，20 人容量、均分 342、最低 294（约为 B 区国线 +10）、带宽 48 分。"
                 "检索显示其第三临床学院（自治区人民医院）2026 年麻醉专硕 15 人、均分 342，2025 年 346，稳定性不错；"
                 "同时 2026 年麻醉学有 3 个调剂名额。「B 区国线 + 中等容量 + 均分 342」是典型的高性价比保底组合，就业以宁夏及西北为主。",
    "赣南医科大学": "原赣南医学院，江西省属，14 人容量、均分 342、最低 303。江西省内中坚，就业以赣南地区为主。"
                 "检索显示江西某校 2026 年麻醉专硕录取 27 人、均分 340，与该校数据接近，可交叉参考。",
    "延安大学": "29 人容量是阶梯三中最大的之一，陕西省属。均分 341，本项目数据缺最低分。"
             "容量大叠加门槛低，对西北考生是务实选择，但需评估陕北地区临床资源与规培条件的实际水平。",
    "南通大学": "江苏南通，19 人容量、均分 341、最低 301、带宽 40 分。附属医院为省级区域医疗中心，南通医疗资源在江苏省内属中上，"
             "本地就业认可度好。江苏考生冲不上南医大与苏大时的稳健备选。",
    "西安医学院": "陕西省属，18 人容量、均分 341、带宽 19 分。西安区位叠加西安市属医院网络。"
               "陕西省内竞争激烈（西安交大、空军军医大学等强校环伺），西医属中下游但容量稳定，适合留陕考生。",
    "大连医科大学": "48 人容量，是阶梯三中最大的，且本身是省属重点——这是本档「容量 + 平台」双优的选择。"
                 "均分 340、最低 298、带宽 42 分。东北地区第一梯队医科院校，48 人的容量意味着录取机会显著高于同档院校。"
                 "对 340 分左右考生性价比很高，主要取舍点是东北的地域限制。",

    # ============================== 阶梯四 ==============================
    "大理大学": "云南 B 区，15 人容量、均分 339。滇西地区医疗人才培养重镇，临床资源依托大理州及周边医院。"
             "B 区国线（284）叠加 339 的均分，门槛在保底档中属中等，适合西南地区求稳考生。",
    "承德医学院": "河北省属，17 人容量、均分 337、最低 305、带宽 32 分。河北考生基数大、竞争激烈，"
               "承德医学院位于河北分数梯队的中下段。适合河北省内冲不上河北医科大、又不想出省的考生。",
    "江南大学": "211 平台，9 人容量、均分 337、最低 310、带宽 27 分。无锡区位，长三角就业。"
             "这是保底档中少见的 211，均分 337 意味着 340 分左右就有真实竞争力。容量 9 人不算大，但相比同档的其他 211（厦门大学 3 人、"
             "石河子大学 3 人、西藏大学 3 人）已属宽裕。对想要 211 学历又不想冒险的考生，这是本档首选。",
    "延边大学": "保底档里最值得推荐的一所。211 平台、37 人容量、均分 336、最低 309、带宽 27 分。"
             "更特别的是，延边大学麻醉学允许用日语（203）替代英语（201）——这对外语为日语的考生是几乎唯一的通道。"
             "2024 年该专业统考招生 18 人（不含推免）。「211 + 大容量 + 336 均分 + 日语通道」四项叠加，性价比在整个 350 分以下区间里都属顶尖。",
    "青海大学": "211 + B 区双重红利，17 人容量、均分 336、最低 291、带宽 45 分。B 区国线 284，"
             "意味着过线不远即有机会进入复试。西北地区 211 医学平台，就业以青海及周边为主。"
             "适合把「211 学历 + 低门槛」放在首位的考生，但需评估高原环境与地域发展的长期取舍。",
    "湖南师范大学": "211，7 人容量、均分 336。师范院校办医学，依托湖南师大附属医院系统。容量偏小，"
                 "适合湖南省内考生作为保底位，或作为长沙区位的一个补充选项。",
    "厦门大学": "985 平台里门槛最低的入口——均分 336、最低 304。但容量只有 3 人，风险极高。"
             "厦大医学院 1996 年成立，临床医学底子相对薄，2026 年医学门类复试线为 295 分（单科 45/150）。"
             "「985 名头 + 3 人容量」的组合意味着：只要某一年出现两三个高分考生，分数线就会瞬间抬起来。"
             "适合有明确厦门就业意向、且能接受高不确定性的考生，不建议作为唯一目标。",
    "内蒙古医科大学": "B 区省属，43 人容量、均分 335、最低 285、带宽 50 分。这是本档容量第二大的院校。"
                  "检索显示其第一临床医学院招生规模逐年波动（2024 年 9 人、2025 年 14 人、2026 年 5 人），"
                  "报考人数少时分数会明显偏低——这正是带宽 50 分的成因。"
                  "「B 区国线 + 大容量」是它的核心优势，但需注意各附属医院招生人数年际波动很大，务必以当年目录为准。",
    "皖南医学院": "安徽省属，42 人容量、均分 335、最低 304。安徽省内中坚，容量大、门槛低，"
               "检索中被列为「低分选手可冲」的院校之一。适合安徽及周边省份以保上岸为目标的考生。",
    "甘肃中医药大学": "甘肃 B 区，14 人容量、均分 333。中西医结合背景的省属院校，麻醉学偏疼痛与中西医结合方向。"
                  "B 区国线叠加 333 的均分，门槛在保底档中偏低，适合西北地区求稳考生。",
    "扬州大学": "江苏省属，8 人容量、均分 333、最低 299、带宽 34 分。扬州医疗资源在江苏省内属中等，"
             "苏中地区就业认可度尚可。容量偏小，适合江苏考生作为梯度中的保底位。",
    "锦州医科大学": "辽宁省属，42 人容量、均分 332、最低 307、带宽 25 分。容量大叠加门槛低，"
                 "检索中亦被列为对低分友好的院校。辽宁及东北地区就业。适合以保上岸为目标的东北考生。",
    "长治医学院": "山西省属，17 人容量、均分 326。山西本地医学人才输送院校，临床资源依托长治及晋东南医院系统。"
               "门槛在保底档中偏低，适合山西考生作为兜底选择。",
    "昆明理工大学": "云南省属，仅 4 人容量、均分 325、最低 286、带宽 39 分。理工大学办医学（依托昆明理工大学医学院），"
                 "容量极小、分数波动大。286 的最低价接近 B 区国线（284），但 4 人的容量使这类型号的可复制性很差，"
                 "不建议作为主要目标。",
    "新疆医科大学": "全表容量最大的一所，62 人。B 区省份，均分 324、最低 283、带宽 41 分。"
                 "公开的 2026 年拟录取统计显示：全校拟录取约 1774 人，麻醉学录取规模位列全校前十（公开口径约 74—99 人，含不同学位类型）；"
                 "全校录取初试分中位数 319，一志愿均分 320.59，调剂均分 316.37；复试淘汰率约 16.2%。"
                 "解读：这是一所「体量巨大、门槛低、复试友好」的院校，一志愿均分甚至略高于调剂均分，说明一志愿考生并未吃亏。"
                 "对分数在 320—340 区间、以稳妥上岸为核心目标的考生，新疆医科大学是本档最具确定性的选择，代价是地域。",
    "湖北医药学院": "湖北省属，19 人容量、均分 324、最低 295、带宽 29 分。湖北省内竞争激烈（武大、华科等强校林立），"
                 "湖北医药学院位于分数梯队下段，对湖北省内考生是务实的保底位。",
    "西藏大学": "211 + B 区双重红利，但容量仅 3 人。均分 321，本项目数据缺最低分。"
             "B 区国线 284 叠加 211 名头，理论门槛极低；然而 3 人容量使实际风险很高，且需评估高原环境与长期发展。"
             "适合有明确援藏定向、或有西藏生源背景的考生。",
    "广东省心血管病研究所": "本档唯一的科研院所（广东省人民医院下属）。2026 年公开复试方案明确：专硕（1051）复试线总分 310，"
                      "英语 45、政治 45、西综 160；临床医学专业学位按 1:3（计划 =1）、1:2（计划 =2）、1:1.5（计划≥3）的比例"
                      "进入临床技能考核，并实行一票否决制。调剂考生按≤1:5 比例筛选。容量仅 2 人。"
                      "科研院所的优势是导师资源集中、临床与科研并重；劣势是招生极少、录取偶然性高。适合科研意向明确、且分数在 320 以上的考生。",
    "石河子大学": "211 + B 区，容量仅 3 人。麻醉科是新疆生产建设兵团的临床重点专科与兵团麻醉专业质控中心主委单位，"
               "近五年承担国家自然科学基金 5 项、发表 SCI 论文 30 余篇，曾获复旦专科声誉排行榜西北地区提名。"
               "2025 年复试线 290，检索建议目标总分 310 以上。学科底子不差，但 3 人容量是硬伤，不建议作为唯一目标。",
    "滨州医学院": "山东省属，18 人容量、均分 318、最低 295、带宽 23 分。山东省内分数梯队下段，"
               "容量中等、门槛低。适合山东考生作为兜底选择，需评估滨州与烟台两地院区的培养条件差异。",
    "右江民族医学院": "广西 B 区，10 人容量、均分 316。面向桂西及少数民族地区医疗人才培养，"
                  "B 区国线叠加 316 的均分，门槛在保底档中很低。适合广西考生或有意向西部地区基层医疗的考生。",
    "陕西中医药大学": "陕西省属，容量仅 2 人、均分 308，是本表门槛最低的院校。中西医结合背景，"
                  "麻醉学方向偏疼痛诊疗与中西医结合麻醉。2 人的容量意味着数据与结果都高度偶然，仅作信息参考。",
}

# ---------------------------------------------------------------- 计算
def in_scope(x):
    if x.get("lo") and x["lo"] <= 350:
        return True
    if not x.get("lo") and x.get("avg") and x["avg"] <= 350:
        return True
    return False


def tier_of(avg):
    if avg >= 358:
        return 1
    if avg >= 348:
        return 2
    if avg >= 340:
        return 3
    return 4


def build_rows():
    d = json.load(open(DATA, encoding="utf-8"))
    rows = []
    for x in d:
        if not in_scope(x):
            continue
        avg = x.get("avg") or 0
        lo = x.get("lo")
        band = (avg - lo) if (lo and avg) else None
        rows.append({
            "name": x["name"],
            "region": x["region"],
            "city": x.get("city") or "",
            "level": x["level"],
            "lo": lo,
            "avg": x.get("avg"),
            "band": band,
            "n": x.get("n"),
            "fy": x.get("fy") or "",
            "basis": x.get("basis") or "",
            "tier": tier_of(avg),
            "note": NOTES.get(x["name"], ""),
            "hist": x.get("hist") or {},
            "units": x.get("hist_units") or [],
            "verdict": x.get("verdict"),
            "reason": x.get("verdict_reason") or "",
            "sources": x.get("sources") or [],
        })
    rows.sort(key=lambda r: (-(r["avg"] or 0), r["name"]))
    return rows


STYLE = """
  :root {
    color-scheme: light;
    --paper: oklch(96% 0.018 83);
    --paper-deep: oklch(91% 0.026 81);
    --card: oklch(98.5% 0.008 83);
    --ink: oklch(27% 0.045 242);
    --ink-soft: oklch(43% 0.035 242);
    --ink-faint: oklch(58% 0.022 242);
    --navy: oklch(29% 0.065 242);
    --navy-deep: oklch(21% 0.05 242);
    --line: oklch(78% 0.025 82);
    --accent: oklch(58% 0.17 31);
    --focus: oklch(63% 0.16 245);
    --t1: oklch(58% 0.17 31);
    --t2: oklch(60% 0.13 63);
    --t3: oklch(52% 0.09 152);
    --t4: oklch(52% 0.09 240);
  }
  * { box-sizing: border-box; }
  html { background: var(--navy-deep); scroll-behavior: smooth; }
  body {
    margin: 0; min-height: 100vh; color: var(--ink);
    background: linear-gradient(90deg, transparent 0 1.45rem, color-mix(in oklch, var(--accent) 22%, transparent) 1.45rem 1.5rem, transparent 1.5rem), var(--paper);
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    line-height: 1.6; padding: 0 0 max(2rem, env(safe-area-inset-bottom));
  }
  a { color: inherit; }
  button, input, select { font: inherit; }
  button, input, select { min-height: 44px; }
  :focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; }
  .masthead {
    position: relative; overflow: hidden; color: oklch(96% 0.018 83);
    background: var(--navy); padding: clamp(2rem, 7vw, 4.5rem) clamp(1.25rem, 6vw, 5rem) clamp(1.75rem, 5vw, 3rem);
    border-bottom: 5px solid var(--accent);
  }
  .masthead::after {
    content: "350"; position: absolute; right: -.02em; bottom: -.42em;
    font-family: Georgia, "Times New Roman", serif; font-size: clamp(7rem, 30vw, 17rem);
    font-weight: 700; line-height: 1; letter-spacing: -.07em;
    color: color-mix(in oklch, var(--paper) 7%, transparent); pointer-events: none;
  }
  .backlink {
    position: relative; z-index: 2; display: inline-flex; align-items: center; gap: .4rem;
    margin: 0 0 1.1rem; padding: .5rem .9rem; border-radius: 999px;
    border: 1px solid color-mix(in oklch, var(--paper) 34%, transparent);
    background: color-mix(in oklch, var(--paper) 12%, transparent);
    color: oklch(94% 0.02 236); font-size: .84rem; font-weight: 600; text-decoration: none;
    transition: background-color .2s ease;
  }
  .backlink:hover { background: color-mix(in oklch, var(--paper) 22%, transparent); }
  .eyebrow { position: relative; z-index: 1; margin: 0 0 .7rem; color: oklch(82% 0.08 70); font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
  h1 { position: relative; z-index: 1; margin: 0; font-family: "Songti SC", "STSong", Georgia, serif; font-size: clamp(1.95rem, 7.5vw, 3.3rem); line-height: 1.05; letter-spacing: -.035em; }
  .dek { position: relative; z-index: 1; max-width: 62ch; margin: 1rem 0 0; color: oklch(88% 0.025 236); font-size: clamp(.93rem, 2.8vw, 1.05rem); }
  main { max-width: 82rem; margin: 0 auto; padding: clamp(1.5rem, 5vw, 3rem) clamp(1rem, 4vw, 3rem) 4rem; }
  h2 { margin: 0 0 .35rem; font-family: "Songti SC", "STSong", Georgia, serif; font-size: clamp(1.35rem, 4vw, 1.8rem); letter-spacing: -.02em; }
  .sec { margin: 0 0 clamp(1.75rem, 5vw, 3rem); }
  .sec-label { margin: 0 0 .5rem; font-size: .76rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-soft); }
  .sec > p.lead { margin: .5rem 0 1.25rem; max-width: 76ch; color: var(--ink-soft); font-size: .96rem; }
  .kpis { display: grid; gap: .75rem; grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr)); margin: 0 0 clamp(1.75rem, 5vw, 2.75rem); }
  .kpi { padding: 1rem 1.05rem; background: var(--card); border: 1px solid var(--line); border-top: 4px solid var(--navy); }
  .kpi b { display: block; font-family: Georgia, serif; font-size: clamp(1.6rem, 5vw, 2.15rem); line-height: 1.05; letter-spacing: -.03em; color: var(--navy); }
  .kpi span { display: block; margin-top: .35rem; font-size: .8rem; color: var(--ink-soft); }
  .grid-cards { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr)); }
  .card { padding: 1.15rem 1.25rem; background: var(--card); border: 1px solid var(--line); }
  .card h3 { margin: 0 0 .45rem; font-size: 1.02rem; }
  .card p { margin: 0; font-size: .9rem; color: var(--ink-soft); }
  .card b { color: var(--ink); }
  .tiercard { border-left: 6px solid var(--navy); }
  .tiercard.t1 { border-left-color: var(--t1); }
  .tiercard.t2 { border-left-color: var(--t2); }
  .tiercard.t3 { border-left-color: var(--t3); }
  .tiercard.t4 { border-left-color: var(--t4); }
  .tiercard .tt { display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap; margin: 0 0 .4rem; }
  .tiercard .tt h3 { margin: 0; font-family: "Songti SC", serif; font-size: 1.14rem; }
  .tiercard .tt em { font-style: normal; font-size: .8rem; color: var(--ink-faint); }
  /* 工具条 */
  .tools { display: grid; gap: .85rem; padding: 1rem 1.1rem; background: var(--paper-deep); border: 1px solid var(--line); margin: 0 0 1rem; }
  .toolrow { display: flex; flex-wrap: wrap; gap: .55rem; align-items: center; }
  .toolrow > .lbl { font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-soft); margin-right: .2rem; }
  .chip {
    padding: .4rem .8rem; border-radius: 999px; border: 1px solid var(--line); background: var(--card);
    color: var(--ink-soft); font-size: .84rem; font-weight: 600; cursor: pointer; transition: all .18s ease;
  }
  .chip:hover { border-color: var(--navy); color: var(--navy); }
  .chip[aria-pressed="true"] { background: var(--navy); border-color: var(--navy); color: oklch(96% 0.018 83); }
  #q { flex: 1 1 12rem; min-width: 10rem; padding: .5rem .8rem; border: 1px solid var(--line); background: var(--card); color: var(--ink); }
  .count { font-size: .84rem; color: var(--ink-soft); }
  .count b { color: var(--navy); font-family: Georgia, serif; font-size: 1.05rem; }
  /* 表格 */
  .tablewrap { overflow-x: auto; border: 1px solid var(--line); background: var(--card); }
  table { width: 100%; border-collapse: collapse; font-size: .88rem; min-width: 46rem; }
  thead th {
    position: sticky; top: 0; z-index: 3; background: var(--navy); color: oklch(95% 0.018 83);
    padding: .6rem .7rem; text-align: left; font-size: .78rem; font-weight: 700; letter-spacing: .04em; white-space: nowrap;
  }
  thead th.sortable { cursor: pointer; user-select: none; }
  thead th.sortable::after { content: " \\2195"; opacity: .38; font-size: .7rem; }
  thead th[data-dir="asc"]::after { content: " \\2191"; opacity: 1; }
  thead th[data-dir="desc"]::after { content: " \\2193"; opacity: 1; }
  tbody td { padding: .55rem .7rem; border-bottom: 1px solid color-mix(in oklch, var(--line) 55%, transparent); vertical-align: top; }
  tbody tr.row { cursor: pointer; }
  tbody tr.row:hover { background: color-mix(in oklch, var(--navy) 6%, transparent); }
  tbody tr.row.open { background: color-mix(in oklch, var(--navy) 9%, transparent); }
  .sch { font-weight: 700; }
  .tag { display: inline-block; padding: .1rem .42rem; border-radius: 3px; font-size: .72rem; font-weight: 700; white-space: nowrap; }
  .tag.t1 { background: color-mix(in oklch, var(--t1) 18%, white); color: oklch(38% 0.15 31); }
  .tag.t2 { background: color-mix(in oklch, var(--t2) 22%, white); color: oklch(38% 0.11 63); }
  .tag.t3 { background: color-mix(in oklch, var(--t3) 18%, white); color: oklch(33% 0.08 152); }
  .tag.t4 { background: color-mix(in oklch, var(--t4) 16%, white); color: oklch(33% 0.08 240); }
  .tag.lv { background: var(--paper-deep); color: var(--ink-soft); }
  .num { font-family: Georgia, "Times New Roman", serif; font-variant-numeric: tabular-nums; }
  .num.hi { color: var(--t1); font-weight: 700; }
  .band-cell { display: flex; align-items: center; gap: .45rem; }
  .bar { height: .45rem; border-radius: 999px; background: color-mix(in oklch, var(--navy) 16%, transparent); min-width: 2px; }
  .bar.b-hi { background: oklch(58% 0.17 31); }
  .bar.b-md { background: oklch(70% 0.13 63); }
  .bar.b-lo { background: oklch(62% 0.09 152); }
  tr.detail td { background: color-mix(in oklch, var(--navy) 5%, transparent); padding: 0 .7rem 1rem; border-bottom: 1px solid var(--line); }
  tr.detail .note { max-width: 84ch; font-size: .89rem; color: var(--ink); }
  tr.detail .basis { display: block; margin-top: .6rem; font-size: .8rem; color: var(--ink-soft); }
  tr.detail .basis b { color: var(--ink); }
  .empty { padding: 1.5rem; text-align: center; color: var(--ink-soft); font-size: .9rem; }
  .note-legend { display: flex; gap: 1rem; flex-wrap: wrap; margin: .75rem 0 0; font-size: .8rem; color: var(--ink-soft); }
  footer { max-width: 82rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 3rem; color: var(--ink-soft); font-size: .84rem; }
  footer a { color: var(--navy); }
  @media (max-width: 640px) {
    .tools { padding: .8rem; }
    .kpi { padding: .85rem; }
    thead th, tbody td { padding: .5rem .5rem; font-size: .82rem; }
  }
  @media print {
    body { background: #fff; }
    .tools { display: none; }
    tbody tr.detail { display: table-row !important; }
  }
"""

# 策略页补充样式
STRATEGY_EXTRA = """
  .plan { border: 1px solid var(--line); background: var(--card); margin: 0 0 1rem; }
  .plan header { padding: .85rem 1.15rem; background: var(--navy); color: oklch(96% 0.018 83); display: flex; flex-wrap: wrap; gap: .6rem; align-items: baseline; }
  .plan header h3 { margin: 0; font-family: "Songti SC", serif; font-size: 1.12rem; }
  .plan header em { font-style: normal; font-size: .8rem; color: oklch(85% 0.03 236); }
  .plan .body { padding: 1rem 1.15rem; }
  .plan .body p { margin: 0 0 .8rem; font-size: .9rem; color: var(--ink-soft); }
  .plan .body p:last-child { margin-bottom: 0; }
  .slot { display: grid; gap: .6rem; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); }
  .slot div { padding: .7rem .8rem; border: 1px dashed var(--line); background: var(--paper); font-size: .86rem; }
  .slot div b { display: block; font-size: .74rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-faint); margin-bottom: .25rem; }
  .checklist { list-style: none; margin: 0; padding: 0; }
  .checklist li { padding: .7rem 0; border-bottom: 1px solid color-mix(in oklch, var(--line) 60%, transparent); font-size: .9rem; }
  .checklist li:last-child { border-bottom: 0; }
  .checklist b { display: block; color: var(--ink); }
  .checklist span { color: var(--ink-soft); }
  .timeline { list-style: none; margin: 0; padding: 0 0 0 1.1rem; border-left: 3px solid var(--line); }
  .timeline li { position: relative; padding: 0 0 1.1rem 1rem; font-size: .9rem; }
  .timeline li::before { content: ""; position: absolute; left: -1.55rem; top: .42rem; width: .68rem; height: .68rem; border-radius: 50%; background: var(--accent); }
  .timeline b { display: block; color: var(--ink); }
  .timeline span { color: var(--ink-soft); }
  .warn { padding: 1rem 1.15rem; border-left: 6px solid var(--accent); background: color-mix(in oklch, var(--accent) 9%, var(--card)); font-size: .9rem; }
  .warn b { color: var(--ink); }
  /* —— 核对后 · 近三年录取 —— */
  .hist { margin-top: .85rem; padding: .78rem .9rem; border: 1px solid color-mix(in oklch, var(--navy) 26%, transparent); background: color-mix(in oklch, var(--paper) 45%, #fff); }
  .hist-head { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; margin: 0 0 .45rem; }
  .hist-head strong { font-size: .78rem; letter-spacing: .06em; color: var(--navy); }
  .vb { display: inline-block; padding: .05rem .5rem; border-radius: 999px; color: #fff; font-size: .7rem; font-weight: 700; white-space: nowrap; }
  .vb.v-修正 { background: oklch(52% 0.19 27); }
  .vb.v-补充 { background: oklch(52% 0.14 250); }
  .vb.v-确认 { background: oklch(50% 0.11 150); }
  .vb.v-无法核实 { background: oklch(60% 0.02 260); }
  .hyear { display: grid; grid-template-columns: 3.5rem minmax(0, 1fr); gap: .05rem .5rem; padding: .38rem 0; border-top: 1px dashed color-mix(in oklch, var(--ink) 16%, transparent); }
  .hyear .hy { grid-row: 1 / span 2; font-weight: 700; font-size: .84rem; font-variant-numeric: tabular-nums; color: var(--navy); }
  .hyear .hy .pick { display: block; font-weight: 400; color: var(--accent); font-size: .62rem; letter-spacing: .04em; }
  .hyear .hm { display: flex; flex-wrap: wrap; gap: .1rem .8rem; font-size: .78rem; }
  .hyear .hm span { white-space: nowrap; color: var(--ink-soft); }
  .hyear .hm b { color: var(--ink); font-variant-numeric: tabular-nums; }
  .hyear .hn { grid-column: 2; font-size: .72rem; color: var(--ink-soft); line-height: 1.45; }
  .hyear.cur { background: color-mix(in oklch, var(--accent) 12%, transparent); }
  .hist .hu, .hist .hr { margin-top: .45rem; font-size: .76rem; color: var(--ink-soft); line-height: 1.55; }
  .hist .hu b { color: var(--navy); }
  .hist .hs { margin-top: .35rem; font-size: .74rem; }
  .hist .hs b { color: var(--navy); }
  .hist .hs a { color: oklch(48% 0.13 250); margin-right: .6rem; }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def build_tier350(rows):
    total = len(rows)
    banded = [r for r in rows if r["band"] is not None]
    big_band = sorted(banded, key=lambda r: -r["band"])[:5]
    big_cap = sorted([r for r in rows if r["n"]], key=lambda r: -r["n"])[:5]
    cnt = {t: len([r for r in rows if r["tier"] == t]) for t in (1, 2, 3, 4)}

    data = [
        {k: r[k] for k in ("name", "region", "city", "level", "lo", "avg", "band", "n", "tier", "note", "basis", "fy", "hist", "units", "verdict", "reason", "sources")}
        for r in rows
    ]

    tier_cards = []
    for t in (1, 2, 3, 4):
        info = TIERS[t]
        tier_cards.append(
            f'<article class="card tiercard t{t}">'
            f'<div class="tt"><h3>{info["name"]}</h3><em>{info["sub"]}</em></div>'
            f'<p>{info["desc"]}</p>'
            f'<p style="margin-top:.6rem"><b>{cnt[t]} 所</b></p>'
            f'</article>'
        )

    ballast = "、".join(f'{r["name"]}（{r["band"]}分）' for r in big_band)
    capacity = "、".join(f'{r["name"]}（{r["n"]}人）' for r in big_cap)

    doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173149">
<title>350 分以下择校分析 · 105118 麻醉学专硕</title>
<style>{STYLE}</style>
</head>
<body>
<header class="masthead">
  <a class="backlink" href="nav.html">&larr; 返回资料导航</a>
  <p class="eyebrow">Score Ceiling 350 &middot; Tiered Selection</p>
  <h1>350 分以下<br>麻醉学专硕择校分析</h1>
  <p class="dek">以「录取最低分 ≤ 350」划出可选范围，再用录取均分、分数带宽与招生容量三个指标，把 {total} 所院校拆成四个阶梯。每一所都有独立点评，不套模板。</p>
</header>

<main>
  <section class="sec">
    <div class="kpis">
      <div class="kpi"><b>{total}</b><span>范围内院校（所）</span></div>
      <div class="kpi"><b>{len([r for r in rows if r["lo"]])}</b><span>有录取最低分数据</span></div>
      <div class="kpi"><b>4</b><span>难度阶梯</span></div>
      <div class="kpi"><b>{sum(r["n"] or 0 for r in rows)}</b><span>范围内录取人数合计</span></div>
    </div>
  </section>

  <section class="sec">
    <p class="sec-label">Method</p>
    <h2>为什么不能只看「最低分」</h2>
    <p class="lead">本项目此前的检索已经确认：临床医学类专业学位（1051）进入复试的成绩要求<b>由招生单位自主确定</b>，
    国家线只是参考。这直接导致各校分数结构差异极大。只看最低分会踩两类坑，所以这里用三个指标交叉判断。</p>
    <div class="grid-cards">
      <article class="card">
        <h3>准入线 &mdash; 录取最低分</h3>
        <p>决定「这所学校有没有 350 分以下上岸的实例」。<b>它是筛选条件，不是目标分。</b></p>
      </article>
      <article class="card">
        <h3>中枢线 &mdash; 录取均分</h3>
        <p>决定「350 分在这所学校大概处于什么位次」。<b>它才是真实竞争强度。</b></p>
      </article>
      <article class="card">
        <h3>容量 &mdash; 录取人数</h3>
        <p>决定「机会是否真实」。3 人以下容量的院校，均分与最低分都带很强偶然性。</p>
      </article>
      <article class="card">
        <h3>带宽 &mdash; 均分减最低分</h3>
        <p><b>本页的核心新增指标。</b>带宽越大，说明录取分越离散：低分窗口可能来自专项计划或扩招末位，复制难度越高。</p>
      </article>
    </div>
    <p class="note-legend">
      <span><b>本页带宽最大的 5 所：</b>{ballast}</span>
      <span><b>容量最大的 5 所：</b>{capacity}</span>
    </p>
  </section>

  <section class="sec">
    <p class="sec-label">Four Tiers</p>
    <h2>四阶梯</h2>
    <p class="lead">阶梯按<b>录取均分</b>划分，而不是按最低分&mdash;&mdash;因为在「最低分 ≤ 350」这个共同前提下，
    真正区分难度的是中枢线的位置。所有四档院校的最低分都在 350 以下，差别在于它们各自有多难。</p>
    <div class="grid-cards">
      {"".join(tier_cards)}
    </div>
  </section>

  <section class="sec">
    <p class="sec-label">Explorer</p>
    <h2>逐校查询</h2>
    <p class="lead">点击任意一行展开该校的独立点评与数据依据。支持按院校名、省份或城市搜索、按阶梯与层次筛选、按列排序。</p>

    <div class="tools">
      <div class="toolrow">
        <input id="q" type="search" placeholder="搜索院校名称或地区，如「浙江」「医科大学」" aria-label="搜索院校">
        <span class="count" id="count"></span>
      </div>
      <div class="toolrow" id="tierChips">
        <span class="lbl">阶梯</span>
        <button class="chip" data-filter="tier" data-val="" aria-pressed="true">全部</button>
        <button class="chip" data-filter="tier" data-val="1" aria-pressed="false">阶梯一 窗口档</button>
        <button class="chip" data-filter="tier" data-val="2" aria-pressed="false">阶梯二 匹配档</button>
        <button class="chip" data-filter="tier" data-val="3" aria-pressed="false">阶梯三 稳健档</button>
        <button class="chip" data-filter="tier" data-val="4" aria-pressed="false">阶梯四 保底档</button>
      </div>
      <div class="toolrow" id="lvChips">
        <span class="lbl">层次</span>
        <button class="chip" data-filter="lv" data-val="" aria-pressed="true">全部</button>
        <button class="chip" data-filter="lv" data-val="985" aria-pressed="false">985</button>
        <button class="chip" data-filter="lv" data-val="211" aria-pressed="false">211 / 双一流</button>
        <button class="chip" data-filter="lv" data-val="B" aria-pressed="false">B 区院校</button>
        <button class="chip" data-filter="lv" data-val="big" aria-pressed="false">容量 ≥ 30 人</button>
      </div>
    </div>

    <div class="tablewrap">
      <table id="tbl">
        <thead>
          <tr>
            <th class="sortable" data-key="name">院校</th>
            <th class="sortable" data-key="city">地区 / 城市 / 层次</th>
            <th class="sortable" data-key="lo">录取最低分</th>
            <th class="sortable" data-key="avg">录取均分</th>
            <th class="sortable" data-key="band">分数带宽</th>
            <th class="sortable" data-key="n">录取人数</th>
            <th>阶梯</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="empty" id="empty" hidden>没有符合条件的院校，试试放宽筛选。</div>
  </section>

  <section class="sec">
    <p class="sec-label">Limits</p>
    <h2>这份分析不能替你做的事</h2>
    <div class="grid-cards">
      <article class="card">
        <h3>数据缺口</h3>
        <p>94 所院校中有 33 所本项目未采集到最低分，其中 12 所的均分 ≤ 350 已被纳入本页；仍有新乡医学院、
        广西医科大学、郑州大学、中山大学、徐州医科大学等<b>因缺分或均分高于 350 而未进入范围</b>&mdash;&mdash;这不代表它们不在 350 分可及区间，只是缺数据。</p>
      </article>
      <article class="card">
        <h3>统计口径不一</h3>
        <p>各校「录取人数」的统计范围不同：有的含推免、有的不含，有的是全院口径、有的是单一培养单位。
        与目标院校的招生目录交叉核对是必要的。</p>
      </article>
      <article class="card">
        <h3>年份会变</h3>
        <p>本页数据主要来自 2025 与 2026 年。医学院校招生计划年际波动很大&mdash;&mdash;内蒙古医科大学的
        第一临床医学院四年间从 9 人到 14 人再到 5 人。务必以报考当年的招生目录为准。</p>
      </article>
      <article class="card">
        <h3>上线不等于录取</h3>
        <p>均分反映的是<b>已被录取者</b>的分数。复试权重高、差额比例大的院校（如按 1:2 差额复试的广东医科大学），
        实际淘汰率远高于分数表面所示。</p>
      </article>
    </div>
  </section>
</main>

<footer>
  <p>数据来自各院校研究生院公开发布的招生目录、复试细则与拟录取名单，经本项目逐条整理。
  本页仅作择校参考，最终以目标院校当年官方公告为准。</p>
  <p><a href="nav.html">返回资料导航</a> &middot; <a href="tier350-strategy.html">报考组合与实操策略</a> &middot; <a href="sources.html">数据来源与口径</a></p>
</footer>

<script>
const ROWS = {json.dumps(data, ensure_ascii=False)};
const TIER_NAME = {{1:"阶梯一 窗口档",2:"阶梯二 匹配档",3:"阶梯三 稳健档",4:"阶梯四 保底档"}};
const state = {{ tier:"", lv:"", q:"", key:"avg", dir:"desc" }};

function isB(r) {{ return r.region && ["内蒙古","广西","海南","贵州","云南","西藏","甘肃","青海","宁夏","新疆"].includes(r.region); }}
function is985(r) {{ return r.level.includes("985"); }}
function is211(r) {{ return r.level.includes("211") || r.level.includes("双一流"); }}

function match(r) {{
  if (state.tier && String(r.tier) !== state.tier) return false;
  if (state.lv === "985" && !is985(r)) return false;
  if (state.lv === "211" && !is211(r)) return false;
  if (state.lv === "B" && !isB(r)) return false;
  if (state.lv === "big" && !(r.n >= 30)) return false;
  if (state.q) {{
    const k = state.q.trim();
    if (!(r.name.includes(k) || r.region.includes(k) || r.city.includes(k))) return false;
  }}
  return true;
}}

function bandClass(b) {{ if (b === null) return ""; if (b >= 40) return "b-hi"; if (b >= 25) return "b-md"; return "b-lo"; }}
function dash(v) {{ return (v === null || v === undefined) ? "—" : v; }}

function histHtml(r) {{
  const h = r.hist || {{}};
  let out = "";
  ["2024","2025","2026"].forEach(y => {{
    const yv = h[y] || {{}};
    const fs = (yv.fs === null || yv.fs === undefined) ? "—" : (yv.fs + (yv.fs_kind && yv.fs_kind !== "未公布" ? "（" + yv.fs_kind + "）" : ""));
    out += '<div class="hyear' + (r.fy === y ? " cur" : "") + '">'
      + '<div class="hy">' + y + (r.fy === y ? '<span class="pick">采用</span>' : "") + '</div>'
      + '<div class="hm">'
      + '<span>最低 <b>' + dash(yv.lo) + '</b></span>'
      + '<span>均分 <b>' + dash(yv.avg) + '</b></span>'
      + '<span>人数 <b>' + dash(yv.n) + '</b></span>'
      + '<span>复试线 <b>' + fs + '</b></span>'
      + '</div>'
      + (yv.note ? '<div class="hn">' + yv.note + '</div>' : "")
      + '</div>';
  }});
  let u = "";
  if (r.units && r.units.length) {{
    u = '<div class="hu"><b>分培养单位：</b>' + r.units.map(x => x.year + " " + x.unit + "：最低 " + dash(x.lo) + " / 均分 " + dash(x.avg) + " / " + dash(x.n) + " 人").join("<br>") + '</div>';
  }}
  const reason = r.reason ? '<div class="hr">核对说明：' + r.reason + '</div>' : "";
  let src = "";
  if (r.sources && r.sources.length) {{
    src = '<div class="hs"><b>来源：</b>' + r.sources.slice(0,5).map(s => '<a href="' + s.url + '" target="_blank" rel="noopener">' + (s.year ? s.year + " " : "") + (s.kind || "链接") + '</a>').join("") + '</div>';
  }}
  const vb = r.verdict ? '<span class="vb v-' + r.verdict + '">' + r.verdict + '</span>' : "";
  return '<div class="hist"><div class="hist-head"><strong>核对后 · 近三年录取（2024—2026）</strong>' + vb + '</div>' + out + u + reason + src + '</div>';
}}

function render() {{
  const rows = ROWS.filter(match).slice();
  const k = state.key, mul = state.dir === "asc" ? 1 : -1;
  rows.sort((a, b) => {{
    let va = a[k], vb = b[k];
    if (k === "name") {{ return mul * a.name.localeCompare(b.name, "zh-Hans-CN"); }}
    if (k === "city") {{ return mul * (a.city || a.region).localeCompare(b.city || b.region, "zh-Hans-CN") || a.name.localeCompare(b.name, "zh-Hans-CN"); }}
    va = (va === null || va === undefined) ? -Infinity : va;
    vb = (vb === null || vb === undefined) ? -Infinity : vb;
    if (va === vb) return a.avg === b.avg ? a.name.localeCompare(b.name, "zh-Hans-CN") : b.avg - a.avg;
    return mul * (va - vb);
  }});

  document.getElementById("count").innerHTML = "共 <b>" + rows.length + "</b> 所匹配";

  const tb = document.getElementById("tbody");
  tb.innerHTML = "";
  const maxBand = Math.max(1, ...ROWS.map(r => r.band || 0));

  rows.forEach((r, idx) => {{
    const tr = document.createElement("tr");
    tr.className = "row";
    const bw = r.band === null ? 0 : Math.max(3, Math.round(r.band / maxBand * 74));
    tr.innerHTML =
      '<td class="sch">' + r.name + '</td>' +
      '<td>' + r.region + (r.city && r.city !== r.region ? ' · ' + r.city : '') + ' <span class="tag lv">' + r.level + '</span></td>' +
      '<td class="num' + (r.lo && r.lo <= 300 ? ' hi' : '') + '">' + dash(r.lo) + '</td>' +
      '<td class="num">' + dash(r.avg) + '</td>' +
      '<td><span class="band-cell"><span class="bar ' + bandClass(r.band) + '" style="width:' + bw + 'px"></span><span class="num">' + dash(r.band) + '</span></span></td>' +
      '<td class="num">' + dash(r.n) + '</td>' +
      '<td><span class="tag t' + r.tier + '">' + TIER_NAME[r.tier] + '</span></td>';

    const dr = document.createElement("tr");
    dr.className = "detail";
    dr.hidden = true;
    dr.innerHTML = '<td colspan="7"><div class="note">' + (r.note || "暂无点评。") + '</div>' +
      (r.basis ? '<span class="basis"><b>数据依据：</b>' + r.basis + '</span>' : '') +
      histHtml(r) + '</td>';

    tr.addEventListener("click", () => {{
      const open = !dr.hidden;
      dr.hidden = open;
      tr.classList.toggle("open", !open);
    }});
    tb.appendChild(tr);
    tb.appendChild(dr);
  }});

  document.getElementById("empty").hidden = rows.length > 0;
}}

document.querySelectorAll(".chip").forEach(c => {{
  c.addEventListener("click", () => {{
    const f = c.dataset.filter, v = c.dataset.val;
    document.querySelectorAll('.chip[data-filter="' + f + '"]').forEach(o => o.setAttribute("aria-pressed", "false"));
    c.setAttribute("aria-pressed", "true");
    state[f] = v;
    render();
  }});
}});

document.getElementById("q").addEventListener("input", e => {{ state.q = e.target.value; render(); }});

document.querySelectorAll("th.sortable").forEach(th => {{
  th.addEventListener("click", () => {{
    const k = th.dataset.key;
    if (state.key === k) {{ state.dir = state.dir === "asc" ? "desc" : "asc"; }}
    else {{ state.key = k; state.dir = (k === "name") ? "asc" : "desc"; }}
    document.querySelectorAll("th.sortable").forEach(o => o.removeAttribute("data-dir"));
    th.setAttribute("data-dir", state.dir);
    render();
  }});
}});

render();
</script>
</body>
</html>
"""
    (DOCS / "tier350.html").write_text(doc, encoding="utf-8")
    return DOCS / "tier350.html"


def build_strategy():
    doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173149">
<title>报考组合与实操策略 · 350 分以下麻醉学专硕</title>
<style>{STYLE}{STRATEGY_EXTRA}</style>
</head>
<body>
<header class="masthead">
  <a class="backlink" href="tier350.html">&larr; 返回 350 分全景分析</a>
  <p class="eyebrow">Portfolio &middot; Operational Playbook</p>
  <h1>报考组合<br>与实操策略</h1>
  <p class="dek">选校不是选一所，是配一套。这一页给出三套可直接照抄的组合方案，以及复试阶段真正会决定成败的核查清单。</p>
</header>

<main>
  <section class="sec">
    <p class="sec-label">Premise</p>
    <h2>先确认三件事，再谈选校</h2>
    <div class="warn">
      <p style="margin:0 0 .7rem"><b>一、国家线对你几乎没有约束力。</b>教育部 2026 年国家线文件写明：报考临床医学类专业学位（1051）
      考生进入复试的初试成绩要求，<b>由招生单位自主确定并公布</b>。医学门类 A 区线 294、B 区 284 只是参考，
      也是「临床专硕调剂到其他专业」的基本要求。所以别再问「过国家线能不能上」&mdash;&mdash;要问「这所学校自己划到哪」。</p>
      <p style="margin:0 0 .7rem"><b>二、B 区红利只值 10 分，而且常被抢掉。</b>B 区国家线比 A 区低 10 分（284 vs 294）。
      但海南医科大学均分 353、贵州医科大学均分 349，都远高于 B 区线&mdash;&mdash;B 区里交通与政策较好的院校，
      红利已经被生源填平。真正吃到 B 区红利的是新疆、内蒙古、宁夏、青海、西藏这一类。</p>
      <p style="margin:0"><b>三、容量比分数线更值得优先看。</b>3 人容量的院校（厦门大学、石河子大学、西藏大学、
      广东省心血管病研究所），最低分与均分都不具备统计意义。相反，新疆医科大学 62 人、南昌大学 61 人、
      大连医科大学 48 人、温州医科大学 47 人、安徽医科大学 47 人这一类，分数结构的可预测性高得多。</p>
    </div>
  </section>

  <section class="sec">
    <p class="sec-label">Portfolios</p>
    <h2>三套组合方案</h2>
    <p class="lead">以下为「冲 &mdash; 稳 &mdash; 保」三档组合示例。之所以要配三档，是因为医学专硕招生计划年际波动极大，
    单一目标一旦缩招就没有退路。请按自己的估分与地域意愿调整。</p>

    <article class="plan">
      <header><h3>方案 A &middot; 平台优先</h3><em>适合估分 350&mdash;360，愿意为学历层次承担风险</em></header>
      <div class="body">
        <p>核心思路：用「985/211 里的低分窗口」博一次平台跃迁，同时用容量充足的 211 兜住底线。</p>
        <div class="slot">
          <div><b>冲刺</b>武汉大学（985，均分 352，19 人）<br>或 兰州大学（985，均分 354，16 人）</div>
          <div><b>稳妥</b>南昌大学（211，均分 359，61 人）<br>或 苏州大学（211，均分 356，13 人）</div>
          <div><b>保底</b>延边大学（211，均分 336，37 人）<br>或 江南大学（211，均分 337，9 人）</div>
        </div>
        <p style="margin-top:.9rem">这条线之所以成立：武大与兰大是本表里唯一两所「985 且录取均分落在 350 出头」的院校，
        比华中科技大学（362）低了 10 分左右，容量还更大。保底端的延边大学同时具备 211、37 人容量、336 均分，
        并且接受日语考生&mdash;&mdash;在整个 350 分以下区间里没有第二所。</p>
      </div>
    </article>

    <article class="plan">
      <header><h3>方案 B &middot; 容量优先</h3><em>适合估分 335&mdash;350，追求确定性</em></header>
      <div class="body">
        <p>核心思路：放弃校名，把预算全部押在「招生体量大、分数结构稳定」的院校上。大容量意味着复试与分数都更可预测。</p>
        <div class="slot">
          <div><b>冲刺</b>哈尔滨医科大学（均分 363，46 人）<br>或 中国医科大学（均分 363，42 人，扩招中）</div>
          <div><b>稳妥</b>大连医科大学（均分 340，48 人）<br>或 昆明医科大学（均分 349，42 人，B 区）</div>
          <div><b>保底</b>新疆医科大学（均分 324，62 人，B 区）<br>或 锦州医科大学（均分 332，42 人）</div>
        </div>
        <p style="margin-top:.9rem">中国医科大学与河北医科大学是本表里扩招最明确的两所（河北医科大 2026 年专硕计划
        较上年翻倍至 45 人）。扩招年份往往是分数线相对友好的年份&mdash;&mdash;但要注意中国医科大 2026 年复试线虽有 305，
        单科线却是 45/170，单科短板会直接被卡。</p>
      </div>
    </article>

    <article class="plan">
      <header><h3>方案 C &middot; 上岸优先</h3><em>适合估分 320&mdash;340，或以二战求稳为核心目标</em></header>
      <div class="body">
        <p>核心思路：以「过线即有较大机会」为标准，优先 B 区与省属大容量院校，把不确定性压到最低。</p>
        <div class="slot">
          <div><b>冲刺</b>安徽医科大学（均分 360，47 人）<br>或 河北医科大学（均分 362，44 人，扩招）</div>
          <div><b>稳妥</b>宁夏医科大学（均分 342，20 人，B 区）<br>或 内蒙古医科大学（均分 335，43 人，B 区）</div>
          <div><b>保底</b>新疆医科大学（均分 324，62 人，B 区）<br>或 皖南医学院（均分 335，42 人）</div>
        </div>
        <p style="margin-top:.9rem">新疆医科大学公开的 2026 年数据值得单独看：全校录取初试分中位数 319、
        一志愿均分 320.59、调剂均分 316.37，复试淘汰率约 16.2%。<b>一志愿均分高于调剂均分</b>&mdash;&mdash;
        这说明该校并不歧视一志愿，反而是调剂进来要更难。对求稳考生这是很重要的信号。</p>
      </div>
    </article>
  </section>

  <section class="sec">
    <p class="sec-label">Rules</p>
    <h2>复试规则：真正决定成败的四项</h2>
    <p class="lead">初试线只是入场券。以下四项在检索到的 2026 年公开复试办法里都能查到原文，建议逐项核实目标院校。</p>
    <ul class="checklist">
      <li>
        <b>差额复试比例</b>
        <span>广东医科大学 2026 年办法明确：临床医学专业学位按 <b>1:2</b> 差额复试，其他学科 1:1.5&mdash;&mdash;临床专硕的淘汰率是全学科里最高的。
        南方医科大学与广东省心血管病研究所则按计划数分级：计划 =1 时 1:3、=2 时 1:2、≥3 时 1:1.5。比例越高，低分考生越危险。</span>
      </li>
      <li>
        <b>临床技能考核是否「一票否决」</b>
        <span>南方医科大学 2026 年办法写明：临床技能考核成绩排序在报考分委员会<b>最后 10%</b> 的考生为不合格，
        不得参加后续复试内容考核。广东省心血管病研究所同样实行一票否决制。这类院校里，初试高分不等于安全。</span>
      </li>
      <li>
        <b>单科线，而不只是总分线</b>
        <span>中国医科大学 2026 年临床医学（1051）复试线为总分 305，但单科线是 <b>45 / 170</b>。
        广东省心血管病研究所专硕线为总分 310，单科 45 / 45 / 160。总分过线而单科卡住，是每年都在发生的翻车方式。</span>
      </li>
      <li>
        <b>培养单位差异</b>
        <span>同一所学校的不同附属医院分数可能差出 30 分以上。检索到安徽医科大学安庆医学中心等合作附属单位录取均分
        只有 300 出头，而本部竞争激烈；贵州医科大学麻醉学院的疼痛方向均分 338，低于麻醉方向。报名时务必确认到具体培养单位与方向。</span>
      </li>
    </ul>
  </section>

  <section class="sec">
    <p class="sec-label">Special Channels</p>
    <h2>三条容易被忽略的通道</h2>
    <div class="grid-cards">
      <article class="card">
        <h3>专项计划：低分「异常值」的真正来源</h3>
        <p>本表里那些远低于均分的最低分（浙江大学 328、温州医科大学 295、内蒙古医科大学 285、新疆医科大学 283），
        相当一部分来自<b>少数民族高层次骨干人才计划</b>与<b>退役大学生士兵计划</b>。
        以北京大学医学部 2026 年为例：少骨计划总分比相同研究方向普通考生实际复试线<b>下调 10 分</b>，士兵计划则与普通线一致。
        若你没有专项资格，这些最低分对你不构成参考。</p>
      </article>
      <article class="card">
        <h3>调剂：一志愿缺额的信号价值</h3>
        <p>调剂系统 4 月 8 日开通。检索到的 2026 年医学调剂信息显示，麻醉学在宁夏医科大学（3 人）、
        广州医科大学、中国医科大学、南京医科大学、苏州大学、江苏大学、中山大学、中南大学湘雅等校均有名额。
        <b>但调剂名额的存在有两面性</b>：既说明有缺口，也可能说明该校偏向调剂生源。报考前应查清一志愿与调剂是否同批次复试。</p>
      </article>
      <article class="card">
        <h3>科研院所与军队院校</h3>
        <p>广东省心血管病研究所是本表唯一科研院所：专硕复试线 310、临床技能考核一票否决、调剂按 ≤1:5 筛选，
        优势是导师资源集中。军队院校（海军军医大学 2025 年最低 353、陆军军医大学 363）分数高于 350 未进入本表范围，
        但报考需注意政治审查、体检与军籍要求，规则与地方院校完全不同。</p>
      </article>
    </div>
  </section>

  <section class="sec">
    <p class="sec-label">Job Market</p>
    <h2>岗位端验证：硕士学历是不是必须</h2>
    <p class="lead">不引用「人才缺口多少万」这类无法溯源的数字，直接看 2026 年实际招聘公告的硬条件。</p>
    <div class="grid-cards">
      <article class="card">
        <h3>三甲医院普遍要求硕士及以上</h3>
        <p>四川大学华西第二医院 2026 年麻醉科医师岗：学历要求<b>硕士研究生及以上</b>，须持医师资格证与规培合格证，有三甲经验优先。
        北京积水潭医院贵州医院麻醉科医师岗：硕士及以上，须医师资格证、规培合格证（麻醉科）、CET-4 ≥ 425。
        湖南湘潭市第一人民医院（三甲）麻醉科医师岗：研究生学历，本科专业须为临床医学或麻醉学。</p>
      </article>
      <article class="card">
        <h3>规培阶段的待遇可查</h3>
        <p>上海市第一人民医院麻醉科 2026 年规培招聘：要求硕士及以上、CET6 ≥ 440、以一作发表 SCI 优先；
        待遇为科室额外绩效补助约 5000 元/月、住房补贴 2000 元/月，优秀住院医师津贴 A 类 5500 元/月。
        这是可溯源的官方公告口径，比二手薪资传闻可靠。</p>
      </article>
      <article class="card">
        <h3>本科层的现实</h3>
        <p>麻醉学本科（100202TK）全国就业率约 85%&mdash;90%，毕业起薪约 6829 元，毕业 5 年约 10664 元。
        这与「98.5% 就业率」的说法差距明显。结论是：本科能进入医疗体系，但<b>要进入三甲或省会医院，硕士基本是硬门槛</b>&mdash;&mdash;
        这正是 105118 值得投入三年的原因。</p>
      </article>
      <article class="card">
        <h3>地域黏性高于校名</h3>
        <p>规培资源、导师人脉、同门网络基本扎在就读城市。招聘公告里的地域偏好也很直白&mdash;&mdash;
        北京积水潭医院贵州医院招的是贵州岗位，湘潭市第一人民医院招的是湖南岗位。
        <b>如果就业城市已经确定，优先选当地认可度最高的医学院，而不是跨省冲一个名字更响的学校。</b></p>
      </article>
    </div>
  </section>

  <section class="sec">
    <p class="sec-label">Timeline</p>
    <h2>接下来一年要做的事</h2>
    <ul class="timeline">
      <li><b>现在 &mdash; 9 月：定范围，不锁定单校</b><span>用本页的四个阶梯圈出 6&mdash;9 所目标，覆盖冲/稳/保三档。此时只做粗筛，不投入任何针对性复习。</span></li>
      <li><b>9 月：招生目录发布，逐所复核</b><span>这是全年最关键的一次核对。看三件事：招生计划是否缩招、推免占比是否提高、报考条件是否新增限制。任何一项变差就立刻启用备选。</span></li>
      <li><b>10 月：报名，敲定到培养单位</b><span>医学专硕的报名单位要精确到附属医院或临床医学院。同一所学校不同培养单位分数可以差 30 分以上。</span></li>
      <li><b>12 月底：初试</b><span>政治 + 英语一 + 306 临床医学综合能力（西医），总分 500。306 占 300 分，是绝对主战场。</span></li>
      <li><b>次年 2 月底&mdash;3 月：出分、国家线、校线</b><span>2026 年国家线于 2 月 28 日公布，考生成绩同期可查。此时立刻核对目标院校的自划线，并重估三档组合。</span></li>
      <li><b>3 月底：一志愿复试</b><span>多数院校要求在 4 月 7 日前完成一志愿复试录取。差额比例、技能考核权重、是否一票否决，都要在此前查清。</span></li>
      <li><b>4 月 8 日：调剂系统开通</b><span>调剂意向采集 3 月 27 日开通。三个平行志愿按冲/稳/保搭配填报，不要全填同一层次。</span></li>
    </ul>
  </section>
</main>

<footer>
  <p>规则类信息均来自各院校 2026 年公开发布的招生简章、复试录取办法与研招网公示文件；院校分数数据来自本项目整理。
  本页仅作决策参考，最终以目标院校当年官方公告为准。</p>
  <p><a href="tier350.html">350 分全景分析</a> &middot; <a href="nav.html">返回资料导航</a> &middot; <a href="glossary.html">概念与术语</a></p>
</footer>
</body>
</html>
"""
    (DOCS / "tier350-strategy.html").write_text(doc, encoding="utf-8")
    return DOCS / "tier350-strategy.html"


if __name__ == "__main__":
    rows = build_rows()
    p1 = build_tier350(rows)
    p2 = build_strategy()
    print(f"范围内院校 {len(rows)} 所")
    for t in (1, 2, 3, 4):
        g = [r for r in rows if r["tier"] == t]
        print(f"  阶梯{t}: {len(g):>2} 所   " + "、".join(r["name"] for r in g[:4]) + ("…" if len(g) > 4 else ""))
    missing = [r["name"] for r in rows if not r["note"]]
    print("缺点评:", missing if missing else "无")
    print("已生成:", p1.name, p2.name)
