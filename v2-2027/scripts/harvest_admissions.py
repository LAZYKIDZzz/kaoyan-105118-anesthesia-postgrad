"""Download official admissions pages and linked original files; preserve an audit manifest.

Run with a candidates JSON path. Does not infer or alter admission counts.
"""
import concurrent.futures, hashlib, json, pathlib, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote, quote

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'v2-2027/research/2026-10-18'
DEST = ROOT / 'docs/admissions/2027'
DEST.mkdir(parents=True, exist_ok=True)

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.current=None; self.text=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='a': self.current=[d.get('href',''),d.get('title','')]
        if tag in ('iframe','embed','object'):
            u=d.get('src') or d.get('data')
            if u:self.links.append((u,'内嵌文件'))
    def handle_data(self, data):
        self.text.append(data)
        if self.current:self.current[1]+=data
    def handle_endtag(self, tag):
        if tag=='a' and self.current:
            self.links.append(tuple(self.current));self.current=None

def fetch(url, target):
    url=quote(url,safe=':/?&=%+;,@!~*\'()[]')
    r=subprocess.run(['curl','-sS','-L','--connect-timeout','12','--max-time','40','--retry','1',
        '-A','Mozilla/5.0','-o',str(target),'-w','%{http_code}\n%{url_effective}',url],capture_output=True,text=True)
    status=r.stdout.splitlines()
    if r.returncode or not status or status[0]!='200':
        if target.exists():target.unlink()
        raise ValueError((r.stderr or r.stdout)[-300:])
    b=target.read_bytes()
    if not b:raise ValueError('empty response')
    return b,status[-1]

def decode(b):
    for enc in ['utf-8','gb18030']:
        try:return b.decode(enc)
        except UnicodeDecodeError:pass
    return b.decode('utf-8',errors='replace')

def safe(s):return re.sub(r'[\\/:*?"<>|\s]+','_',s).strip('_.')[:140]

def process(s):
    out=dict(s);out['pages']=[];out['files']=[];out['failures']=[]
    folder=DEST/safe(s['name']);folder.mkdir(exist_ok=True)
    previous={}
    if (folder/'manifest.json').exists():
        old=json.loads((folder/'manifest.json').read_text())
        previous={x['url']:x.get('effective_url',x['url']) for x in old.get('pages',[])}
        out['files']=[x for x in old.get('files',[]) if (ROOT/x['path']).exists()]
    known=set();queue=[(c['url'],c['title'],0) for c in s['candidates'][:5]]
    while queue and len(out['pages'])<7:
        url,title,depth=queue.pop(0)
        if url in known:continue
        known.add(url)
        try:
            token=hashlib.sha256(url.encode()).hexdigest()[:10]
            target=folder/('page-'+token+'.html')
            if target.exists():b,effective=target.read_bytes(),previous.get(url,url)
            else:b,effective=fetch(url,target)
            if b.startswith(b'%PDF'):
                target=target.rename(target.with_suffix('.pdf'))
                out['files'].append({'title':title,'url':url,'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)});continue
            html=decode(b);p=Links();p.feed(html)
            if not re.search(r'2027|招生|目录',html):
                target.unlink();raise ValueError('response is not an admissions page')
            txt=' '.join(p.text)
            # Some official pages put their original PDF URL in a public preview script.
            for raw in re.findall(r'[\"\']([^\"\'<>\s]+\.pdf(?:\?[^\"\'<>\s]*)?)[\"\']', html, re.I):
                if not raw.startswith(('application/','image/')):
                    p.links.append((raw,'内嵌文件'))
            (RESEARCH/(safe(s['name'])+'-'+token+'.txt')).write_text(txt,encoding='utf-8')
            out['pages'].append({'title':title,'url':url,'effective_url':effective,'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
            for href,label in p.links:
                u=urljoin(effective,href);label=' '.join(label.split())
                if not u.startswith(('http://','https://')) or u in known or any(f['url']==u for f in out['files']):continue
                isfile=bool(re.search(r'\.(pdf|xlsx?|docx?|zip|rar)(?:$|[?&#])|download|Download',u,re.I))
                if isfile:
                    if any(k in label for k in ['大纲','参考书','参考教材','联系','学术学位','非全日制','博士','推免','全日制学硕','非规培','普通高等学校本科专业']):continue
                    if s['name']=='延边大学' and not ('医学院' in label and '专业型' in label):continue
                    if re.search(r'202[0-6]',label) and '2027' not in label:continue
                    if not (any(k in label for k in ['目录','计划','简章','章程','专业学位','附件1','附件2','附件一','附件二']) or label=='内嵌文件'):continue
                    if len(out['files'])>=7:continue
                    known.add(u)
                    ext=re.search(r'\.(pdf|xlsx?|docx?|zip|rar)(?:$|[?&#])',u,re.I)
                    nameext=re.search(r'\.(pdf|xlsx?|docx?|zip|rar)$',label,re.I)
                    ext='.'+ext.group(1).lower() if ext else '.'+nameext.group(1).lower() if nameext else '.bin'
                    name=safe(label) or '招生附件'
                    target=folder/(name if name.lower().endswith(ext) else name+ext)
                    target=folder/(target.stem+'-'+hashlib.sha256(u.encode()).hexdigest()[:6]+ext)
                    try:
                        data,_=fetch(u,target)
                        if data.startswith(b'%PDF'):expected='.pdf'
                        elif data.startswith(b'PK'):expected=ext if ext in ['.xlsx','.docx','.zip'] else '.zip'
                        elif data.startswith(b'Rar!'):expected='.rar'
                        elif data.startswith(bytes.fromhex('d0cf11e0')):expected=ext
                        else:target.unlink();raise ValueError('attachment response has no recognized file signature')
                        if target.suffix!=expected:target=target.rename(target.with_suffix(expected))
                        out['files'].append({'title':label,'url':u,'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
                    except Exception as e:out['failures'].append({'url':u,'title':label,'error':str(e)})
                elif depth<3 and '2027' in label and any(k in label for k in ['招生专业目录','招生目录','招生章程','招生简章','统考招生计划','招生指南','分专业拟招生计划','拟招生总计划']):
                    if any(k in label for k in ['博士','推免','非全日制','工商管理','工程管理','参考书']):continue
                    host=urlparse(u).hostname or ''
                    if host.endswith(('edu.cn','chsi.com.cn','301hospital.com.cn','gdph.org.cn','gmu.cn','mdjmu.cn')):queue.append((u,label,depth+1))
        except Exception as e:
            out['failures'].append({'url':url,'title':title,'error':str(e)})
    out['status']='已下载原附件' if out['files'] else '已保存官方网页' if out['pages'] else '下载失败'
    (folder/'manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(s['name'],out['status'],len(out['files']),flush=True)
    return out

if __name__=='__main__':
    items=json.loads(pathlib.Path(sys.argv[1]).read_text())
    if len(sys.argv)>2:items=[s for s in items if s['name'] in sys.argv[2:]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(process,items))
