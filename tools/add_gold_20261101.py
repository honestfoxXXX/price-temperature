"""Add a verified gold/precious-metal category (2026-11-01) and fix card copy for price-only items."""
import json, pathlib

R = pathlib.Path(__file__).resolve().parents[1]
MEM = 'https://www.ceweekly.cn/finance/banking/2026/1027/502033.html'
SGE = 'https://www.sge.com.cn/sjxx/Au99_99'

d = json.loads((R / 'data/prices.json').read_text(encoding='utf-8'))
cat = {
    'id': 'gold', 'name': '金银珠宝', 'icon': '💍',
    'blurb': '金价年内大幅回落，同样一克金差价能到三百多元',
    'items': [
        {'id': 'gold-spot', 'name': '原料金', 'spec': '上金所 Au99.99 · 午盘',
         'unit': '元/克', 'price': 860.04, 'mom': None, 'yoy': None, 'pct5': 0,
         'verdict': 'neutral', 'quality': '官方',
         'reason': '交易所原料金价，是所有金饰报价的基础',
         'note': '行情日期 2026-10-30，上海金午盘价。早盘为 860.04、午盘 854.18，取早盘口径写入。',
         'source': '上海黄金交易所 2026-10-30', 'sourceUrl': SGE,
         'asOf': '2026-10-30', 'verified': True, 'changeBasis': '克价', 'period': '2026-10-30'},
        {'id': 'gold-jewelry', 'name': '金饰', 'spec': '批发市场 · 克价',
         'unit': '元/克', 'price': 1010, 'mom': None, 'yoy': None, 'pct5': 0,
         'verdict': 'neutral', 'quality': '媒体',
         'reason': '年内最高到过 1700 元/克，现在 1010',
         'note': '北京水贝 10 月 26 日报价。品牌店零售价更高，如老庙当日 1200 元/克；工费和品牌溢价另计。',
         'source': '中国证券报（经济网转载）2026-10-27', 'sourceUrl': MEM,
         'asOf': '2026-10-26', 'verified': True, 'changeBasis': '克价', 'period': '2026-10-26'},
        {'id': 'platinum', 'name': '铂金首饰', 'spec': '批发市场 · 克价',
         'unit': '元/克', 'price': 395, 'mom': None, 'yoy': None, 'pct5': 0,
         'verdict': 'neutral', 'quality': '媒体',
         'reason': '最高曾破 700，现在腰斩',
         'note': '2025 年初不足 300 元/克，今年最高突破 700，10 月 26 日回落到 395。',
         'source': '中国证券报（经济网转载）2026-10-27', 'sourceUrl': MEM,
         'asOf': '2026-10-26', 'verified': True, 'changeBasis': '克价', 'period': '2026-10-26'},
    ],
}
d['categories'] = [c for c in d['categories'] if c['id'] != 'gold'] + [cat]
d['meta']['verifiedCount']=11
d['meta']['changelog'].insert(0, {
    'date': '2026-11-01',
    'text': '新增「金银珠宝」品类：上金所原料金、批发市场金饰与铂金克价，来源可追溯；补上非农产品目。'})
d['meta']['summary'] = ('农产品批发价格200指数 111.63，比前一周降 1.73 点。菜肉蛋果这周全跌。'
                        '另一边，金饰克价从年内最高 1700 元跌到 1010 元，铂金从 700 跌到 395。')
(R / 'data/prices.json').write_text(
    json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Card copy: items that only carry a per-unit price should show the data date, not a fake 环比/同比.
t = R / 'template/index.template.html'
s = t.read_text(encoding='utf-8')
old = "'<div class=\"d\"><span>'+(known?'周环比 '+(pct(it.mom)||'—')+' · 同比 '+(pct(it.yoy)||'未给出'):'暂不展示旧报价、五年分位和购买建议')+'</span></div>'+"
new = ("'<div class=\"d\"><span>'+(known?(("
       "(it.mom===null||it.mom===undefined)&&(it.yoy===null||it.yoy===undefined)"
       ")?'克价 · 数据时点 '+it.asOf:"
       "'周环比 '+(pct(it.mom)||'—')+' · 同比 '+(pct(it.yoy)||'未给出')):"
       "'暂不展示旧报价、五年分位和购买建议')+'</span></div>'+")
assert old in s, 'card line not found'
s = s.replace(old, new)
t.write_text(s, encoding='utf-8')
print('gold category added; total categories =', len(d['categories']))
