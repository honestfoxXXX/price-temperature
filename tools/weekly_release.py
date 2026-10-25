"""Verified episode -> cloned narration, safe-area motion video, covers, article.
Usage: python tools/weekly_release.py 2026-10-25 [voice|render|assets|verify]
Credentials only via VOLC_KEY. No publication to social accounts.
"""
import os,json,pathlib,sys,wave,hashlib,subprocess,math,shutil
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
from make_voice_volc import synth
R=pathlib.Path(__file__).resolve().parents[1]
DAY=sys.argv[1] if len(sys.argv)>1 else '2026-10-25'
E=json.loads((R/'data'/('episode-'+DAY+'.json')).read_text(encoding='utf-8'))
OUT=R/'output'/DAY; V=OUT/'视频'; V.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe(); W,H,FPS,SR=1080,1920,30,24000
SAFE=104; RIGHT=W-SAFE; INK='#2b211b'; MUTED='#806b5d'; ORANGE='#ff5a1f'; RED='#cf3b31'; GREEN='#138b4a'
@lru_cache(maxsize=64)
def font(size,bold=False,emoji=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('seguiemj.ttf' if emoji else 'msyhbd.ttc' if bold else 'msyh.ttc'),size)
def fit(text,size,width,bold=True):
    while ImageDraw.Draw(Image.new('RGB',(1,1))).textlength(text,font=font(size,bold))>width:size-=1
    return font(size,bold)
def ff(args):subprocess.run([FF,'-y','-loglevel','error']+args,check=True)
def readwav(path):
    with wave.open(str(path)) as q:
        assert q.getframerate()==SR and q.getnchannels()==1 and q.getsampwidth()==2
        return np.frombuffer(q.readframes(q.getnframes()),dtype='<i2').astype(np.float32)/32768

def voice():
    key=os.environ.get('VOLC_KEY')
    if not key:raise RuntimeError('VOLC_KEY missing; never store credentials in episode files')
    cache=V/'voice';cache.mkdir(exist_ok=True)
    raw=[]
    for i,c in enumerate(E['clips']):
        token=hashlib.sha256((E['voice']+c['text']).encode()).hexdigest()[:12]
        mp=cache/(token+'.mp3');wav=cache/(token+'.wav')
        if not mp.exists():mp.write_bytes(synth(c['text'],E['voice'],key))
        if not wav.exists():ff(['-i',str(mp),'-ar',str(SR),'-ac','1',str(wav)])
        raw.append((wav,len(readwav(wav))/SR))
        print('Voice',i+1,round(raw[-1][1],2),flush=True)
    dur=sum(x[1] for x in raw); ratio=max(1.,dur/25.)
    if ratio>1.65:raise RuntimeError('Narration too long: shorten text rather than excessive speed-up')
    for i,(p,d) in enumerate(raw):
        target=cache/('clip-%02d.wav'%i)
        ff(['-i',str(p),'-af','atempo=%.6f'%ratio,'-ar',str(SR),'-ac','1',str(target)])
    (V/'voice-manifest.json').write_text(json.dumps({'voice':E['voice'],'rawSeconds':dur,'tempo':ratio,'clips':[c['text'] for c in E['clips']]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Cloned voice ready; tempo',round(ratio,3),flush=True)

def base():
    a=np.zeros((H,W,3),dtype=np.uint8)
    for y in range(H):a[y,:,:]=(255,int(248-10*y/H),int(241-15*y/H))
    img=Image.fromarray(a).convert('RGBA');d=ImageDraw.Draw(img)
    # Fixed branding within 104px safe area.
    ico=Image.open(R/'assets/logo-icon-128.png').convert('RGBA').resize((78,78),Image.Resampling.LANCZOS)
    img.alpha_composite(ico,(SAFE,104));d.text((SAFE+98,104),'今天贵不贵',font=font(43,True),fill=INK)
    d.text((SAFE+98,158),'什么该买，什么该等',font=font(24),fill=MUTED)
    d.text((SAFE,235),'10月25日核验更新 · 第43周内容',font=font(25),fill=MUTED)
    return img

def lines(text,maxwidth,f):
    d=ImageDraw.Draw(Image.new('RGB',(1,1)));out=[];line=''
    for ch in text:
        if ch=='\n' or d.textlength(line+ch,font=f)>maxwidth:
            if line:out.append(line)
            line='' if ch=='\n' else ch
        else:line+=ch
    if line:out.append(line)
    return out

def textblock(img,text,y,size=54,bold=True,color=INK,width=None):
    d=ImageDraw.Draw(img);f=font(size,bold)
    for line in lines(text,width or RIGHT-SAFE,f):
        d.text((SAFE,y),line,font=f,fill=color);y+=int(size*1.5)
    return y

def board_image(b,active):
    img=base();d=ImageDraw.Draw(img)
    textblock(img,b['title'],355,62)
    textblock(img,b['note'],455,27,False,MUTED)
    count=len(b['rows']);rh=184 if count>2 else 250;top=590 if count>2 else 665
    for i,row in enumerate(b['rows']):
        y=top+i*rh;selected=i in active
        d.rounded_rectangle((SAFE,y,RIGHT,y+rh-18),radius=24,fill='#ffffff' if selected else '#f5ebe3',outline='#ffc7a5' if selected else '#e6d6c8',width=3 if selected else 1)
        d.text((SAFE+22,y+40),row['icon'],font=font(49,emoji=True),embedded_color=True)
        # Names and values occupy separate nonoverlapping columns.
        namefont=fit(row['name'],44,385)
        d.text((SAFE+94,y+30),row['name'],font=namefont,fill=INK if selected else '#806c60')
        vf=fit(row['value'],62,258)
        d.text((RIGHT-24,y+25),row['value'],font=vf,fill=(GREEN if row['direction']=='down' else RED),anchor='ra')
        bf=fit(row['basis'],23,RIGHT-SAFE-130,False)
        d.text((SAFE+94,y+103),row['basis'],font=bf,fill=MUTED)
    textblock(img,'统计期：10月12—18日；10月19日发布',1416,25,False,MUTED)
    textblock(img,'来源：农业农村部 · 全国批发市场周均价',1460,23,False,MUTED)
    return img

def scene(c):
    if c['scene']=='board':return board_image(E['boards'][c['board']],c['active'])
    img=base();d=ImageDraw.Draw(img)
    if c['scene']=='hook':
        d.text((SAFE,435),'🥚',font=font(135,emoji=True),embedded_color=True)
        textblock(img,'鸡蛋变便宜了',630,91)
        textblock(img,'怎么还说贵？',770,91,color=RED)
        textblock(img,'比上周便宜，仍比去年同期贵。',985,35,False,MUTED)
    elif c['scene']=='takeaway':
        textblock(img,'涨跌之前，',510,85)
        textblock(img,'先问：和谁比？',640,79,color=ORANGE)
        textblock(img,'周环比：对比上周\n同比：对比去年同期',880,46)
        textblock(img,'批发价 ≠ 本地零售价',1150,44,color=RED)
    elif c['scene']=='correction':
        textblock(img,'更正上期',400,70,color=RED)
        textblock(img,'数据存储设备',570,63)
        textblock(img,'同比 +46.7%',720,78,color=RED)
        textblock(img,'月环比 +1.7%',865,64)
        textblock(img,'此前说成“一个月涨46.7%”有误。',1045,33)
        textblock(img,'统计期：2026年9月\n来源：国家统计局10月14日解读原文',1170,27,False,MUTED)
    else:
        textblock(img,'看清涨跌，',520,88)
        textblock(img,'别被数字带跑。',655,83,color=ORANGE)
        textblock(img,'每周日，更新有出处的数据。',900,40)
        d.rounded_rectangle((SAFE,1065,RIGHT,1180),radius=40,fill=ORANGE)
        d.text(((SAFE+RIGHT)//2,1120),'关注「今天贵不贵」',font=font(48,True),fill='white',anchor='mm')
        textblock(img,'AI复刻配音 · AI生成配乐',1290,24,False,MUTED)
    return img

def subtitle(img,text):
    ls=lines(text,RIGHT-SAFE-60,font(39,True));ph=35+len(ls)*56
    layer=Image.new('RGBA',(RIGHT-SAFE,ph),(0,0,0,0));d=ImageDraw.Draw(layer)
    d.rounded_rectangle((0,0,layer.width-1,ph-1),radius=24,fill=(255,255,255,240))
    for i,l in enumerate(ls):d.text((30,12+i*56),l,font=font(39,True),fill=INK)
    img.alpha_composite(layer,(SAFE,1550))

def render():
    manifest=json.loads((V/'voice-manifest.json').read_text(encoding='utf-8'))
    assert manifest['clips']==[c['text'] for c in E['clips']],'Audio/script mismatch'
    arrays=[readwav(V/'voice'/('clip-%02d.wav'%i)) for i in range(len(E['clips']))]
    starts=[];t=.16
    for a in arrays:starts.append(t);t+=len(a)/SR+.13
    total=t+.45
    assert total<=35, '35-second hard limit'
    count=math.ceil(total*FPS);total=count/FPS
    voicebuf=np.zeros(round(total*SR),dtype=np.float32)
    for start,a in zip(starts,arrays):
        k=round((start+.035)*SR);voicebuf[k:k+len(a)]+=a
    peak=np.abs(voicebuf).max()
    if peak:voicebuf*=.83/peak
    bgm_source=R/'output/2026-10-18/视频/_bgm.wav'
    if bgm_source.exists():
        ff(['-i',str(bgm_source),'-ar',str(SR),'-ac','1',str(V/'配乐.wav')])
        b=readwav(V/'配乐.wav');b=np.tile(b,math.ceil(len(voicebuf)/len(b)))[:len(voicebuf)]
        rms=np.sqrt(np.mean(b*b))
        if rms:b*=.009/rms
        fade=min(int(.6*SR),len(b));b[:fade]*=np.linspace(0,1,fade);b[-int(SR):]*=np.linspace(1,0,int(SR))
        voicebuf+=b
    voicebuf=np.clip(voicebuf,-.98,.98)
    track=V/'配音混音.wav'
    with wave.open(str(track),'wb') as q:q.setparams((1,2,SR,len(voicebuf),'NONE','not compressed'));q.writeframes((voicebuf*32767).astype('<i2').tobytes())
    outfile=V/'今天贵不贵-2026-10-25.mp4'
    cmd=[FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(FPS),'-i','-','-i',str(track),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-shortest','-movflags','+faststart',str(outfile)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    frames=[scene(c) for c in E['clips']]
    srt=[]
    def stamp(t):
        ms=round(t*1000);return '%02d:%02d:%02d,%03d'%(ms//3600000,ms//60000%60,ms//1000%60,ms%1000)
    for i,c in enumerate(E['clips']):srt.append('%d\n%s --> %s\n%s\n'%(i+1,stamp(starts[i]),stamp(starts[i]+len(arrays[i])/SR),c['text']))
    (V/'字幕.srt').write_text('\n'.join(srt),encoding='utf-8-sig')
    for f in range(count):
        tm=f/FPS;idx=max([i for i,s in enumerate(starts) if tm>=s] or [0]);img=frames[idx].copy()
        # A moving colored accent and active rows, without moving the safe-area text.
        d=ImageDraw.Draw(img);d.rounded_rectangle((SAFE,330,SAFE+int((RIGHT-SAFE)*max(0.,min(1.,(tm-starts[idx])/.22))),338),radius=4,fill=ORANGE)
        subtitle(img,E['clips'][idx]['caption'])
        d=ImageDraw.Draw(img);d.rounded_rectangle((SAFE,1800,RIGHT,1806),radius=3,fill='#e4d4c8');d.rounded_rectangle((SAFE,1800,SAFE+int((RIGHT-SAFE)*tm/total),1806),radius=3,fill=ORANGE)
        proc.stdin.write(img.convert('RGB').tobytes())
    proc.stdin.close();rc=proc.wait()
    if rc:raise RuntimeError('Encoder failed '+str(rc))
    for i in [0,1,3,6,7]:
        im=frames[i].copy();subtitle(im,E['clips'][i]['caption']);im.convert('RGB').save(V/('预览-%02d.png'%i))
    (V/'timing.json').write_text(json.dumps({'duration':total,'starts':starts,'safeMarginPixels':SAFE,'voice':E['voice'],'sources':[E['sourceUrl'],E['monthlyCorrectionUrl']]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rendered',outfile,'seconds',round(total,2),flush=True)

def assets():
    # Cover avoids unverified superlatives and explicitly labels both reference periods.
    for h,tag in [(1440,'3x4'),(1920,'9x16')]:
        img=base().crop((0,0,W,h));d=ImageDraw.Draw(img)
        y=390 if h==1440 else 600
        textblock(img,'鸡蛋变便宜了',y,91)
        textblock(img,'怎么还说贵？',y+140,88,color=RED)
        textblock(img,'比上周 −4.3%',y+355,64,color=GREEN)
        textblock(img,'比去年同期 +28.5%',y+465,64,color=RED)
        textblock(img,'统计期 10/12—10/18 · 全国批发',h-120,27,False,MUTED)
        img.convert('RGB').save(OUT/('封面-视频号-'+tag+'.png'))
    cover=Image.new('RGB',(1350,575),'#fff4ea');d=ImageDraw.Draw(cover)
    ico=Image.open(R/'assets/logo-icon-128.png').convert('RGBA').resize((68,68));cover.paste(ico,(100,55),ico)
    d.text((190,65),'今天贵不贵 · 10月25日核验更新',font=font(34,True),fill=INK)
    d.text((100,205),'鸡蛋变便宜了，怎么还说贵？',font=fit('鸡蛋变便宜了，怎么还说贵？',78,1150),fill=INK)
    d.text((100,355),'比上周 −4.3%  ｜  比去年同期 +28.5%',font=font(46,True),fill=GREEN)
    d.text((100,470),'全国批发周均价 · 第42周（10/12—10/18）',font=font(29),fill=MUTED)
    cover.save(OUT/'封面-公众号.png')
    article='''# 鸡蛋变便宜了，怎么还说贵？｜今天贵不贵

鸡蛋比上周便宜了4.3%，却比去年同期贵28.5%。不是矛盾，是比较的时间不同。

【在公众号编辑器中插入本期视频号视频】

【在这里上传本期「长图.jpg」】

本期依据农业农村部第42周周报，统计期为**10月12—18日**，10月19日发布。以上是全国批发周均价变化，不等于本地零售价。

**更正上期：**存储设备上涨46.7%、平板电脑上涨23.6%，均是9月同比，不是月环比。对应月环比为1.7%、1.5%。此前表述有误，网站与本期视频已更正。

完整数据：
https://honestfoxXXX.github.io/price-temperature/

每周日更新。什么该买，什么该等，先看有出处的数据。
'''
    (OUT/'公众号文章.md').write_text(article,encoding='utf-8')
    (OUT/'发布说明.md').write_text('''# 本期发布说明

1. 先发布视频号，再在公众号编辑器插入对应视频。
2. 视频号封面用3x4版，公众号封面用横版。
3. 公众号正文仅视频、长图、地址及简短统计口径/更正说明。
4. 网站“阅读原文”填 https://honestfoxXXX.github.io/price-temperature/ 。
5. 按发布平台实际选项声明AI复刻配音/AI配乐；不承诺标注对推荐量的影响。
6. 本期数据截至10月18日，更新日为10月25日；不是第43周行情。
7. 未操作视频号/公众号账号，尚未替用户发布。

## 视频号短标题
鸡蛋变便宜了，怎么还说贵？

## 视频号描述
鸡蛋周环比−4.3%，同比却+28.5%。先看和谁比，再判断贵不贵。
数据：农业农村部第42周，10/12—10/18，全国批发周均价。
更正上期：存储+46.7%是同比，月环比为+1.7%。
#物价 #菜价 #生活成本
''',encoding='utf-8')
    print('Covers and simple article ready')

if __name__=='__main__':
    mode=sys.argv[2] if len(sys.argv)>2 else 'assets'
    {'voice':voice,'render':render,'assets':assets}[mode]()
