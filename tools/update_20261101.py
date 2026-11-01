"""2026-11-01 update from the verified MOA week-43 report (10/19-10/25)."""
import json, pathlib, shutil

R = pathlib.Path(__file__).resolve().parents[1]
DAY = '2026-11-01'
SRC = 'http://www.agri.cn/sj/jcyj/202610/t20261027_8879242.htm'
NBS = 'https://www.stats.gov.cn/sj/zxfbhjd/202610/t20261014_1965475.html'
PERIOD = '2026-10-19—2026-10-25'
PERIOD_END = '2026-10-25'

def load(p): return json.loads((R / p).read_text(encoding='utf-8'))
def save(p, x):
    t = R / p
    t.parent.mkdir(parents=True, exist_ok=True)
    t.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# archive previous snapshot before overwriting
arch = R / 'data/archive/2026-10-25'
for f in ('prices.json', 'watchlist.json', 'cpi.json'):
    src = R / 'data' / f
    dst = arch / f
    if src.exists() and not dst.exists():
        save(str(dst.relative_to(R)), load('data/' + f))

# name, price 元/公斤, 周环比, 同比
FOOD = {
    'pork': ('猪肉', 15.70, -0.8, -12.1),
    'beef': ('牛肉', 73.04, -0.4, 10.6),
    'lamb': ('羊肉', 67.49, -0.3, 9.4),
    'chicken': ('白条鸡', 16.97, -0.6, -3.6),
    'egg': ('鸡蛋', 9.38, -2.7, 27.1),
    'veg': ('28种蔬菜均价', 4.14, -3.5, -21.7),
    'fruit': ('6种水果均价', 6.65, -0.4, -5.9),
    'fish': ('草鱼', 17.02, -1.3, None),
}
REASON = {
    'egg': '连跌两周，但仍比去年同期贵两成七',
    'veg': '叶菜领跌，菠菜一周便宜了一成',
    'pork': '同比便宜一成二，仍在低位',
    'beef': '本周略跌，但同比仍高一成',
    'fish': '淡水鱼小幅回落',
}

d = load('data/prices.json')
for cat in d['categories']:
    cat['blurb'] = '本期已核实条目见卡片；其余保留目录，待取得可追溯来源后更新。'
    for it in cat['items']:
        it['verified'] = it['id'] in FOOD
        if not it['verified']:
            it['verificationNote'] = '历史录入，未在本期取得逐项可追溯证据；不作为当前报价、历史分位或购买建议。'
            continue
        name, price, mom, yoy = FOOD[it['id']]
        it.update(
            name=name, price=price, mom=mom, yoy=yoy,
            spec='全国批发市场 · 周均价', unit='元/公斤',
            verdict='neutral', quality='官方', asOf=PERIOD_END,
            source='农业农村部第43周原文（10/19—10/25）', sourceUrl=SRC,
            changeBasis='周环比', period=PERIOD,
            reason=REASON.get(it['id'], '已核实周度批发数据，不代表本地零售价。'),
            note='10月27日发布，第43周全国批发周均价；元/公斤按 0.5 折为元/斤。'
                 + ('该文未给出草鱼同比，不填。' if yoy is None else '同比与上年同期比较。'),
        )
        it.pop('priceText', None)

m = d['meta']
m.update(
    period='2026-11-01 核验更新',
    asOf=DAY,
    headline='这周菜价跌得狠，菠菜<em>便宜一成</em>。',
    lede='最新已核实周报为第43周（10/19—10/25，10月27日发布）。28种蔬菜均价一周跌 3.5%，菠菜跌 10.8%、菜花跌 10.2%；鸡蛋连跌两周，同比仍高 27.1%。',
    summary='农产品批发价格200指数 111.63，比前一周降 1.73 点，同比低 12.20 点。菜、肉、蛋、果这周全在跌，但同比口径下鸡蛋仍比去年贵两成七、牛肉贵一成。',
    readme='核验日 2026-11-01，不等于所有条目的统计期。8 项本期核实批发周均价；62 项历史资料待核验，隐藏旧报价和建议。周环比、月环比、同比均单独标注。批发价不等于本地零售价。',
)
m['changelog'].insert(0, {
    'date': DAY,
    'text': '核验第43周（10/19—10/25）原文：更新8项批发周均价（菜价跌3.5%、菠菜跌10.8%、鸡蛋跌2.7%）；10月CPI按发布日程11月9日公布，本期仍沿用9月数据。'})
d['sources'] = [
    {'name': '农业农村部：2026年第43周市场动态（10/27发布）', 'url': SRC},
    {'name': '国家统计局：2026年9月CPI原文（同比/环比分列）', 'url': NBS},
]
save('data/prices.json', d)

# item-level changes quoted in the week-43 report
VEG = {'菠菜': -10.8, '菜花': -10.2, '芹菜': -8.6, '莴笋': -8.2, '生菜': -7.8,
       '平菇': -7.5, '大白菜': -6.5, '油菜': -6.2, '青椒': -5.3, '黄瓜': -5.1,
       '西红柿': 0.0, '南瓜': 1.3, '韭菜': 0.5}
FISH = {'草鱼': -1.3, '鲫鱼': -1.1, '大黄花鱼': -1.1, '鲤鱼': -0.9, '花鲢鱼': -0.3,
        '大带鱼': 1.3, '白鲢鱼': 0.3}
FRUIT = {'菠萝': -3.3, '富士苹果': -1.6, '鸭梨': -0.8, '西瓜': 1.9, '巨峰葡萄': 1.5, '香蕉': 0.4}
watch = []
def add(name, cat, mom, src='农业农村部第43周'):
    watch.append(dict(
        id='w43-%d' % len(watch), name=name, cat=cat, mom=mom, yoy=None,
        changeBasis='周环比', period=PERIOD,
        note='第43周批发周均价较上周变化，不是零售报价。',
        source=src, sourceUrl=SRC, quality='官方', asOf=PERIOD_END))
for k, v in VEG.items(): add(k, 'produce' if k not in ('南瓜',) else 'produce', v)
for k, v in FISH.items(): add(k, 'meat', v)
for k, v in FRUIT.items(): add(k, 'produce', v)
for name, mom, yoy in [('数据存储设备', 1.7, 46.7), ('平板电脑', 1.5, 23.6),
                       ('计算机', 2.0, 21.8), ('移动电话机', 3.7, 14.9)]:
    watch.append(dict(
        id='cpi202609-%d' % len(watch), name=name, cat='digital', mom=mom, yoy=yoy,
        changeBasis='月环比', period='2026年9月',
        note='9月CPI分项指数变化；不是当周变化，也不等于某品牌型号涨幅。',
        source='国家统计局9月CPI解读', sourceUrl=NBS, quality='官方', asOf='2026-09-30'))
save('data/watchlist.json', {
    'meta': {'period': '第43周批发数据 + 9月CPI分项', 'verifiedAt': DAY,
             'note': '不同统计期不可直接排名为同一周涨跌幅。'}, 'items': watch})

c = load('data/cpi.json')
c['meta'].update(
    verifiedAt=DAY,
    note='仅核对本表选取的CPI分项，并非穷尽全部消费品类。10月CPI按发布日程为11月9日，本期仍是9月数据。')
save('data/cpi.json', c)

save('data/verification-%s.json' % DAY, {
    'verifiedAt': DAY,
    'sources': [SRC, NBS],
    'weeklyPeriod': PERIOD,
    'weeklyPublishedAt': '2026-10-27',
    'index200': {'value': 111.63, 'wow': -1.73, 'yoy': -12.20},
    'monthlyPeriod': '2026-09',
    'monthlyNote': '10月CPI按国家统计局发布日程为2026-11-09，本期未引用10月数据。',
    'verifiedPriceItems': list(FOOD),
    'itemLevelChanges': {'veg': VEG, 'fish': FISH, 'fruit': FRUIT},
    'pendingLegacyItems': 62,
    'notClaimed': [
        '未声称第44周（10/26—11/1）已发布',
        '未把9月CPI分项当作10月或当周数据',
        '无可复核完整序列，不宣称五年分位或四年涨幅结论',
    ],
})
print('updated: 8 prices, %d watch rows, week-43 report' % len(watch))
