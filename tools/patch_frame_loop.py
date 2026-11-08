"""Rewrite the frame loop: per-scene local time, camera push-in, slide transitions."""
import pathlib

p = pathlib.Path('tools/weekly_release.py')
s = p.read_text(encoding='utf-8')
start = s.index('    frames=[scene(c) for c in E[\'clips\']]')
end = s.index('    proc.stdin.close();rc=proc.wait()')

new = '''    srt=[]
    def stamp(t):
        ms=round(t*1000);return '%02d:%02d:%02d,%03d'%(ms//3600000,ms//60000%60,ms//1000%60,ms%1000)
    for i,c in enumerate(E['clips']):srt.append('%d\\n%s --> %s\\n%s\\n'%(i+1,stamp(starts[i]),stamp(starts[i]+len(arrays[i])/SR),c['text']))
    (V/'字幕.srt').write_text('\\n'.join(srt),encoding='utf-8-sig')

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
        ca=a.convert('RGB');cb=b.convert('RGB')
        out=Image.new('RGB',(W,H),(255,246,236))
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
'''
s = s[:start] + new + s[end:]

# previews: render with animation state at a moment inside each scene
s = s.replace("""    for i in sorted({0,1,3,len(E['clips'])-1}):
        im=frames[i].copy();subtitle(im,E['clips'][i]['caption']);im.convert('RGB').save(V/('预览-%02d.png'%i))""",
"""    for i in sorted({0,1,3,len(E['clips'])-1}):
        im=shot(i,min(2.6,ends[i]-starts[i]))
        im.convert('RGB').save(V/('预览-%02d.png'%i))""")
p.write_text(s, encoding='utf-8')
print('frame loop rewritten')
