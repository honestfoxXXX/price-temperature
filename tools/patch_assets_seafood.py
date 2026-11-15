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
        textblock(img,'梭子蟹',y,95)
        textblock(img,'三十多一斤',y+150,92,color=GREEN)
        textblock(img,'国庆时还要 60—70',y+330,48,color=MUTED)
        textblock(img,'龙虾 150 → 60 元/斤',y+420,52,color=GREEN)
        textblock(img,'但带鱼、黄花鱼在涨',y+510,48,color=RED)
        textblock(img,'开海后量增价降',h-130,28,False,MUTED)
        img.convert('RGB').save(OUT/('封面-视频号-'+tag+'.png'))
    cover=Image.new('RGB',(1350,575),'#fff4ea');d=ImageDraw.Draw(cover)
    ico=Image.open(R/'assets/logo-icon-128.png').convert('RGBA').resize((68,68));cover.paste(ico,(100,55),ico)
    d.text((190,65),'今天贵不贵',font=font(34,True),fill=INK)
    d.text((100,200),t,font=fit(t,68,1150),fill=INK)
    d.text((100,330),'波士顿龙虾 150 → 60 元/斤',font=font(38,True),fill=GREEN)
    d.text((100,410),'但大带鱼 +1.1%、大黄花 +0.2%',font=font(34,True),fill=RED)
    d.text((100,500),'来源：人民日报 · 农业农村部周报',font=font(24),fill=MUTED)
    cover.save(OUT/'封面-公众号.png')

    article = (
        '# 梭子蟹三十多一斤，海鲜真的便宜了｜今天贵不贵\\n\\n'
        '国庆时梭子蟹要六七十，现在三十多。开海之后，大众海鲜确实便宜了。\\n\\n'
        '【在公众号编辑器中插入本期视频号视频】\\n\\n'
        '## 开海之后，降了多少\\n\\n'
        '- **波士顿龙虾**：开渔前 8两—1斤3两规格 150 元/斤，开渔后约 **60 元/斤**\\n'
        '- **梭子蟹**：半斤左右规格，开渔后降幅约 **30%**\\n'
        '- **大闸蟹**：国庆每只 20 元上下，现在十几元\\n\\n'
        '## 但不是全都便宜\\n\\n'
        '按农业农村部第45周批发周均价：\\n\\n'
        '- 大带鱼 **+1.1%**、大黄花鱼 **+0.2%**，反而在涨\\n'
        '- 草鱼 **−0.9%**、鲫鱼 **−1.0%**，淡水鱼在跌\\n\\n'
        '贝类稳中缓降；海胆、海肠这类小品种产量小，价格不跌反涨。'
        '所以准确的说法是**大众海鲜更平价、吃海鲜更日常**，不是“所有海鲜进入低价时代”。\\n\\n'
        '## 什么时候最便宜\\n\\n'
        '9 月刚开海是一年中最低，春节假期是一年中最高。冻货受季节影响小，价格本来就稳。\\n\\n'
        '## 顺带一句\\n\\n'
        '11月12日24时起油价下调，92号汽油每升 **−0.51 元**，加满一箱省约 26 元。\\n\\n'
        '【在这里上传本期「长图.jpg」】\\n\\n'
        '完整数据：\\nhttps://honestfoxXXX.github.io/price-temperature/\\n\\n'
        '**口径说明**：梭子蟹、龙虾、大闸蟹的价格来自人民日报 11月11日《大众海鲜更平价》报道，'
        '是市场零售价；周环比来自农业农村部第45周（11/2—11/8）全国批发市场周均价，两者口径不同，不能混算。\\n\\n'
        '每周日更新。什么该买，什么该等。\\n'
    )
    (OUT/'公众号文章.md').write_text(article,encoding='utf-8')

    notes = (
        '# 本期发布说明 · '+t+'\\n\\n'
        '1. 先发布视频号，再在公众号编辑器插入对应视频。\\n'
        '2. 视频号封面用3x4版，公众号封面用横版。\\n'
        '3. 公众号正文：导语 → 视频 → 开海降价 → 不是全都便宜 → 季节规律 → 油价 → 长图 → 地址 → 口径。\\n'
        '4. 网站“阅读原文”填 https://honestfoxXXX.github.io/price-temperature/ 。\\n'
        '5. 按发布平台实际选项声明AI复刻配音/AI配乐；不承诺标注对推荐量的影响。\\n'
        '6. 零售价（人民日报）与批发周均价（农业部）口径不同，文中分开标注。\\n'
        '7. 未操作视频号/公众号账号，尚未替用户发布。\\n\\n'
        '## 视频号短标题\\n梭子蟹三十多一斤\\n\\n'
        '## 视频号描述\\n'
        '开海之后大众海鲜便宜了：梭子蟹 30—60 元一斤，国庆还要六七十；波士顿龙虾从 150 跌到 60。\\n'
        '但不是全都便宜——大带鱼 +1.1%、大黄花鱼 +0.2% 反而在涨。\\n'
        '9月开海最便宜，春节最贵，现在正是好时候。\\n'
        '顺带：92号汽油降了 0.51 元/升。\\n'
        '#海鲜 #梭子蟹 #菜篮子 #生活成本\\n'
    )
    (OUT/'发布说明.md').write_text(notes,encoding='utf-8')
    print('Covers and simple article ready')


"""
s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('assets() rewritten for seafood')
