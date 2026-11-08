import pathlib

p = pathlib.Path('tools/weekly_release.py')
s = p.read_text(encoding='utf-8')
start = s.index('def assets():')
end = s.index("if __name__=='__main__':")

new = """def assets():
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
    d.text((190,65),'今天贵不贵 · 11月8日更新',font=font(34,True),fill=INK)
    d.text((100,200),t,font=fit(t,70,1150),fill=INK)
    d.text((100,330),'电脑 +21.8%　手机 +14.9%　平板 +23.6%',font=font(36,True),fill=RED)
    d.text((100,410),'家电 −1.8%，是今年少见的在跌的大件',font=font(34,True),fill=GREEN)
    d.text((100,500),'9月CPI同比 · 国家统计局 2026-10-14',font=font(25),fill=MUTED)
    cover.save(OUT/'封面-公众号.png')

    article = (
        '# 双11 该买什么，别急着买什么｜今天贵不贵\\n\\n'
        '先说结论：**家电可以买，电脑和手机再等等。**\\n\\n'
        '【在公众号编辑器中插入本期视频号视频】\\n\\n'
        '## 在涨的四样，是一条链\\n\\n'
        '按国家统计局 9月CPI 同比：\\n\\n'
        '- 数据存储设备 **+46.7%**\\n'
        '- 平板电脑 **+23.6%**\\n'
        '- 计算机 **+21.8%**\\n'
        '- 移动电话机 **+14.9%**\\n\\n'
        '这不是四个独立的涨价，是同一条链：存储芯片涨，整机跟着涨。'
        '所以今年下单买电脑手机，买的是这条链的高位。\\n\\n'
        '## 在跌的那一类\\n\\n'
        '- 家用器具 **−1.8%**（比去年同期便宜）\\n'
        '- 生活用品及服务 **+0.2%**（基本没动）\\n\\n'
        '大件里，家电是少见的还在跌的一类。\\n\\n'
        '【在这里上传本期「长图.jpg」】\\n\\n'
        '完整数据：\\nhttps://honestfoxXXX.github.io/price-temperature/\\n\\n'
        '**口径说明**：以上是 9月CPI 同比，统计期 2026年9月，10月14日发布；'
        '不是双11当天的成交价，也不代表某一款具体型号。'
        '各平台各店铺的双11折扣不同，文中说的是整体价格水平。\\n\\n'
        '**这不是预测**：我不知道明年电脑手机会不会更便宜，只能说今年它们一直在涨。\\n\\n'
        '每周日更新。什么该买，什么该等。\\n'
    )
    (OUT/'公众号文章.md').write_text(article,encoding='utf-8')

    notes = (
        '# 本期发布说明 · '+t+'\\n\\n'
        '1. 先发布视频号，再在公众号编辑器插入对应视频。\\n'
        '2. 视频号封面用3x4版，公众号封面用横版。\\n'
        '3. 公众号正文：结论 → 视频 → 在涨的四样 → 在跌的一类 → 长图 → 地址 → 口径。\\n'
        '4. 网站“阅读原文”填 https://honestfoxXXX.github.io/price-temperature/ 。\\n'
        '5. 按发布平台实际选项声明AI复刻配音/AI配乐；不承诺标注对推荐量的影响。\\n'
        '6. 数据为9月CPI同比，不是双11当日价格；折扣因店而异。\\n'
        '7. 未操作视频号/公众号账号，尚未替用户发布。\\n'
        '8. 不做“明年更便宜”的预测，只说今年在涨。\\n\\n'
        '## 视频号短标题\\n双11先别急着换电脑手机\\n\\n'
        '## 视频号描述\\n'
        '9月CPI同比：电脑+21.8%、平板+23.6%、手机+14.9%、存储+46.7%——同一条链，存储涨、整机涨。\\n'
        '反过来，家电−1.8%，是少见的还在跌的大件。\\n'
        '所以这波：家电可以买，电脑手机再等等。\\n'
        '数据：国家统计局9月CPI，10月14日发布。\\n'
        '#双11 #该买什么 #电脑涨价 #家电 #生活成本\\n'
    )
    (OUT/'发布说明.md').write_text(notes,encoding='utf-8')
    print('Covers and simple article ready')


"""
s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('assets() rewritten for Double-11')
