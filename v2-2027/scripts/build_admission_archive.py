"""Build the dated admissions audit, download index and plan-data supplement."""
import collections,csv,hashlib,html,json,pathlib,re,shutil,zipfile
from urllib.parse import quote
ROOT=pathlib.Path(__file__).resolve().parents[2]
V2=ROOT/'v2-2027';R=V2/'research/2026-10-18';DEST=ROOT/'docs/admissions/2027'
scope=json.loads((R/'scope.json').read_text())['schools']
review=json.loads((R/'reviewed.json').read_text())['schools']
extractions=json.loads((R/'extractions.json').read_text())
by_path={x['path']:x for x in extractions}

def manual_original(name,src,url,title,ext,kind='original'):
    folder=DEST/name;mf=folder/'manifest.json';m=json.loads(mf.read_text())
    b=pathlib.Path(src).read_bytes();file=folder/(title+ext);file.write_bytes(b)
    item={'title':title,'url':url,'path':str(file.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'kind':kind}
    m['files']=[x for x in m['files'] if x['url']!=url or x['title']!=title]+[item];mf.write_text(json.dumps(m,ensure_ascii=False,indent=2))

for unit in ['001','002','102']:
    manual_original('温州医科大学',R/'official-web-exports'/('wmu-'+unit+'.html'),
        'https://yjszs.wmu.edu.cn/yzbm/zsml/sszsml/zsmlYjfx/2027/'+unit+'/105118?ksfs=21',
        '温州医科大学2027年105118目录-'+unit,'.html','official_web_catalogue')
manual_original('东南大学',R/'official-web-exports/seu-data.js','https://gsas.seu.edu.cn/ssmlcx2027/pages/js/data.js',
    '东南大学2027年目录官方数据','.js','official_directory_data')
for unit in ['530','540']:
    manual_original('华中科技大学',R/'official-web-exports'/('hust-'+unit+'.html'),
        'https://yanzhao.hust.edu.cn/Master/Zsml_View.aspx',
        '华中科技大学2027年专业学位目录-'+unit,'.html','official_web_catalogue')
manual_original('大连理工大学',R/'official-web-exports/dlut-final.html',
    'https://yjszs.dlut.edu.cn/zsbm/zsml/sszsml/zsmlYjfx/2027/500/105118?ksfs=21',
    '大连理工大学2027年105118专业目录','.html','official_web_catalogue')
manual_original('山东大学',R/'official-web-exports/sdu-105118.json',
    'https://sduyjs.sdu.edu.cn/yjszs/plugins/zs/sszs/xdeh3mizwpj6Psdm/zsxxfb/list/zymlxqV2',
    '山东大学2027年105118目录官方数据','.json','official_directory_data')
manual_original('山东大学',R/'official-web-exports/sdu-fields.json',
    'https://sduyjs.sdu.edu.cn/yjszs/plugins/zs/sszs/xdeh3mizwpj6Psdm/zsxxfb/list/getZymlDetailTableFields',
    '山东大学2027年目录官方表头','.json','official_directory_data')
manual_original('山东大学',R/'official-web-exports/sdu-105118.html',
    'https://sduyjs.sdu.edu.cn/yjszs/plugins/zs/sszs/zsxxfb/index',
    '山东大学2027年105118目录正文整理','.html','research_snapshot')

aliases={'皖南医学院':'皖南医科大学','绍兴文理学院':'绍兴大学','湖州师范学院':'湖州师范大学','新乡医学院':'河南医药大学','滨州医学院':'山东医药大学'}
records=[]
plans_path=V2/'data/plan2027.json';plans=json.loads(plans_path.read_text())
baseline_path=R/'plan2027_before.json'
if not baseline_path.exists():shutil.copyfile(plans_path,baseline_path)
baseline=json.loads(baseline_path.read_text())['plans']
for s in scope:
    name=s['name'];mf=DEST/name/'manifest.json';m=json.loads(mf.read_text());p=baseline.get(name,{})
    facts=review.get(name,{})
    # Restrict the final archive to the requested year and admissions materials.
    files=[];seen=set()
    for f in m['files']:
        title=f['title'];raw=ROOT/f['path'];ext=by_path.get(f['path'],{})
        text_path=ROOT/ext.get('text_path','__no_text__');text=text_path.read_text() if text_path.is_file() else ''
        if any(k in title for k in ['2017','推免','免试','直博','非全日制','全日制学硕','参考','自命题','学制一览']):continue
        if title=='内嵌文件' and text:
            first=text[:500]
            if any(k in first for k in ['非全日制','学术学位','参考书','考试相关书目']) and '105118' not in text:continue
            if not any(k in text for k in ['105118','麻醉学']) and not any(k in first for k in ['招生章程','招生简章']):continue
        if f['sha256'] in seen:continue
        seen.add(f['sha256'])
        if title=='内嵌文件':
            kind='招生专业目录' if '105118' in text or ('麻醉学' in text and '105100' in text) else '招生章程'
            title=name+'2027年'+kind;f['title']=title
        # Collapse labels duplicated by site markup; keep filenames concise and stable.
        if len(title)%2==0 and title[:len(title)//2]==title[len(title)//2:]:title=title[:len(title)//2]
        for suffix in ['.pdf','.xlsx','.xls','.doc','.docx']:
            if title.count(suffix)>1:title=title.split(suffix)[0]+suffix
        clean=re.sub(r'[\\/:*?"<>|\s]+','_',title).strip('_.')[:110]
        if not clean.lower().endswith(raw.suffix.lower()):clean+=raw.suffix
        target=raw.parent/clean
        if target.exists() and target!=raw and hashlib.sha256(target.read_bytes()).hexdigest()!=f['sha256']:
            target=target.with_name(target.stem+'-'+f['sha256'][:6]+target.suffix)
        if target!=raw:shutil.copyfile(raw,target)
        f.update(path=str(target.relative_to(ROOT)),title=title)
        f.setdefault('kind','original')
        files.append(f)
    m['files']=files
    # The official webpage IS the directory for these two institutions.
    for pg in m['pages']:
        if any(u in pg['url'] for u in ['grs.zmu.edu.cn/info/1099/6790.htm','content_143619']):
            item=dict(pg);item['kind']='official_web_catalogue';files.append(item)
    files=list({(f['url'],f['sha256']):f for f in files}.values())
    m['files']=files
    binaries=[f for f in files if f['kind']=='original']
    webdirs=[f for f in files if f['kind'] in ['official_web_catalogue','official_directory_data']]
    status='已下载官方原附件' if binaries else '已归档官方网页目录' if webdirs else '仅归档招生网页，目录待补' if m['pages'] else '官网访问受限，待补原件'
    check='官方原文已核验' if facts else '已检索，人数待复核'
    detail=facts.get('detail') or ('本轮已保存官方招生页面；既有计划数尚缺本轮原文复核，请从官方入口核对，不能视作新确认。' if m['pages'] else '官网访问受限；本轮未取得可核验的招生计划原件，保留既有数值并标记待核。')
    if name=='内蒙古科技大学（包头医学院）' and not facts:detail='已下载官方2027目录，但PDF为扫描版，文本提取无有效条目；原有25人本轮尚未逐页核实。'
    if name in ['南华大学','新乡医学院']:detail='已下载2027专业目录；临床专硕按105100大类及方向招生，未将临床医学大类人数当成麻醉学人数。'
    if name=='苏州大学':detail='已下载2027目录；105118列报考条件和科目，未列可据以独立核实的专业计划数；原有数字标记待核。'
    if name=='上海交通大学':detail='已下载2027医学院Excel目录，105118列五个医院方向但未给各方向招生人数；原有数字标记待核。'
    if name=='南方医科大学':detail='已下载2027目录，105118列五个临床方向但未给专业人数；原有数字须另从统考计划核实。'
    if name=='东南大学':detail='已保存2027目录官方数据；专硕按105100临床医学09麻醉方向招生，目录未单列方向人数，不能沿用旧105118解释。'
    if name=='大连理工大学':detail='已归档2027年105118官方动态目录正文，列导师和考试科目但未给专业人数；章程要求统考拟招人数以中国研招网为准，既有2人本轮未独立核实。'
    if name=='华中科技大学':detail='已归档2027专业学位530/540两家临床学院官网目录正文，麻醉按105100临床医学下方向展示；独立统考名额仍须结合研招网核实，未用目录内其他数字替代。'
    if name=='中国医科大学':detail=facts['detail']
    official_urls=facts.get('official_urls') or list(dict.fromkeys(f['url'] for f in binaries)) or [x['url'] for x in m['pages']] or [x['url'] for x in m.get('candidates',[])]
    current=plans['plans'].setdefault(name,{})
    current.setdefault('previous_plan',p.get('plan'));current.setdefault('previous_basis',p.get('basis'))
    if facts:
        current.update(plan=facts['plan'],basis=facts['basis'],source='2026-10-18核验：'+facts['detail'])
    current.update(checked_at='2026-10-18',verification='verified' if facts else 'pending',
        official_urls=official_urls,archive='admissions/index.html#'+quote(name),latest_note=detail)
    if facts.get('policy2027'):current['policy2027']=facts['policy2027']
    if facts.get('zone2027'):current['zone2027']=facts['zone2027']
    rec={**s,'current_name':aliases.get(name,name),'plan':current.get('plan'),'basis':current.get('basis'),
        'previous_plan':p.get('plan'),'previous_basis':p.get('basis'),'verification':check,'verified':bool(facts),
        'checked_at':'2026-10-18','note':detail,'status':status,'official_urls':official_urls,
        'files':files,'pages':m['pages'],'failures':m['failures']}
    if facts.get('zone2027'):rec['zone2027']=facts['zone2027']
    m.update(status=status,checked_at='2026-10-18');mf.write_text(json.dumps(m,ensure_ascii=False,indent=2))
    records.append(rec)
plans['meta'].update(generated_at='2026-10-18',last_check_scope='从容区、稳健区、进取区72所，检索范围按更新前分区固定',
    source_priority='本轮已下载的官方目录及官网原文优先；未复核既有数字以verification=pending明确标记',
    note='2027拟计划按basis分别记录统考、总数、推免及转段口径。pending是既有待核值，非本轮最新确认。')
plans_path.write_text(json.dumps(plans,ensure_ascii=False,indent=2)+'\n')
counts=collections.Counter(x['status'] for x in records)
meta={'checked_at':'2026-10-18','schools':len(records),'verified_plans':len(review),'download_status':dict(counts),
      'scope_note':'沿用本轮开始时的三档院校，历史复试线和实录数据不因本轮招生计划变更而改写。',
      'plan_note':'官方目录通常是拟计划；总数与普通统考名额不可混用。pending数值保留用于追溯，不作新确认。'}
result={'meta':meta,'schools':records}
(V2/'data/admissions2027.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(ROOT/'docs/admissions/manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

cols=['梯度','院校','当前校名','2027计划','口径','本轮核验','原计划','下载状态','核验日期','补充说明','官方链接','本地文件']
csvpath=ROOT/'docs/admissions/招生计划与下载清单.csv'
with csvpath.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(cols)
    for x in records:w.writerow([x['tier'],x['name'],x['current_name'],x['plan'],x['basis'],x['verification'],x['previous_plan'],x['status'],x['checked_at'],x['note'],'\n'.join(x['official_urls']),'\n'.join(f['path'] for f in x['files'])])

def a(url,label):return '<a href="'+html.escape(url,quote=True)+'">'+html.escape(label)+'</a>'
rows=[]
for x in records:
    download='<br>'.join(a(f['path'].removeprefix('docs/admissions/'),f['title'])+' <small>'+str(round(f['bytes']/1024))+' KB</small>' for f in x['files']) or '尚未取得目录文件'
    sources='<br>'.join(a(u,'官方来源 '+str(i+1)) for i,u in enumerate(x['official_urls'][:5])) or '见检索记录'
    page='<br>'.join(a(p['path'].removeprefix('docs/admissions/'),'网页原文：'+p['title'][:55]) for p in x['pages'] if not any(k in p['title'] for k in ['推免','免试','博士']))
    val=str(x['plan']) if x['plan'] is not None else '—'
    if not x['verified']:val+='（旧值待核）' if x['plan'] is not None else ''
    changed='；原值 '+str(x['previous_plan']) if x['previous_plan'] is not None and x['plan']!=x['previous_plan'] else ''
    rows.append('<tr id="'+html.escape(x['name'])+'" data-tier="'+x['tier']+'" data-name="'+html.escape(x['name']+x['current_name'])+'"><td>'+x['tier']+'</td><td><b>'+html.escape(x['name'])+'</b>'+('<br><small>现名：'+x['current_name']+'</small>' if x['current_name']!=x['name'] else '')+'</td><td><strong>'+val+'</strong><br>'+html.escape(x['basis'] or '未知')+html.escape(changed)+'<br><small>'+x['verification']+'</small></td><td>'+html.escape(x['status'])+'<p>'+download+'</p><details><summary>来源与网页原文</summary>'+sources+'<p>'+page+'</p></details></td><td>'+html.escape(x['note'])+'</td></tr>')
summary='；'.join(k+' '+str(v)+' 所' for k,v in counts.items())
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>2027招生计划与官方文件</title>
<style>body{margin:0;background:#f6f4ef;color:#27303d;font:15px/1.65 system-ui,"PingFang SC",sans-serif}header,main{max-width:1440px;margin:auto;padding:24px}header{background:#1f3a52;color:white}header a{color:#fff}h1{font-size:26px;margin:12px 0}a{color:#245e91;overflow-wrap:anywhere}small{color:#68717b}header small{color:#ddd}p{margin:8px 0}nav{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}input,select{font:inherit;padding:9px;border:1px solid #ccc;border-radius:5px}.wrap{overflow:auto}table{width:100%;border-collapse:collapse;background:white;min-width:1000px}td,th{text-align:left;vertical-align:top;border-bottom:1px solid #dedbd3;padding:14px}th{background:#ece8df}td:nth-child(1){width:65px}td:nth-child(2){width:145px}td:nth-child(3){width:180px}td:nth-child(4){width:350px}tr:target{background:#fff2cb}summary{cursor:pointer}strong{font-size:19px}details{margin-top:10px}details a{display:block}button{font:inherit;padding:8px 14px}footer{padding:25px;color:#667}</style>
<header><a href="../index.html">← 三年分数与人数对照</a><h1>2027 招生计划与官方文件</h1><p>从容区、稳健区、进取区 · 72 所院校 · 核验日期 2026-10-18</p><p>SUMMARY</p></header><main><p>已核对官方原文的人数共 VERIFIED 所。其余既有数值标注“旧值待核”；网页快照、目录原附件与访问受限分别标明。招生目录是拟计划，含推免、长学制转段和专项的总数不能当成普通统考名额。</p><p><a href="招生计划与下载清单.csv" download>下载逐校清单 CSV</a> · <a href="招生文件合集-2026-10-18.zip" download>下载已取得的官方文件合集 ZIP</a> · <a href="核验报告.md">核验报告与待补清单</a></p><nav><input id="q" placeholder="搜索院校或当前校名" aria-label="搜索院校"><select id="tier" aria-label="梯度筛选"><option>全部梯度</option><option>从容区</option><option>稳健区</option><option>进取区</option></select><span id="count"></span></nav><div class="wrap"><table><thead><tr><th>梯度</th><th>院校</th><th>2027拟计划与口径</th><th>文件与来源</th><th>本轮补充</th></tr></thead><tbody>ROWS</tbody></table></div></main><footer>按本轮开始时的院校分区固定范围；目录调整不改写历年真实录取成绩。未取得文件不等于学校未发布或不招生。</footer><script>const q=document.getElementById('q'),tier=document.getElementById('tier');function filter(){let n=0;document.querySelectorAll('tbody tr').forEach(r=>{r.hidden=!(r.dataset.name.includes(q.value.trim())&&(tier.value==='全部梯度'||r.dataset.tier===tier.value));if(!r.hidden)n++});document.getElementById('count').textContent=n+' 所'}q.addEventListener('input',filter);tier.addEventListener('change',filter);filter();</script></html>'''.replace('SUMMARY',html.escape(summary)).replace('VERIFIED',str(len(review))).replace('ROWS','\n'.join(rows))
(ROOT/'docs/admissions/index.html').write_text(page)

md=['# 2027年招生计划与官方文件核验报告','', '核验日期：2026-10-18。范围：从容区29所、稳健区32所、进取区11所，共72所。','',
    summary+'。官方原文人数核验 '+str(len(review))+' 所。','',
    '## 口径与本轮边界','',
    '- 本轮新增的是2027拟招生计划、报考限制、目录和附件证据。没有用复试线改写2024—2026真实录取最低分。',
    '- 普通统考、含推免总数、5+3转段、退役士兵计划分别注明。尚未核验的原数保留但标记待复核，不能理解为最新确认。',
    '- 学校分区按本轮开始时锁定；延边大学2027执行A类线，历史B类线仍保留在历年成绩中。',
    '- 校方网页目录保存为HTML原文；PDF/Excel/Word原附件保留原内容及SHA-256。动态目录只保存空壳不计作已取得目录正文。',
    '- 招生简章原件已下载不等于麻醉学独立统考名额已公布。原件为扫描PDF时不凭OCR空值填0。','',
    '## 人数或口径的重要修正','',
    '|院校|原值/口径|本轮值/口径|依据|','|---|---|---|---|']
for x in records:
    if x['verified'] and (x['plan']!=x['previous_plan'] or x['basis']!=x['previous_basis']):
        md.append('|'+x['name']+'|'+str(x['previous_plan'])+' / '+str(x['previous_basis'])+'|'+str(x['plan'])+' / '+x['basis']+'|'+x['note']+'|')
md+=['','## 逐校来源与文件','']
for x in records:
    md+=['### '+x['tier']+' · '+x['name'],'',x['status']+'；'+x['verification']+'。', '',x['note'],'']
    md+=['- [官方来源 '+str(i+1)+']('+u+')' for i,u in enumerate(x['official_urls'])]
    md+=['- [原件：'+f['title']+']('+f['path'].removeprefix('docs/admissions/')+')（SHA-256：'+f['sha256']+'）' for f in x['files']]
    md+=['']
md+=['## 仍需补取或核对的院校','']
for x in records:
    if not x['verified'] or not x['files']:
        reasons='；'.join(dict.fromkeys('官网请求失败' if 'SSL' in f['error'] or '412' in f['error'] or '483' in f['error'] else '附件下载受限' for f in x['failures']))
        md.append('- '+x['name']+'：'+x['status']+'；'+x['note']+('（'+reasons+'）' if reasons else ''))
report='\n'.join(md)+'\n';(ROOT/'docs/admissions/核验报告.md').write_text(report)
(R/'核验报告.md').write_text(report)
print(json.dumps(meta,ensure_ascii=False,indent=2))
