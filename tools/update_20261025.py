"""One-off verified update. Never promote legacy estimates to current observations."""
import json, pathlib, copy
R=pathlib.Path(__file__).resolve().parents[1]
DAY='2026-10-25'
MOA='https://www.moa.gov.cn/ztzl/nybrl/rlxx/202610/t20261020_6488764.htm'
NBS='https://www.stats.gov.cn/sj/zxfbhjd/202610/t20261014_1965475.html'
def load(p): return json.loads((R/p).read_text(encoding='utf-8'))
def save(p,x):
    t=R/p;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
d=load('data/prices.json');w=load('data/watchlist.json');c=load('data/cpi.json')
archive=R/'data/archive/2026-10-18'
for p in ['prices.json','watchlist.json','cpi.json','history.json']:
    dest=archive/p
    if not dest.exists(): save(str(dest.relative_to(R)),load('data/'+p))
food={'pork':(15.83,-.6,-12.6,'猪肉'),'beef':(73.37,.7,11.2,'牛肉'),'lamb':(67.69,.2,9.5,'羊肉'),'chicken':(17.07,.2,-3.2,'白条鸡'),'egg':(9.64,-4.3,28.5,'鸡蛋'),'veg':(4.29,-1.2,-14.5,'28种蔬菜均价'),'fruit':(6.68,.8,-5.4,'6种水果均价'),'fish':(17.25,.1,None,'草鱼')}
for cat in d['categories']:
    cat['blurb']='本期已核实条目见卡片；其余保留目录，待取得可追溯来源后更新。'
    for it in cat['items']:
        it['verified']=it['id'] in food
        if not it['verified']:
            it['verificationNote']='历史录入，未在本期取得逐项可追溯证据；不作为当前报价、历史分位或购买建议。'
            continue
        price,change,yoy,name=food[it['id']]
        it.update(price=price,mom=change,yoy=yoy,verdict='neutral',quality='官方',asOf='2026-10-18',name=name,spec='全国批发市场 · 周均价',source='农业农村部第42周原文（10/12—10/18）',sourceUrl=MOA,changeBasis='周环比',period='2026-10-12—2026-10-18',reason='已核实周度批发数据，不代表本地零售价，也不预测下周。',note='10月19日发布，第42周（10/12—10/18）全国批发周均价；元/公斤按0.5折为元/斤。'+('同比未在本文对应草鱼段给出，不填。' if yoy is None else '同比与上年同期比较。'))
        it.pop('priceText',None)
m=d['meta'];m.update(period='2026-10-25 核验更新',asOf=DAY,headline='鸡蛋周跌<em>4.3%</em>，同比却涨<em>28.5%</em>。',lede='最新可核实农业周报为第42周（10/12—10/18，10/19发布），不是10/25当周现价。本期更新8项批发价；62项历史条目标为待核验，不沿用旧结论。',summary='同一个鸡蛋，周环比下降4.3%，同比上涨28.5%。比较基期不同，不矛盾。本期先纠错、再更新；不把月度同比称为一周暴涨。',auditNote='更正：上期“存储设备一个月涨46.7%”表述有误。国家统计局9月原文为同比+46.7%、环比+1.7%；平板电脑同比+23.6%、环比+1.5%。对无充分证据的五年分位、四年涨价推导和绝对化购买建议，本期停止展示。',readme='核验日2026-10-25，不等于所有条目的统计期。8项本期核实批发周均价；62项历史资料待核验，隐藏旧报价和建议。周环比、月环比、同比均单独标注。批发价不等于本地零售价。',auditMode=True)
m['action']={'buy':[{'id':i,'note':n} for i,n in [('egg','周跌4.3% · 同比涨28.5%'),('veg','周跌1.2% · 28种均价'),('pork','周跌0.6% · 批发'),('fish','周涨0.1% · 草鱼')]],'wait':[{'id':i,'note':n} for i,n in [('beef','周涨0.7%'),('lamb','周涨0.2%'),('chicken','周涨0.2%'),('fruit','周涨0.8% · 6种均价')]],'must':[{'id':i,'note':'历史资料待核验，暂不下购买结论'} for i in ['down','vip','gpu','ddr5']]}
m['changelog'].insert(0,{'date':DAY,'text':'打开官方原文逐项核验：更新第42周8项批发周均价；纠正CPI同比误写环比；62项历史报价及分位暂不发布；不伪造第43周数据。'})
d['sources']=[{'name':'农业农村部：2026年第42周市场动态（10/19发布）','url':MOA},{'name':'国家统计局：2026年9月CPI原文（同比/环比分列）','url':NBS}]
save('data/prices.json',d)
# Build monitor pool only from figures explicitly in the opened official report.
changes={'青椒':-6.6,'大白菜':-6.1,'平菇':-5.8,'菠菜':-5.0,'土豆':0,'蒜苔':1.9,'黄瓜':1.8,'茄子':1.5,'南瓜':1.3,'大蒜':1.1,'西葫芦':1.0,'白鲢鱼':1.4,'鲫鱼':.5,'鲤鱼':.2,'草鱼':.1,'大黄花鱼':-1.5,'花鲢鱼':-1.4,'大带鱼':-.4,'西瓜':4.8,'巨峰葡萄':2.7,'菠萝':-.9,'香蕉':-.6,'鸭梨':-.2,'富士苹果':-.1}
watch=[]
for i,(name,v) in enumerate(changes.items()):
    watch.append(dict(id='weekly42-'+str(i),name=name,cat='meat' if '鱼' in name else 'produce',mom=v,yoy=None,changeBasis='周环比',period='10/12—10/18',note='第42周批发周均价较上周变化。不是零售报价。',source='农业农村部第42周',sourceUrl=MOA,quality='官方',asOf='2026-10-18'))
for i,(name,mom,yoy) in enumerate([('数据存储设备',1.7,46.7),('平板电脑',1.5,23.6),('计算机',2.0,21.8),('移动电话机',3.7,14.9)]):
    watch.append(dict(id='cpi202609-'+str(i),name=name,cat='digital',mom=mom,yoy=yoy,changeBasis='月环比',period='2026年9月',note='9月CPI分项指数变化；不是当周变化，不等于某品牌型号涨幅。',source='国家统计局9月CPI解读',sourceUrl=NBS,quality='官方',asOf='2026-09-30'))
save('data/watchlist.json',{'meta':{'period':'第42周批发数据 + 9月CPI分项','verifiedAt':DAY,'note':'不同统计期不可直接排名为同一周涨跌幅。'},'items':watch})
for row in c['rows']:
    fixes={'数据存储设备':(1.7,46.7),'平板电脑':(1.5,23.6),'计算机':(2.,21.8)}
    if row['name'] in fixes: row['mom'],row['yoy']=fixes[row['name']]
c['meta'].update(url=NBS,verifiedAt=DAY,note='仅核对本表选取的CPI分项，并非穷尽全部消费品类。')
save('data/cpi.json',c)
report={'verifiedAt':DAY,'sources':[MOA,NBS],'weeklyPeriod':'2026-10-12—2026-10-18','weeklyPublishedAt':'2026-10-19','monthlyPeriod':'2026-09','corrections':m['auditNote'],'verifiedPriceItems':list(food),'pendingLegacyItems':62,'notClaimed':['未找到第43周可核实原文','不把9月月报当成10月周度','无可核对4年序列，不宣称官方价+4年涨幅结论','不将反推锚点认作真实逐月观测']}
save('data/verification-2026-10-25.json',report)
print('Updated: 8 verified prices, 62 pending, %d monitor signals; old data archived'%len(watch))
