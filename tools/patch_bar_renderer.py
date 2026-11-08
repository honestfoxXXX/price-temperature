"""Replace the slide-style renderer with the approved bar-chart system."""
import pathlib

p = pathlib.Path('tools/weekly_release.py')
s = p.read_text(encoding='utf-8')
start = s.index('def base():')
end = s.index('def render():')

new = '''def base():
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
        if ch=='\\n' or d.textlength(line+ch,font=f)>maxwidth:
            if line:out.append(line)
            line='' if ch=='\\n' else ch
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
    neg=[v<0 for v in [str(r['value']).startswith('−') or str(r['value']).startswith('-') for r in rows]]
    mixed=any(neg) and not all(neg)
    top=540;rh=268 if len(rows)<=4 else 210
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
        span=RIGHT-SAFE
        length=int(span*(vals[i]/mx)*ease(bp))
        if length>8:
            if mixed:
                cx=SAFE+span//2
                x0=cx-length//2 if neg[i] else cx
            else:
                x0=SAFE
            g=_grad(length);mask=Image.new('L',(length,26),0)
            ImageDraw.Draw(mask).rounded_rectangle((0,0,length-1,25),radius=13,fill=255)
            if alpha<255:mask=mask.point(lambda v:int(v*alpha/255))
            img.paste(g,(x0,ty),mask)
    if b.get('note'):
        cp=min(1.0,max(0.0,(local-2.4)/0.5))
        if cp>0:
            a.text((SAFE,1640+int((1-ease(cp))*20)),b['note'],font=font(40),fill=MUTED+(int(255*ease(cp)),))
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
                textblock(img,line,y+int((1-ease(lp))*40),91,
                          color=(colors[i] if i<len(colors) else INK)[:-1]+(int(255*ease(lp)),) if len(colors)>i else INK)
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
    img.alpha_composite(layer,(SAFE,1550))

'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('renderer swapped to bar chart')
