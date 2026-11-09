// Executes actual production JS with fake DOM. It is NOT a browser/layout test.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.dirname(__dirname),html=fs.readFileSync(path.join(root,'template.html'),'utf8').replace('__VISUAL_EXPLAINERS_JS__',fs.readFileSync(path.join(root,'visual-explainers.js'),'utf8'));
const sample={id:'ch-01',arc:1,title:'Глава',wordCount:1500,briefing:'Условия',goals:['Цель'],sections:Array.from({length:5},(_,i)=>({title:'Раздел '+i,html:'<p>Теория</p>'})),diagrams:[],workedExample:{title:'Пример',html:'<p>Разбор</p>'},expedition:{world:'money',title:'Мир',html:'<p>Деньги</p>',transfer:['x'],distinct:['y']},decision:{prompt:'Выбор',options:[{title:'A',consequence:'C',tradeoff:'T'},{title:'B',consequence:'D',tradeoff:'U'}],recommended:0,explanation:'Контекст'},exercise:{prompt:'Задание',model:'<p>Разбор</p>',rubric:['Критерий']},checkpoint:[{question:'Q',options:['A','B'],answer:0,explanation:'Почему A'},{question:'R',options:['C','D'],answer:1,explanation:'Почему D'}],sources:[]};
const data={chapters:Array.from({length:32},(_,i)=>({...sample,id:'ch-'+String(i+1).padStart(2,'0'),arc:Math.floor(i/4)+1})),worlds:'money inventory search geo collaboration media telemetry saas'.split(' ').map(id=>({id,title:id,briefing:'Мир',sections:[]}))};
const script=html.match(/<script>([\s\S]*)<\/script>/)[1].replace('__COURSE_DATA__',JSON.stringify(data));
function runtime(saved={},denied=false,hash='home',code=script){
 const elements=new Map(),store=new Map(Object.entries(saved)),events={};
 class E{constructor(id){this.id=id;this.value='';this.textContent='';this.innerHTML='';this.dataset={};this.style={};this.classList={remove(){},toggle(){}};}setAttribute(k,v){this[k]=v;}focus(){}select(){}showModal(){this.open=true;}close(){this.open=false;}addEventListener(k,f){this['on'+k]=f;}querySelectorAll(){return [];}click(){this.clicked=true;}}
 const el=s=>{if(!elements.has(s))elements.set(s,new E(s));return elements.get(s);};
 const ctx={console,URL:{createObjectURL(){return 'blob:test'},revokeObjectURL(){}},Blob,navigator:{},location:{hash:'#'+hash},setTimeout:f=>{f();return 1;},clearTimeout(){},localStorage:{getItem(k){if(denied)throw Error('denied');return store.get(k)??null},setItem(k,v){if(denied)throw Error('denied');store.set(k,v)}},document:{addEventListener(k,f){events['document-'+k]=f;},querySelector:el,querySelectorAll:s=>{const defs={'[data-note]':[['note-personal',{note:'personal'}],['note-exercise',{note:'exercise'}]],'[data-decision]':[['decision-0',{decision:'0'}],['decision-1',{decision:'1'}]],'[data-check]':[['check-0',{check:'0'}],['check-1',{check:'1'}]]};return (defs[s]||[]).map(([id,ds])=>{const e=el(id);e.dataset=ds;return e;});},getElementById:el,createElement:()=>new E('a'),activeElement:null,body:{classList:{toggle(){}}}},window:{scrollY:100,scrollTo(){},addEventListener(k,f){events[k]=f}}};vm.createContext(ctx);vm.runInContext(code,ctx);return {el,store,eval:s=>vm.runInContext(s,ctx),events};
}
let r=runtime({'sd-course-v1':'{"done":{"ch-01":true}}','sd-course-v2':'old-v2'});
const controls=runtime();
controls.eval(`
 DATA.visualExplainers=[{id:'demo',frames:[{title:'Первый'},{title:'Второй'},{title:'Третий'}]}];
 globalThis.visualButtons=['steps','all','step:0','step:1','step:2','prev','next'].map(action=>({dataset:{vAction:action},disabled:false,setAttribute(k,v){this[k]=v;}}));
 globalThis.visualFrames=[0,1,2].map(index=>({dataset:{vFrame:String(index)},hidden:false}));
 globalThis.visualStatus={textContent:''};
 globalThis.visualRoot={dataset:{visual:'demo'},querySelectorAll(selector){return selector==='[data-v-frame]'?visualFrames:visualButtons;},querySelector(){return visualStatus;}};
 document.querySelectorAll=selector=>selector==='[data-visual]'?[visualRoot]:[];
 bindVisualExplainers();
`);
const visibility=()=>JSON.parse(controls.eval('JSON.stringify(visualFrames.map(frame=>frame.hidden))'));
assert.deepEqual(visibility(),[false,true,true]);
assert(controls.eval('visualButtons[5].disabled'));
controls.eval('visualButtons[6].onclick()');
assert.deepEqual(visibility(),[true,false,true]);
assert(controls.eval('visualStatus.textContent').includes('Шаг 2 из 3'));
assert.equal(controls.eval("visualButtons[3]['aria-pressed']"),'true');
controls.eval('visualButtons[6].onclick()');
assert(controls.eval('visualButtons[6].disabled'));
controls.eval('visualButtons[1].onclick()');
assert.deepEqual(visibility(),[false,false,false]);
assert(controls.eval('visualButtons[5].disabled&&visualButtons[6].disabled'));
controls.eval('visualButtons[2].onclick()');
assert.deepEqual(visibility(),[false,true,true]);
assert.equal(controls.eval("visualButtons[0]['aria-pressed']"),'true');
assert.equal(controls.eval("visualTransition({mode:'steps',index:0},'prev',3).index"),0);
assert.equal(controls.eval("visualTransition({mode:'steps',index:2},'next',3).index"),2);
assert.equal(controls.eval("visualTransition({mode:'steps',index:0},'step:999',3).index"),2);
r.eval('bindChapter(DATA.chapters[0])');r.el('note-personal').value='Через событие';r.el('note-personal').oninput();assert.equal(r.eval("state.notes['ch-01'].personal"),'Через событие');r.el('decision-1').onclick();assert.equal(r.eval("state.decisions['ch-01']"),1);r.el('#bookmark').onclick();assert.equal(r.eval("state.bookmarks['ch-01']"),true);r.el('input[name="q0"]:checked').value='0';r.el('check-0').onclick();assert(r.el('#checkFeedback0').innerHTML.includes('Верно'));assert.equal(r.eval('Object.keys(state.done).length'),0);r.eval('save()');assert.equal(r.store.get('sd-course-v2'),'old-v2');assert.equal(r.store.get('sd-course-v1'),'{"done":{"ch-01":true}}');assert(r.store.has('sd-journey-v3'));
for(let i=0;i<32;i++){let output=r.eval(`chapter(DATA.chapters[${i}])`);assert(!output.includes('undefined'));assert(output.includes('Проверка понимания'));assert(!output.includes('Почему A'));}
r.eval("state.notes['ch-01']={personal:'<script>evil()</script>\\nПривет',exercise:'Ответ'};state.decisions['ch-01']=1;state.bookmarks['ch-01']=true;state.checks['ch-01']={0:{choice:1,confirmed:true}};state.done['ch-01']=true;save()");
assert(r.eval('notes()').includes('&lt;script&gt;'));assert(!r.eval('notes()').includes('<script>'));
r.eval('decisionFeedback(DATA.chapters[0]);checkFeedback(DATA.chapters[0],0)');assert(r.el('#decisionFeedback').innerHTML.includes('Цена и условия'));assert(r.el('#checkFeedback0').innerHTML.includes('пересмотреть'));
let portfolio=JSON.parse(r.eval('JSON.stringify(portfolio())'));assert.equal(portfolio.state.notes['ch-01'].personal,'<script>evil()</script>\nПривет');assert.equal(portfolio.state.bookmarks['ch-01'],true);assert.equal(portfolio.state.decisions['ch-01'],1);assert.equal(portfolio.oldRaw['sd-course-v2'],'old-v2');
let restored=runtime(Object.fromEntries(r.store));assert.equal(restored.eval("state.notes['ch-01'].exercise"),'Ответ');
let fallback=runtime({},true);assert(fallback.el('#warning').textContent.includes('недоступно'));fallback.eval("state.notes['ch-01']={personal:'В памяти'};save()");assert.equal(fallback.eval("portfolio().state.notes['ch-01'].personal"),'В памяти');
for(const bad of ['null','[]','{"done":null,"notes":null,"decisions":{"ch-01":99},"checks":null,"bookmarks":null}']){let safe=runtime({'sd-journey-v3':bad});assert.doesNotThrow(()=>safe.eval('chapter(DATA.chapters[0]);decisionFeedback(DATA.chapters[0])'));}
let pos=runtime({},false,'ch-01');pos.eval("state.positions['ch-01']=650;ignoreScrollUntil=Date.now()+1000");pos.events.scroll();pos.eval('flushPosition()');assert.equal(pos.eval("state.positions['ch-01']"),650);pos.eval("pendingPosition={id:'ch-01',pos:777};location.hash='#ch-02';render()");assert.equal(pos.eval("state.positions['ch-01']"),777);pos.eval("pendingPosition={id:'ch-02',pos:888};window.bookSavePosition()");assert.equal(pos.eval("state.positions['ch-02']"),888);pos.eval("pendingPosition={id:'ch-02',pos:999}");pos.events.pagehide();assert.equal(pos.eval("state.positions['ch-02']"),999);pos.eval("pendingPosition={id:'ch-02',pos:1001};document.visibilityState='hidden'");pos.events['document-visibilitychange']();assert.equal(pos.eval("state.positions['ch-02']"),1001);
console.log('PASS actual JS: 32 render strings, no eager checkpoint reveal, escaping, notes/decisions/checks/bookmarks export+restore, old-progress isolation, denied/corrupt storage. Browser layout NOT_RUN.');

if(fs.existsSync(path.join(root,'system-design.html'))){
 const built=fs.readFileSync(path.join(root,'system-design.html'),'utf8').match(/<script>([\s\S]*)<\/script>/)[1];const actual=runtime({},false,'home',built);
 assert.equal(actual.eval('DATA.chapters.length'),32);assert.equal(actual.eval('DATA.worlds.length'),8);
 assert.equal(actual.eval('DATA.storyStages.length'),8);
 assert.equal(actual.eval('DATA.storyArt.scenes.length'),28);
 assert.equal(actual.eval("DATA.storyArt.scenes.filter(s=>s.kind==='spot').length"),16);
 let spotCount=0;
 for(let i=0;i<32;i++)for(let section=0;section<6;section++){
  const original=actual.eval(`DATA.chapters[${i}].sections[${section}].html`);
  const rendered=actual.eval(`theoryWithSpots(DATA.chapters[${i}],DATA.chapters[${i}].sections[${section}],${section})`);
  const figures=[...rendered.matchAll(/<figure class="story-scene story-spot"[\s\S]*?<\/figure>/g)];
  spotCount+=figures.length;
  assert.equal(rendered.replace(/<figure class="story-scene story-spot"[\s\S]*?<\/figure>/g,''),original,'Spot changed theory text');
  if(figures.length)assert(rendered.includes('</p><figure class="story-scene story-spot"'),'Spot must be between paragraphs');
 }
 assert.equal(spotCount,16);
 assert.equal(actual.eval('DATA.visualExplainers.length'),10);
 let visualCount=0;
 for(let i=0;i<32;i++){
  const output=actual.eval(`chapter(DATA.chapters[${i}])`);
  const expected=actual.eval(`DATA.visualExplainers.filter(v=>v.chapter===DATA.chapters[${i}].id).length`);
  const rendered=[...output.matchAll(/class="visual-explainer"/g)].length;
  assert.equal(rendered,expected,'Wrong visual explainer placement in chapter '+i);visualCount+=rendered;
 }
 assert.equal(visualCount,10);
 assert.equal(actual.eval('DATA.visualExplainers.reduce((n,v)=>n+v.frames.length,0)'),29);
 let illustrationCount=0;
 for(let i=0;i<32;i++){
  const output=actual.eval(`chapter(DATA.chapters[${i}])`);
  const expected=actual.eval(`DATA.storyArt.scenes.filter(s=>s.chapter===DATA.chapters[${i}].id).length`);
  const rendered=[...output.matchAll(/class="story-scene /g)].length;
  assert.equal(rendered,expected,'Wrong story scene placement in chapter '+i);
  illustrationCount+=rendered;
 }
 assert.equal(illustrationCount,28);
 assert(actual.eval("storyArtFor(DATA.chapters[0],'opening')").includes('data:image/png;base64,'));
 actual.eval("DATA.storyArt.scenes[0].alt='<script>alt</script>';DATA.storyArt.scenes[0].caption='<b>caption</b>'");
 const escapedArt=actual.eval("storyArtFor(DATA.chapters[0],'opening')");
 assert(escapedArt.includes('&lt;script&gt;alt&lt;/script&gt;'));
 assert(escapedArt.includes('&lt;b&gt;caption&lt;/b&gt;'));
 assert(!escapedArt.includes('<script>alt'));
 for(let i=0;i<32;i++){
  const passport=actual.eval(`storyPassport(DATA.chapters[${i}])`);
  assert(passport.includes('Паспорт этапа'));
  assert(passport.includes(actual.eval(`DATA.storyStages[Math.floor(${i}/4)].scale`)));
 }
 actual.eval("DATA.storyStages[0].title='<script>test</script>'");
 assert(actual.eval('storyPassport(DATA.chapters[0])').includes('&lt;script&gt;'));
 assert(!actual.eval('storyPassport(DATA.chapters[0])').includes('<script>'));
 for(let i=0;i<32;i++){const output=actual.eval(`chapter(DATA.chapters[${i}])`);assert(!output.includes('undefined'));const ids=[...output.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size,'Duplicate rendered IDs in chapter '+i);}
 for(let i=0;i<8;i++)assert(!actual.eval(`world(DATA.worlds[${i}])`).includes('undefined'));
 console.log('PASS built artifact: actual 32 chapter render strings and 8 worlds, unique per-page SVG/HTML IDs. Browser layout NOT_RUN.');
}else console.log('Built-artifact data/render check NOT_RUN: system-design.html not yet present.');
