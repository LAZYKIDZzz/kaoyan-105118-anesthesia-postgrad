"""Manually read and submit the public attachment download verification form.

prepare SCHOOL retrieves the verification image; submit SCHOOL CODE submits it.
Session cookies stay in /tmp and are never included in the archive.
"""
import hashlib,json,pathlib,re,subprocess,sys,io,zipfile
from urllib.parse import urljoin,urlparse
ROOT=pathlib.Path(__file__).resolve().parents[2]
TEMP=pathlib.Path('/tmp/anesthesia-admissions-verification');TEMP.mkdir(exist_ok=True)
mode,name=sys.argv[1:3]
mf=ROOT/'docs/admissions/2027'/name/'manifest.json';m=json.loads(mf.read_text())
key=hashlib.sha256(name.encode()).hexdigest()[:12];cookie=TEMP/(key+'.cookies');state=TEMP/(key+'.json')
def req(u,dest):
    r=subprocess.run(['curl','-sSL','--max-time','30','--connect-timeout','10','-A','Mozilla/5.0','-c',str(cookie),'-b',str(cookie),'-o',str(dest),u],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr)
    return dest.read_bytes()
if mode=='prepare':
    c=[f for f in m['failures'] if 'signature' in f['error'] and any(k in f.get('title','') for k in ['目录','计划','章程']) and not any(k in f.get('title','') for k in ['参考','非规培','本科','学术','非全日制','退役','推免','免试','博士','直博'])]
    if name=='延边大学':c=[f for f in c if '医学院' in f.get('title','') and '专业型' in f.get('title','')]
    if not c:raise ValueError('No pending directory verification')
    c=c[0];b=req(c['url'],TEMP/(key+'.html'));html=b.decode('utf-8',errors='replace')
    if '请输入验证码' not in html:raise ValueError('Not a verification page')
    im=re.search(r'[\"\']([^\"\']*createimage\.jsp[^\"\']*)[\"\']',html)
    u=urljoin(c['url'],im.group(1) if im else '/system/resource/js/filedownload/createimage.jsp')
    image=TEMP/(key+'.png');req(u,image);state.write_text(json.dumps(c,ensure_ascii=False));print(json.dumps({'school':name,'image':str(image),'title':c['title']},ensure_ascii=False))
elif mode=='submit':
    c=json.loads(state.read_text());label=re.sub(r'[\\/:*?"<>|\s]+','_',c['title'])
    ext=pathlib.Path(label).suffix
    dest=mf.parent/(label if ext else label+'.pdf')
    b=req(c['url']+'&codeValue='+sys.argv[3],dest)
    if not (b.startswith(b'%PDF') or b.startswith(b'PK') or b.startswith(bytes.fromhex('d0cf11e0'))):
        dest.unlink();raise ValueError('Verification failed; no file downloaded')
    if b.startswith(b'PK'):
        entries=zipfile.ZipFile(io.BytesIO(b)).namelist()
        suffix='.xlsx' if 'xl/workbook.xml' in entries else '.docx' if 'word/document.xml' in entries else '.zip'
    elif b.startswith(b'%PDF'):suffix='.pdf'
    else:suffix='.xls'
    if dest.suffix!=suffix:dest=dest.rename(dest.with_suffix(suffix))
    e={k:c[k] for k in ['title','url']};e.update(path=str(dest.relative_to(ROOT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
    m['files']=[x for x in m['files'] if x['url']!=e['url']]+[e];m['failures']=[x for x in m['failures'] if x['url']!=e['url']];m['status']='已下载原附件';mf.write_text(json.dumps(m,ensure_ascii=False,indent=2));print(name,'已下载',len(b))
