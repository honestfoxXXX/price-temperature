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
        textblock(img,'金饰克价',y,95)
        textblock(img,'跌到 1010',y+150,95,color=GREEN)
        textblock(img,'年内最高 1700 元/克',y+330,52,color=MUTED)
        textblock(img,'原料金 860 元',y+430,56,color=INK)
        textblock(img,'品牌店约 1200 元',y+510,56,color=RED)
        textblock(img,'批发市场报价 10/26 · 原料金 10/30',h-120,26,False,MUTED)
        img.convert('RGB').save(OUT/('封面-视频号-'+tag+'.png'))
    cover=Image.new('RGB',(1350,575),'#fff4ea');d=ImageDraw.Draw(cover)
    ico=Image.open(R/'assets/logo-icon-128.png').convert('RGBA').resize((68,68));cover.paste(ico,(100,55),ico)
    d.text((190,65),'今天贵不贵 · 11月1日更新',font=font(34,True),fill=INK)
    d.text((100,200),t,font=fit(t,70,1150),fill=INK)
    d.text((100,330),'原料金 860 元　批发金饰 1010 元',font=font(40,True),fill=INK)
    d.text((100,415),'品牌店约 1200 元，差的是工费和品牌',font=font(36,True),fill=RED)
    d.text((100,500),'金饰/铂金：批发报价 10/26　原料金：上金所 10/30',font=font(25),fill=MUTED)
    cover.save(OUT/'封面-公众号.png')

    article = (
        '# 金饰克价，从1700跌到1010｜今天贵不贵\\n\\n'
        '年内最高 1700 元/克，现在批发市场报 **1010 元/克**，跌了约四成。\\n\\n'
        '但同样一克金，价格差得很远：\\n\\n'
        '- **原料金 860 元**（上金所 Au99.99，10月30日）\\n'
        '- **批发金饰 1010 元**（北京水贝，10月26日）\\n'
        '- **品牌店约 1200 元**（老庙黄金当日报价）\\n\\n'
        '中间的差价是工费和品牌溢价，不是金价本身。买的时候先问克价，再问工费。\\n\\n'
        '铂金跌得更狠：从最高 700 元/克跌到 395 元，接近腰斩。\\n\\n'
        '【在公众号编辑器中插入本期视频号视频】\\n\\n'
        '【在这里上传本期「长图.jpg」】\\n\\n'
        '数据来源：中国证券报（经济网转载）10月27日、上海黄金交易所10月30日行情。'
        '金饰与铂金为批发市场报价，品牌店零售更高。\\n\\n'
        '买来戴，现在确实比年初便宜不少；想靠它赚钱，别猜底。\\n\\n'
        '完整数据：\\nhttps://honestfoxXXX.github.io/price-temperature/\\n\\n'
        '每周日更新。什么该买，什么该等。\\n'
    )
    (OUT/'公众号文章.md').write_text(article,encoding='utf-8')

    notes = (
        '# 本期发布说明 · '+t+'\\n\\n'
        '1. 先发布视频号，再在公众号编辑器插入对应视频。\\n'
        '2. 视频号封面用3x4版，公众号封面用横版。\\n'
        '3. 公众号正文：金饰克价 → 三个价对比 → 铂金 → 数据来源 → 地址。\\n'
        '4. 网站“阅读原文”填 https://honestfoxXXX.github.io/price-temperature/ 。\\n'
        '5. 按发布平台实际选项声明AI复刻配音/AI配乐；不承诺标注对推荐量的影响。\\n'
        '6. 金饰/铂金为10月26日批发报价，原料金为10月30日上金所行情；不是同一天的数。\\n'
        '7. 未操作视频号/公众号账号，尚未替用户发布。\\n'
        '8. 不做投资判断，“别猜底”是提示，不是建议。\\n\\n'
        '## 视频号短标题\\n金饰跌到1010一克\\n\\n'
        '## 视频号描述\\n'
        '金饰克价从年内最高1700跌到1010，跌了约四成。\\n'
        '同样一克金：原料金860、批发金饰1010、品牌店约1200，差的是工费和品牌。\\n'
        '铂金从700跌到395，接近腰斩。\\n'
        '数据：中国证券报10/27、上金所10/30。\\n'
        '#金价 #黄金 #买什么划算 #生活成本\\n'
    )
    (OUT/'发布说明.md').write_text(notes,encoding='utf-8')
    print('Covers and simple article ready')


"""
s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('assets() rewritten for gold')
