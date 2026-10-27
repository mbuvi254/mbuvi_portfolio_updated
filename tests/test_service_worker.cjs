const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const events = {};
const cached = [];
const removed = [];
const context = {
  URL,
  self: {location:{origin:'https://portfolio.example'},addEventListener:(event,fn)=>events[event]=fn,skipWaiting:async()=>{},clients:{claim:async()=>{}}},
  caches: {open:async()=>({addAll:async assets=>cached.push(...assets)}),keys:async()=>['flask-pwa-v1','mbuvi-portfolio-brand-v1','mbuvi-portfolio-brand-v3','unrelated-cache'],delete:async name=>removed.push(name),match:async()=> 'offline-page'},
  fetch:async()=>{throw Error('offline');}
};
vm.runInNewContext(fs.readFileSync('static/pwa/sw.js','utf8'),context);
(async()=>{
  let work;
  events.install({waitUntil:p=>work=p}); await work;
  for(const asset of cached) assert.ok(fs.existsSync('.'+asset),`Missing asset ${asset}`);
  assert.ok(!cached.some(asset=>asset.includes('cm.png')));
  events.activate({waitUntil:p=>work=p}); await work;
  assert.deepEqual(removed,['flask-pwa-v1','mbuvi-portfolio-brand-v1']);
  for(const path of ['/dashboard','/dashboard/login','/admin','/admin/login']){
    let intercepted=false;
    events.fetch({request:{url:'https://portfolio.example'+path,method:'GET',mode:'navigate'},respondWith:()=>intercepted=true});
    assert.equal(intercepted,false);
  }
  let response;
  events.fetch({request:{url:'https://portfolio.example/projects',method:'GET',mode:'navigate'},respondWith:p=>response=p});
  assert.equal(await response,'offline-page');
  console.log('Service worker checks passed: assets, cache cleanup, private routes, offline fallback.');
})().catch(error=>{console.error(error);process.exitCode=1;});
