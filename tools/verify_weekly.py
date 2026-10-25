"""Release assertions, full video decode, validation report and user-facing ZIP."""
import json,pathlib,sys,subprocess,re,zipfile
from PIL import Image
import imageio_ffmpeg
R=pathlib.Path(__file__).resolve().parents[1];day=sys.argv[1] if len(sys.argv)>1 else '2026-10-25';out=R/'output'/day;v=out/'视频'
e=json.loads((R/'data'/('episode-'+day+'.json')).read_text(encoding='utf-8'))
d=json.loads((R/'data/prices.json').read_text(encoding='utf-8'));c=json.loads((R/'data/cpi.json').read_text(encoding='utf-8'))
watch=json.loads((R/'data/watchlist.json').read_text(encoding='utf-8'))
assert d['meta']['asOf']==day
assert e['title']=='鸡蛋变便宜了，怎么还说贵？'
assert e['clips'][0]['text']==e['title']
assert e['clips'][0]['caption']==e['title']
assert not any(x['scene']=='correction' or '更正上期' in x['text'] for x in e['clips'])
manifest=json.loads((v/'voice-manifest.json').read_text(encoding='utf-8'))
assert manifest['clips']==[x['text'] for x in e['clips']]
assert e['title'] in (out/'公众号文章.md').read_text(encoding='utf-8')
assert e['title'] in (out/'发布说明.md').read_text(encoding='utf-8')
assert e['title'] in (v/'字幕.srt').read_text(encoding='utf-8-sig')
food=[i for cat in d['categories'] for i in cat['items'] if i.get('verified')]
assert len(food)==8
assert next(i for i in food if i['id']=='egg')['mom']==-4.3
assert next(i for i in food if i['id']=='egg')['yoy']==28.5
assert next(i for i in watch['items'] if i['name']=='数据存储设备')['mom']==1.7
assert next(i for i in c['rows'] if i['name']=='平板电脑')['yoy']==23.6
t=json.loads((v/'timing.json').read_text(encoding='utf-8'))
assert t['duration']<=35 and t['safeMarginPixels']>=100 and t['voice']==e['voice']
mp=v/'今天贵不贵-2026-10-25.mp4';ff=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,'-v','error','-i',str(mp),'-f','null','-'],check=True)
probe=subprocess.run([ff,'-hide_banner','-i',str(mp)],capture_output=True,text=True,errors='replace')
assert '1080x1920' in probe.stderr and '30 fps' in probe.stderr and 'Audio: aac' in probe.stderr
assert len(re.findall('-->',(v/'字幕.srt').read_text(encoding='utf-8-sig')))==len(e['clips'])
for p,shape in [('封面-视频号-3x4.png',(1080,1440)),('封面-视频号-9x16.png',(1080,1920)),('封面-公众号.png',(1350,575))]:
    with Image.open(out/p) as im:assert im.size==shape
with Image.open(out/'长图.jpg') as im:
    assert im.width==750 and im.height<8000
    longsize=im.size
# Credentials must never enter release metadata.
for p in [R/'data'/('episode-'+day+'.json'),out/'公众号文章.md',out/'核验说明.md']:
    txt=p.read_text(encoding='utf-8');assert not re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',txt)
report={'date':day,'checks':'PASS','videoSeconds':t['duration'],'safeMarginPixels':t['safeMarginPixels'],'videoSize':[1080,1920],'fps':30,'fullDecode':'PASS','clonedVoice':t['voice'],'captionLines':len(e['clips']),'longImageSize':longsize,'verifiedPriceItems':8,'pendingLegacyItems':62,'sourceUrls':[e['sourceUrl'],e['monthlyCorrectionUrl']]}
(out/'验收结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
files=[mp,v/'字幕.srt',out/'公众号文章.md',out/'长图.jpg',out/'封面-视频号-3x4.png',out/'封面-视频号-9x16.png',out/'封面-公众号.png',out/'发布说明.md',out/'核验说明.md',out/'验收结果.json']
z=out/('今天贵不贵-'+day+'-发布素材包.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as q:
    for p in files:q.write(p,p.relative_to(out))
with zipfile.ZipFile(z) as q:assert q.testzip() is None
print(json.dumps(report,ensure_ascii=False,indent=2));print('Package:',z)
