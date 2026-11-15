"""2026-11-15: ingest week-45 produce prices and October CPI."""
import json, pathlib

R = pathlib.Path(__file__).resolve().parents[1]
DAY = '2026-11-15'
MOA = 'https://www.moa.gov.cn/ztzl/nybrl/rlxx/202611/t20261110_6489322.htm'
NBS = 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202611/t20261109_1965795.html'
PERIOD, END = '2026-11-02—2026-11-08', '2026-11-08'

def load(p): return json.loads((R/p).read_text(encoding='utf-8'))
def save(p, x):
    t = R/p; t.parent.mkdir(parents=True, exist_ok=True)
    t.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

arch = R/'data/archive/2026-11-08'
for f in ('prices.json', 'watchlist.json', 'cpi.json'):
    if (R/'data'/f).exists() and not (arch/f).exists():
        save(str((arch/f).relative_to(R)), load('data/'+f))

FOOD = {'pork': ('猪肉', 15.01, -3.1, -16.7), 'beef': ('牛肉', 73.51, 0.3, 10.8),
        'lamb': ('羊肉', 67.59, 0.0, 7.8), 'chicken': ('白条鸡', 17.20, 0.9, -1.9),
        'egg': ('鸡蛋', 9.50, 1.7, 30.9), 'veg': ('28种蔬菜均价', 4.03, -1.7, -29.8),
        'fruit': ('6种水果均价', 6.64, 0.9, -5.8), 'fish': ('草鱼', 16.76, -0.9, None)}
REASON = {'pork': '四周连跌，7.5元一斤', 'egg': '跌了三周后转涨，同比仍高三成',
          'veg': '继续跌，比去年同期便宜近三成', 'fish': '淡水鱼集体回落'}

d = load('data/prices.json')
for cat in d['categories']:
    for it in cat['items']:
        if it['id'] in ('gold-spot','gold-jewelry','platinum'):
            it['verified']=True          # 贵金属条目另有一期核验，不受本期农产品更新影响
            continue
        it['verified'] = it['id'] in FOOD
        if not it['verified']:
            it['verificationNote'] = '历史录入，未在本期取得逐项可追溯证据；不作为当前报价、历史分位或购买建议。'
            continue
        name, price, mom, yoy = FOOD[it['id']]
        it.update(name=name, price=price, mom=mom, yoy=yoy, spec='全国批发市场 · 周均价',
                  unit='元/公斤', verdict='neutral', quality='官方', asOf=END,
                  source='农业农村部第45周原文（11/2—11/8）', sourceUrl=MOA,
                  changeBasis='周环比', period=PERIOD,
                  reason=REASON.get(it['id'], '已核实周度批发数据，不代表本地零售价。'),
                  note='11月9日发布，第45周全国批发周均价；元/公斤按 0.5 折为元/斤。'
                       + ('该文未给出草鱼同比，不填。' if yoy is None else '同比与上年同期比较。'))
        it.pop('priceText', None)

m = d['meta']
m.update(asOf=DAY, period='2026-11-15 更新',
         headline='梭子蟹从<em>六七十</em>降到三十多。',
         lede='开海之后水产品量增价降：梭子蟹 30—60 元/斤，波士顿龙虾从 150 元跌到 60 元；但大带鱼、大黄花鱼反而在涨。同期猪肉四周连跌，7.5 元一斤。',
         readme='核验日 2026-11-15。农产品为第45周（11/2—11/8）批发周均价；CPI 分项为 2026年10月。62 项历史资料待核验，隐藏旧报价和建议。批发价不等于本地零售价。')
m['verifiedCount']=11
m['changelog'].insert(0, {'date': DAY, 'text': '更新第45周农产品：猪肉四周连跌至15.01元/公斤、鸡蛋转涨+1.7%、水产转跌；CPI 换成10月数据。'})
d['sources'] = [{'name': '农业农村部：2026年第45周市场动态（11/9发布）', 'url': MOA},
                {'name': '国家统计局：2026年10月CPI（11/9发布）', 'url': NBS}]
save('data/prices.json', d)

VEG = {'莴笋': -6.0, '芹菜': -5.7, '油菜': 0.0, '黄瓜': 1.9}
FISH = {'鲫鱼': -1.0, '花鲢鱼': -1.0, '草鱼': -0.9, '白鲢鱼': -0.3, '鲤鱼': -0.1,
        '大带鱼': 1.1, '大黄花鱼': 0.2}
FRUIT = {'西瓜': 1.8, '香蕉': 1.4, '鸭梨': 1.4, '巨峰葡萄': 0.6, '菠萝': 0.4, '富士苹果': 0.2}
watch = []
def add(name, cat, mom):
    watch.append(dict(id='w45-%d' % len(watch), name=name, cat=cat, mom=mom, yoy=None,
                      changeBasis='周环比', period=PERIOD,
                      note='第45周批发周均价较上周变化，不是零售报价。',
                      source='农业农村部第45周', sourceUrl=MOA, quality='官方', asOf=END))
for k, v in VEG.items(): add(k, 'produce', v)
for k, v in FISH.items(): add(k, 'meat', v)
for k, v in FRUIT.items(): add(k, 'produce', v)
CPI = [('鲜菜', -5.8, -16.9), ('蛋类', -5.2, 10.1), ('水产品', -1.3, 0.4),
       ('猪肉', None, -8.6), ('交通通信', None, 5.5), ('医疗保健', None, 2.4),
       ('其他用品及服务', None, 1.8), ('居住', None, -0.3)]
for name, mom, yoy in CPI:
    watch.append(dict(id='cpi202610-%d' % len(watch), name=name,
                      cat='digital' if name == '交通通信' else 'meat',
                      mom=mom, yoy=yoy, changeBasis='月环比' if mom is not None else '同比',
                      period='2026年10月',
                      note='10月CPI分项；不是当周变化，也不等于某品牌型号涨幅。',
                      source='国家统计局10月CPI', sourceUrl=NBS, quality='官方', asOf='2026-10-31'))
save('data/watchlist.json', {'meta': {'period': '第45周批发 + 10月CPI', 'verifiedAt': DAY,
                                      'note': '不同统计期不可直接排名为同一周涨跌幅。'}, 'items': watch})

c = load('data/cpi.json')
c['meta'].update(period='2026 年 10 月', source='国家统计局 2026-11-09', url=NBS, verifiedAt=DAY,
                 headline={'yoy': 0.7, 'mom': 0.0},
                 note='10月CPI同比+0.7%、环比持平；仅列本表选取分项，非穷尽。')
c['rows'] = [
    {'name': '鲜菜', 'yoy': -16.9, 'mom': -5.8, 'covered': True, 'why': '周报覆盖'},
    {'name': '蛋类', 'yoy': 10.1, 'mom': -5.2, 'covered': True, 'why': '周报覆盖'},
    {'name': '水产品', 'yoy': 0.4, 'mom': -1.3, 'covered': True, 'why': '周报覆盖'},
    {'name': '猪肉', 'yoy': -8.6, 'mom': None, 'covered': True, 'why': '周报覆盖'},
    {'name': '交通通信', 'yoy': 5.5, 'mom': None, 'covered': True, 'why': '油价传导'},
    {'name': '医疗保健', 'yoy': 2.4, 'mom': None, 'covered': True, 'why': '监控中'},
    {'name': '其他用品及服务', 'yoy': 1.8, 'mom': None, 'covered': True, 'why': '监控中'},
    {'name': '居住', 'yoy': -0.3, 'mom': None, 'covered': True, 'why': '监控中'},
]
save('data/cpi.json', c)
save('data/verification-%s.json' % DAY, {
    'verifiedAt': DAY, 'sources': [MOA, NBS],
    'weeklyPeriod': PERIOD, 'weeklyPublishedAt': '2026-11-09',
    'monthlyPeriod': '2026-10', 'monthlyPublishedAt': '2026-11-09',
    'index200': {'value': 111.15, 'wow': -0.38, 'yoy': -16.67},
    'verifiedPriceItems': list(FOOD), 'pendingLegacyItems': 62})
print('updated: 8 prices, %d watch rows, CPI -> 2026-10' % len(watch))
