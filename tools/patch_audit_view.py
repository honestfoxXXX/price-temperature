import pathlib
R=pathlib.Path(__file__).resolve().parents[1]
p=R/'template/index.template.html';s=p.read_text(encoding='utf-8')
s=s.replace("document.getElementById('readme').textContent = M.readme;","document.getElementById('readme').textContent = M.readme;\n  if(M.auditNote){document.getElementById('lede').insertAdjacentHTML('afterend','<p style=\"padding:16px;background:#fff0db;border-radius:12px;font-size:13px;line-height:1.8\">'+esc(M.auditNote)+'</p>');}")
s=s.replace("{key:'buy',  title:'现在买划算', cls:'buy'}","{key:'buy',  title:'已核实周度变化', cls:'buy'}").replace("{key:'wait', title:'再忍忍',     cls:'wait'}","{key:'wait', title:'同周上涨',     cls:'wait'}").replace("{key:'must', title:'躲不掉',     cls:'must'}","{key:'must', title:'暂缓结论',     cls:'must'}")
s=s.replace("var lv = level(avgPct(list));","var lv = {cls:'lvl-mid',lbl:list.some(function(x){return x.verified;})?'有已核实数据':'待核验'};")
s=s.replace("var lv = level(avgPct(its));","var lv = {cls:'lvl-mid',lbl:its.some(function(x){return x.verified;})?'已核实 / 待核验':'待核验'};")
start=s.index('  function cardHTML(it){');end=s.index('  /* ---------- render ---------- */',start)
s=s[:start]+'''  function cardHTML(it){
    var p = priceMain(it), known = !!it.verified;
    return '<article class="card'+(known?'':' calm')+'" role="button" tabindex="0" data-id="'+it.id+'"><div class="in">'+
      '<div class="head"><span class="ic">'+it.icon+'</span><span class="tt"><span class="name">'+esc(it.name)+'</span><span class="spec">'+esc(known?it.spec:'保留目录 · 历史资料待核验')+'</span></span><span class="pill neutral">'+(known?'已核实':'待核验')+'</span></div>'+
      '<div class="p"><b class="num">'+(known?p.text:'待核验')+'</b><i>'+(known?esc(p.unit):'')+'</i>'+(known&&p.alt?'<em class="alt">'+p.alt+'</em>':'')+'</div>'+
      '<div class="d"><span>'+(known?'周环比 '+(pct(it.mom)||'—')+' · 同比 '+(pct(it.yoy)||'未给出'):'暂不展示旧报价、五年分位和购买建议')+'</span></div>'+
      '<p style="font-size:10px;color:#947a67">'+(known?'10/12—10/18 · 批发周均价':'本期未取得可追溯证据，不能视为2026-10-25现价')+'</p></div></article>';
  }

'''+s[end:]
# Modal should not resurrect hidden legacy figures or historical percentile.
s=s.replace("    var v = V[it.verdict] || V.neutral;\n    var p = priceMain(it);\n    var d = diffOf(it);", "    var v = {label:it.verified?'已核实批发数据':it.watch?'已核实监控信号':'待核验',cls:'neutral'};\n    var p = (!it.verified && !it.watch)?{text:'待核验',unit:'',alt:''}:priceMain(it);\n    var d = null;")
s=s.replace("esc(it.reason);", "esc(it.verified||it.watch?it.reason:'历史条目尚未复核，旧结论已暂停。');")
s=s.replace("document.getElementById('m-note').textContent = it.note || '';", "document.getElementById('m-note').textContent = it.verified||it.watch?(it.note||''):'旧报价、涨跌与分位暂无可核查证据，不作为本期现价或购买建议。';")
s=s.replace("'同比 ' + (pct(it.yoy) || '—');", "it.verified||it.watch?'同比 ' + (pct(it.yoy) || '未给出'):'未核验，不下结论';")
s=s.replace("(d ? '对照 ' + d.ref : '') + (it.mom !== null", "(d ? '对照 ' + d.ref : '') + ((it.verified||it.watch) && it.mom !== null")
s=s.replace("'　环比 ' + pct(it.mom)", "'　'+(it.changeBasis||'环比')+' '+pct(it.mom)")
s=s.replace("(typeof it.pct5 === 'number' ? it.pct5 + ' · ' + level(it.pct5).lbl : '未采集')", "'暂无可复核完整序列，不作分位判断'")
s=s.replace("'监控池 ' + (D.watch || []).length + ' 条里，本周变化最大的'", "'已核实信号；周度与月度口径分别标注，非统一周榜'")
s=s.replace("(pct(x.val) || '—') + '</span></li>'", "(x.kind==='yoy'?'同比 ':(it.changeBasis||'环比')+' ')+(pct(x.val)||'—')+' · '+esc(it.period||'')+'</span></li>'")
s=s.replace("(pct(v) || '—') + '</span></li>';", "((it.mom!==null&&it.mom!==undefined)?(it.changeBasis||'环比'):'同比')+' '+(pct(v)||'—')+'</span></li>';")
s=s.replace("tag.textContent = '本期已全部覆盖';", "tag.textContent = '已选分项有对应监控';").replace("head + '本期 CPI 分项里没有未覆盖的品类，之前识别出的 ' + closed.length + ' 个缺口都已转入监控池。'", "head+'本表仅检查已选分项，不代表全部品类已覆盖；9月数据不是本周数据。'")
p.write_text(s,encoding='utf-8')
# Do not render inferred old anchors as an observed price history.
p=R/'tools/build.py';s=p.read_text(encoding='utf-8');s=s.replace('data["history"] = series','data["history"] = {} if meta.get("auditMode") else series');p.write_text(s,encoding='utf-8')
print('Audit presentation patched')
