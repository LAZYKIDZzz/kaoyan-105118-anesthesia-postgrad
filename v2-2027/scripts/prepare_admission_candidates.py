import json, pathlib, re
from urllib.parse import urlparse
P=pathlib.Path(__file__).resolve().parents[1]/'research/2026-10-18'
ALIASES={'皖南医学院':'皖南医科大学','绍兴文理学院':'绍兴大学','湖州师范学院':'湖州师范大学','新乡医学院':'河南医药大学','内蒙古科技大学（包头医学院）':'包头医学院','解放军医学院（301）':'解放军医学院','滨州医学院':'山东医药大学'}
SEEDS={
 '延边大学':['https://grad.ybu.edu.cn/zsgz/sszs.htm'],
 '甘肃中医药大学':['https://yjsc.gszy.edu.cn/'],
 '内蒙古医科大学':['https://yjsxy.immu.edu.cn/'],
 '华北理工大学':['https://yjsxy.ncst.edu.cn/'],
 '武汉科技大学':['https://ysxy.wust.edu.cn/info/1831/50612.htm','https://ysxy.wust.edu.cn/zsgz/tzgg.htm'],
 '绍兴文理学院':['https://yjsc.usx.edu.cn/yzw/sy.htm'],
 '川北医学院':['https://www.nsmc.edu.cn/dwyjsgzb/info/1322/68888.htm','https://www.nsmc.edu.cn/dwyjsgzb/'],
 '温州医科大学':['https://yjszs.wmu.edu.cn/yzbm/zsml/sszsml/index/2027','https://yjsy.wmu.edu.cn/'],
 '徐州医科大学':['https://yjs.xzhmu.edu.cn/zs/sszs.htm'],
 '陕西中医药大学':['https://yzb.sntcm.edu.cn/'],
 '汕头大学':['https://www.gs.stu.edu.cn/Open/RecruitTkss/ZsDir_View.aspx','https://gs.stu.edu.cn/yjszs/master_zsjz.htm'],
 '扬州大学':['https://yjsc.yzu.edu.cn/'],
 '江苏大学':['https://yz.ujs.edu.cn/zsjzml/sszsjzml.htm'],
 '福建医科大学':['https://yjsy.fjmu.edu.cn/'],
 '滨州医学院':['https://yjszs.sdmpu.edu.cn/2056/list.htm'],
 '解放军医学院（301）':['https://yz.chsi.com.cn/sch/viewZszc--infoId-25318117%2CcategoryId-10462685%2CschId-367823%2Cmindex-12.dhtml'],
 '山东第一医科大学':['https://yz.sdfmu.edu.cn/sszs1/zyml.htm'],
 '遵义医科大学':['https://grs.zmu.edu.cn/'],
 '浙江中医药大学':['https://yjsgl.zcmu.edu.cn/show/6007','https://yjsgl.zcmu.edu.cn/'],
 '宁夏医科大学':['https://www.nxmu.edu.cn/yjsy/zsgz/ssszs.htm'],
 '华中科技大学':['https://yanzhao.hust.edu.cn/Master/Zsml_View.aspx'],
 '广东省心血管病研究所':['https://yz.chsi.com.cn/sch/viewZszc--infoId-3122169199%2CcategoryId-10462591%2CschId-368406%2Cmindex-12.dhtml'],
 '河南大学':['https://grs.henu.edu.cn/zsgz/sszs.htm'],
 '贵州医科大学':['https://yjsxy.gmc.edu.cn/'],
 '广东医科大学':['https://yjsxy.gdmu.edu.cn/zsgz/sszs.htm'],
 '沈阳医学院':['https://yjsjy.symc.edu.cn/'],
 '大连大学':['https://yjs.dlu.edu.cn/'],
 '山东大学':['https://yz.sdu.edu.cn/sszs/zyml.htm'],
 '成都中医药大学':['https://zyd.cdutcm.edu.cn/yjs/zsgz/sszs/content_142106','https://yjs.cdutcm.edu.cn/'],
 '南昌大学':['https://yjsy.ncu.edu.cn/zsgz/sszs.htm'],
 '兰州大学':['https://yz.lzu.edu.cn/shuoshishengzhaosheng/shuoshijianzhang/2026/1009/338207.html','https://yz.lzu.edu.cn/'],
 '中国医科大学':['https://www.cmu.edu.cn/cmuyjs/'],
 '宁波大学':['https://graduate.nbu.edu.cn/zsgz/ssszs.htm'],
 '湖州师范学院':['https://yjsy.huznu.edu.cn/2026/0930/c1785a256211/page.htm'],
}
items=json.loads((P/'scope.json').read_text())['schools']
for s in items:
    cs=[]
    for f in P.glob('search*.txt'):
        for t,u in re.findall(r'^(.{1,200}?) \((https?://[^\n]+)\)$',f.read_text(),re.M):
            host=urlparse(u).hostname or ''
            if not (host.endswith('edu.cn') or host.endswith(('gmu.cn','mdjmu.cn'))):continue
            if not any(n in t for n in [s['name'],ALIASES.get(s['name'],s['name'])]):continue
            if '2027' not in t or not any(k in t for k in ['目录','章程','简章','指南']):continue
            if any(k in t for k in ['推免','免试','单独考试','非全日制','骨干','MEM','工商管理','人文学院','马克思主义','高水平研究生项目','博士','考试科目调整','自命题变更']):continue
            cs.append({'title':t,'url':u})
    cs.sort(key=lambda x:('目录' not in x['title'],'章程' not in x['title']))
    cs += [{'title':s['name']+'招生官网（查找2027目录）','url':u} for u in SEEDS.get(s['name'],[])]
    s['candidates']=list({x['url']:x for x in cs}.values())[:5]
(P/'candidates.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
print('具有官网检索入口',sum(bool(s['candidates']) for s in items),'/',len(items))
