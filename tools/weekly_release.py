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
SAFE=104; RIGHT=W-SAFE; INK=(43,33,27); MUTED=(128,107,93); ORANGE=(255,90,31); RED=(207,59,49); GREEN=(19,139,74)
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
    dur=sum(x[1] for x in raw); ratio=max(1.,dur/float(E.get('voiceTargetSeconds',34.)))
    # 听感优先：宁可片子长一点，也不靠变速硬压。超过 1.12 就说明台词写长了。
    if ratio>1.20:
        raise RuntimeError('Narration too long (%.2fx). Shorten the script instead of speeding up.'%ratio)
    for i,(p,d) in enumerate(raw):
        target=cache/('clip-%02d.wav'%i)
        ff(['-i',str(p),'-af','atempo=%.6f'%ratio,'-ar',str(SR),'-ac','1',str(target)])
    (V/'voice-manifest.json').write_text(json.dumps({'voice':E['voice'],'rawSeconds':dur,'tempo':ratio,'clips':[c['text'] for c in E['clips']]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Cloned voice ready; tempo',round(ratio,3),flush=True)

def _rgba(h,a=255):
    h=h.lstrip('#')
    return (int(h[0:2],16),int(h[2:4],16),int(h[4:6],16),max(0,min(255,int(a))))

def base():
    a=np.zeros((H,W,3),dtype=np.uint8)
    for y in range(H):a[y,:,:]=(255,int(248-10*y/H),int(241-15*y/H))
    img=Image.fromarray(a).convert('RGBA');d=ImageDraw.Draw(img)
    ico=Image.open(R/'assets/logo-icon-128.png').convert('RGBA').resize((78,78),Image.Resampling.LANCZOS)
    img.alpha_composite(ico,(SAFE,104));d.text((SAFE+98,104),'今天贵不贵',font=font(43,True),fill=INK)
    d.text((SAFE+98,158),'什么该买，什么该等',font=font(24),fill=MUTED)
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

def ease(t): return 1-(1-t)**3

def _grad(w):
    w=max(1,int(w));g=Image.new('RGBA',(w,26),(0,0,0,0));d=ImageDraw.Draw(g)
    for x in range(w):
        t=x/max(1,w-1)
        d.line([(x,0),(x,25)],fill=(int(255-48*t),int(138-79*t),int(76-27*t),255))
    return g

def board_image(b,local):
    """横向条形图：长度＝幅度，数字同步滚动，逐行入场。"""
    img=base();a=ImageDraw.Draw(img)
    p=min(1.0,local/0.32)
    a.text((SAFE,330+int((1-ease(p))*26)),b['title'],font=font(68),fill=INK+(int(255*p),))
    a.rounded_rectangle((SAFE,430,SAFE+int(120*ease(p)),436),radius=3,fill=ORANGE+(int(255*p),))
    rows=b['rows']
    vals=[abs(float(str(r['value']).replace('+','').replace('−','-').replace('%',''))) for r in rows]
    mx=max(vals) or 1
    neg=[str(r['value']).startswith(('−','-')) for r in rows]
    mixed=any(neg) and not all(neg)
    top=500 if len(rows)>=3 else 640;rh=250 if len(rows)<=4 else 205
    for i,row in enumerate(rows):
        t0=0.30+i*0.13
        rp=min(1.0,max(0.0,(local-t0)/0.30))
        if rp<=0:continue
        y=top+i*rh+int((1-ease(rp))*46);alpha=int(255*ease(rp))
        a.text((SAFE,y+4),row['icon'],font=font(50,emoji=True),embedded_color=True)
        a.text((SAFE+68,y),row['name'],font=fit(row['name'],46,560),fill=INK+(alpha,))
        bp=min(1.0,max(0.0,(local-t0-0.06)/0.95))
        sign='−' if neg[i] else '+'
        num=vals[i]*ease(bp)
        color=GREEN if neg[i] else RED
        a.text((RIGHT,y-6),'%s%.1f%%'%(sign,num),font=font(64),fill=color+(alpha,),anchor='ra')
        ty=y+118
        a.rounded_rectangle((SAFE,ty,RIGHT,ty+26),radius=13,fill=(240,226,214,alpha))
        if mixed:
            cx=SAFE+(RIGHT-SAFE)//2
            a.line((cx,ty-16,cx,ty+42),fill=(206,188,173,alpha),width=3)
        span=RIGHT-SAFE
        half=span//2 if mixed else span
        length=int(half*(vals[i]/mx)*ease(bp))
        if length>8:
            if mixed:
                cx=SAFE+span//2
                x0=cx-length if neg[i] else cx
            else:
                x0=SAFE
            g=_grad(length) if not neg[i] else Image.new('RGBA',(length,26),GREEN+(255,))
            mask=Image.new('L',(length,26),0)
            ImageDraw.Draw(mask).rounded_rectangle((0,0,length-1,25),radius=13,fill=255)
            if alpha<255:mask=mask.point(lambda v:int(v*alpha/255))
            img.paste(g,(x0,ty),mask)
    if b.get('note'):
        cp=min(1.0,max(0.0,(local-2.4)/0.5))
        if cp>0:
            a.text((SAFE,1452+int((1-ease(cp))*20)),b['note'],font=font(40),fill=MUTED+(int(255*ease(cp)),))
    return img

def scene(c,local=0.0):
    if c['scene']=='board':return board_image(E['boards'][c['board']],local)
    img=base();d=ImageDraw.Draw(img)
    if c['scene']=='hook':
        p=min(1.0,local/0.34)
        d.text((SAFE,435),c.get('icon','🥬'),font=font(135,emoji=True),embedded_color=True)
        y=630
        colors=c.get('colors',[])
        for i,line in enumerate(c.get('big') or ['这周']):
            lp=min(1.0,max(0.0,(local-0.08*i)/0.34))
            if lp>0:
                col=_rgba(colors[i] if i<len(colors) else '#2b211b',255*ease(lp))
                textblock(img,line,y+int((1-ease(lp))*40),91,color=col)
            y+=140
        if c.get('note'):
            np_=min(1.0,max(0.0,(local-0.5)/0.4))
            if np_>0:textblock(img,c['note'],y+18,35,False,MUTED)
    else:
        p=min(1.0,local/0.4)
        textblock(img,'该买的趁现在',520,88)
        textblock(img,'该等的别急。',655,83,color=ORANGE)
        textblock(img,'每周日更新有出处的数据。',900,40)
        d.rounded_rectangle((SAFE,1065,RIGHT,1180),radius=40,fill=ORANGE)
        d.text(((SAFE+RIGHT)//2,1120),'关注「今天贵不贵」',font=font(48,True),fill='white',anchor='mm')
    return img

def subtitle(img,text):
    ls=lines(text,RIGHT-SAFE-60,font(39,True));ph=35+len(ls)*56
    layer=Image.new('RGBA',(RIGHT-SAFE,ph),(0,0,0,0));d=ImageDraw.Draw(layer)
    d.rounded_rectangle((0,0,layer.width-1,ph-1),radius=24,fill=(255,255,255,240))
    for i,l in enumerate(ls):d.text((30,12+i*56),l,font=font(39,True),fill=INK)
    img.alpha_composite(layer,(SAFE,1585))

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
    outfile=V/('今天贵不贵-'+DAY+'.mp4')
    cmd=[FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(FPS),'-i','-','-i',str(track),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-af','acompressor=threshold=-16dB:ratio=3:attack=5:release=150,treble=g=2,loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-shortest','-movflags','+faststart',str(outfile)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    srt=[]
    def stamp(t):
        ms=round(t*1000);return '%02d:%02d:%02d,%03d'%(ms//3600000,ms//60000%60,ms//1000%60,ms%1000)
    for i,c in enumerate(E['clips']):srt.append('%d\n%s --> %s\n%s\n'%(i+1,stamp(starts[i]),stamp(starts[i]+len(arrays[i])/SR),c['text']))
    (V/'字幕.srt').write_text('\n'.join(srt),encoding='utf-8-sig')

    ends=starts[1:]+[total]
    XF=0.24
    def shot(idx,local):
        img=scene(E['clips'][idx],local)
        d=ImageDraw.Draw(img)
        d.rounded_rectangle((SAFE,1800,RIGHT,1806),radius=3,fill='#e4d4c8')
        d.rounded_rectangle((SAFE,1800,SAFE+int((RIGHT-SAFE)*min(1.,(starts[idx]+local)/total)),1806),radius=3,fill=ORANGE)
        subtitle(img,E['clips'][idx]['caption'])
        return img

    def push(a,b,k):
        """b 从下方推入，a 向上退出。"""
        ca=a if a.mode=='RGBA' else a.convert('RGBA')
        cb=b if b.mode=='RGBA' else b.convert('RGBA')
        out=Image.new('RGBA',(W,H),(255,246,236,255))
        out.paste(ca,(0,-int(H*k)));out.paste(cb,(0,int(H*(1-k))))
        return out

    for f in range(count):
        tm=f/FPS;idx=max([i for i,s in enumerate(starts) if tm>=s] or [0])
        local=tm-starts[idx]
        cur=scene(E['clips'][idx],local)
        if idx>0 and local<XF:
            prev=scene(E['clips'][idx-1],ends[idx-1]-starts[idx-1])
            img=push(prev,cur,ease(local/XF))
        else:
            img=cur
        d=ImageDraw.Draw(img)
        d.rounded_rectangle((SAFE,1800,RIGHT,1806),radius=3,fill='#e4d4c8')
        d.rounded_rectangle((SAFE,1800,SAFE+int((RIGHT-SAFE)*tm/total),1806),radius=3,fill=ORANGE)
        subtitle(img,E['clips'][idx]['caption'])
        # 镜头：全片缓慢推近 3%
        z=1.0+0.03*(tm/total)
        crop=img.convert('RGB').resize((int(W*z),int(H*z)),Image.LANCZOS)
        left=(crop.width-W)//2;top=(crop.height-H)//2
        proc.stdin.write(crop.crop((left,top,left+W,top+H)).tobytes())
    proc.stdin.close();rc=proc.wait()
    if rc:raise RuntimeError('Encoder failed '+str(rc))
    for i in sorted({0,1,3,len(E['clips'])-1}):
        im=shot(i,min(2.6,ends[i]-starts[i]))
        im.convert('RGB').save(V/('预览-%02d.png'%i))
    (V/'timing.json').write_text(json.dumps({'duration':total,'starts':starts,'safeMarginPixels':SAFE,'voice':E['voice'],'sources':[E['sourceUrl'],E['monthlyCorrectionUrl']]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rendered',outfile,'seconds',round(total,2),flush=True)

def assets():
    t=E['title']
    for h,tag in [(1440,'3x4'),(1920,'9x16')]:
        img=base().crop((0,0,W,h));d=ImageDraw.Draw(img)
        y=390 if h==1440 else 600
        textblock(img,'双11 先别急',y,88)
        textblock(img,'这两样在涨',y+140,92,color=RED)
        textblock(img,'电脑 +21.8%',y+330,56,color=RED)
        textblock(img,'手机 +14.9%',y+420,56,color=RED)
        textblock(img,'平板 +23.6%　存储 +46.7%',y+510,40,color=RED)
        textblock(img,'家电反而 −1.8%，可以下手',h-130,30,False,MUTED)
        img.convert('RGB').save(OUT/('封面-视频号-'+tag+'.png'))
    cover=Image.new('RGB',(1350,575),'#fff4ea');d=ImageDraw.Draw(cover)
    ico=Image.open(R/'assets/logo-icon-128.png').convert('RGBA').resize((68,68));cover.paste(ico,(100,55),ico)
    d.text((190,65),'今天贵不贵',font=font(34,True),fill=INK)
    d.text((100,200),t,font=fit(t,70,1150),fill=INK)
    d.text((100,330),'电脑 +21.8%　手机 +14.9%　平板 +23.6%',font=font(36,True),fill=RED)
    d.text((100,410),'家电 −1.8%，是今年少见的在跌的大件',font=font(34,True),fill=GREEN)
    d.text((100,500),'9月CPI同比 · 国家统计局 2026-10-14',font=font(25),fill=MUTED)
    cover.save(OUT/'封面-公众号.png')

    article = (
        '# 双11 该买什么，别急着买什么｜今天贵不贵\n\n'
        '先说结论：**家电可以买，电脑和手机再等等。**\n\n'
        '【在公众号编辑器中插入本期视频号视频】\n\n'
        '## 在涨的四样，是一条链\n\n'
        '按国家统计局 9月CPI 同比：\n\n'
        '- 数据存储设备 **+46.7%**\n'
        '- 平板电脑 **+23.6%**\n'
        '- 计算机 **+21.8%**\n'
        '- 移动电话机 **+14.9%**\n\n'
        '这不是四个独立的涨价，是同一条链：存储芯片涨，整机跟着涨。'
        '所以今年下单买电脑手机，买的是这条链的高位。\n\n'
        '## 在跌的那一类\n\n'
        '- 家用器具 **−1.8%**（比去年同期便宜）\n'
        '- 生活用品及服务 **+0.2%**（基本没动）\n\n'
        '大件里，家电是少见的还在跌的一类。\n\n'
        '【在这里上传本期「长图.jpg」】\n\n'
        '完整数据：\nhttps://honestfoxXXX.github.io/price-temperature/\n\n'
        '**口径说明**：以上是 9月CPI 同比，统计期 2026年9月，10月14日发布；'
        '不是双11当天的成交价，也不代表某一款具体型号。'
        '各平台各店铺的双11折扣不同，文中说的是整体价格水平。\n\n'
        '**这不是预测**：我不知道明年电脑手机会不会更便宜，只能说今年它们一直在涨。\n\n'
        '每周日更新。什么该买，什么该等。\n'
    )
    (OUT/'公众号文章.md').write_text(article,encoding='utf-8')

    notes = (
        '# 本期发布说明 · '+t+'\n\n'
        '1. 先发布视频号，再在公众号编辑器插入对应视频。\n'
        '2. 视频号封面用3x4版，公众号封面用横版。\n'
        '3. 公众号正文：结论 → 视频 → 在涨的四样 → 在跌的一类 → 长图 → 地址 → 口径。\n'
        '4. 网站“阅读原文”填 https://honestfoxXXX.github.io/price-temperature/ 。\n'
        '5. 按发布平台实际选项声明AI复刻配音/AI配乐；不承诺标注对推荐量的影响。\n'
        '6. 数据为9月CPI同比，不是双11当日价格；折扣因店而异。\n'
        '7. 未操作视频号/公众号账号，尚未替用户发布。\n'
        '8. 不做“明年更便宜”的预测，只说今年在涨。\n\n'
        '## 视频号短标题\n双11先别急着换电脑手机\n\n'
        '## 视频号描述\n'
        '9月CPI同比：电脑+21.8%、平板+23.6%、手机+14.9%、存储+46.7%——同一条链，存储涨、整机涨。\n'
        '反过来，家电−1.8%，是少见的还在跌的大件。\n'
        '所以这波：家电可以买，电脑手机再等等。\n'
        '数据：国家统计局9月CPI，10月14日发布。\n'
        '#双11 #该买什么 #电脑涨价 #家电 #生活成本\n'
    )
    (OUT/'发布说明.md').write_text(notes,encoding='utf-8')
    print('Covers and simple article ready')


if __name__=='__main__':
    mode=sys.argv[2] if len(sys.argv)>2 else 'assets'
    {'voice':voice,'render':render,'assets':assets}[mode]()
