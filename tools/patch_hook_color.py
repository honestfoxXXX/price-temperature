import pathlib
p = pathlib.Path('tools/weekly_release.py')
s = p.read_text(encoding='utf-8')

helper = '''def _rgba(h,a=255):
    h=h.lstrip('#')
    return (int(h[0:2],16),int(h[2:4],16),int(h[4:6],16),max(0,min(255,int(a))))

def base():'''
s = s.replace('def base():', helper, 1)

old = """            lp=min(1.0,max(0.0,(local-0.08*i)/0.34))
            if lp>0:
                textblock(img,line,y+int((1-ease(lp))*40),91,
                          color=(colors[i] if i<len(colors) else INK)[:-1]+(int(255*ease(lp)),) if len(colors)>i else INK)
            y+=140"""
new = """            lp=min(1.0,max(0.0,(local-0.08*i)/0.34))
            if lp>0:
                col=_rgba(colors[i] if i<len(colors) else '#2b211b',255*ease(lp))
                textblock(img,line,y+int((1-ease(lp))*40),91,color=col)
            y+=140"""
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print('hook colour fixed')
