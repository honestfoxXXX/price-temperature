// 最小 DOM 桩，用于在 Node 里跑 index.html 的渲染逻辑。
const fs = require('fs');
const path = 'D:/价格监控/index.html';
const html = fs.readFileSync(path, 'utf8');

const jsonM = html.match(/<script type="application\/json" id="price-data">([\s\S]*?)<\/script>/);
const jsM = html.match(/<script>([\s\S]*?)<\/script>/);
if (!jsonM || !jsM) { console.error('FAIL: 找不到数据或脚本块'); process.exit(1); }

const D = JSON.parse(jsonM[1]);
const total = D.categories.reduce((n, c) => n + c.items.length, 0);

function makeEl(id) {
  return {
    id, innerHTML: '', textContent: '', value: '', className: '', hidden: true, style: {},
    listeners: {},
    addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); },
    getAttribute() { return null; }, setAttribute() {}, hasAttribute() { return false; },
    querySelectorAll() { return []; }, querySelector() { return makeEl('q'); },
    focus() {}, closest() { return null; }, scrollIntoView() {},
  };
}
const store = {};
// 模拟页面初始状态：搜索框为空、排序下拉默认选中第一项 cat
store['q'] = Object.assign(makeEl('q'), { value: '' });
store['sort'] = Object.assign(makeEl('sort'), { value: 'cat' });
global.document = {
  getElementById(id) {
    if (id === 'price-data') return { textContent: jsonM[1] };
    return store[id] || (store[id] = makeEl(id));
  },
  querySelectorAll() { return []; },
  querySelector() { return makeEl('q'); },
  addEventListener() {},
  activeElement: null,
  body: { style: {} },
};
global.window = {};

try { new Function(jsM[1])(); }
catch (e) { console.error('FAIL: 渲染脚本抛错 ->', e.message); process.exit(1); }

const list = (store['list'] || {}).innerHTML || '';
const act = (store['act'] || {}).innerHTML || '';
const temp = (store['temp'] || {}).innerHTML || '';
const src = (store['sources'] || {}).innerHTML || '';

const count = (s, re) => (s.match(re) || []).length;

const histN = Object.keys(D.history || {}).length;
const sparkN = count(list, /class="spark"/g);

const checks = [
  ['卡片总数 = 条目数', count(list, /<article class="card\b/g) === total, `${count(list, /<article class="card\b/g)} / ${total}`],
  ['走势图 = 有序列的条目', sparkN === histN, `${sparkN} 张 / history ${histN} 条`],
  ['走势图无空路径', !/<path d="" /.test(list), ''],
  ['品类区块 = 10', count(list, /<section class="section"/g) === D.categories.length, `${count(list, /<section class="section"/g)} 个`],
  ['温度块 = 10', count(temp, /<button class="idx"/g) === D.categories.length, `${count(temp, /<button class="idx"/g)} 个`],
  ['行动清单 3 列 12 条', count(act, /<div class="act"/g) === 3 && count(act, /<li data-id=/g) === 12,
    `${count(act, /<div class="act"/g)} 列 / ${count(act, /<li data-id=/g)} 条`],
  ['信源已渲染', count(src, /<li>/g) === D.sources.length, `${count(src, /<li>/g)} / ${D.sources.length}`],
  ['标题已注入', (store['asof'] || {}).textContent === D.meta.asOf, `asOf=${(store['asof'] || {}).textContent}`],
  ['无未替换占位符', !html.includes('__PRICE_DATA__'), ''],
  ['无 undefined/null 泄漏', !/<b[^>]*>(undefined|null)</.test(list) && !/>(undefined|null)</.test(act), ''],
];

let bad = 0;
for (const [name, ok, info] of checks) {
  console.log((ok ? '  [ok] ' : '  [x]  ') + name + (info ? '  ' + info : ''));
  if (!ok) bad++;
}
console.log(bad === 0 ? '\nSMOKE PASS' : `\nSMOKE FAIL (${bad})`);
if (process.env.DUMP) {
  console.log('\n--- 首张卡片 ---\n' + (list.match(/<article[\s\S]*?<\/article>/) || [''])[0]);
  console.log('\n--- 行动清单首列 ---\n' + (act.match(/<div class="act-col">[\s\S]*?<\/div>/) || [''])[0]);
  console.log('\n--- 温度带首块 ---\n' + (temp.match(/<button[\s\S]*?<\/button>/) || [''])[0]);
}
process.exit(bad === 0 ? 0 : 1);
