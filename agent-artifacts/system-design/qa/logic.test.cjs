// Executes the actual course script with a minimal DOM adapter. This is NOT a layout test.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');const root=path.dirname(__dirname);
const html=fs.readFileSync(path.join(root,'system-design.html'),'utf8');
const code=html.match(/<script>([\s\S]*)<\/script>/)[1];
function runtime(saved=null,unavailable=false,legacy=null){
 const elements=new Map(),store=new Map(saved?[['sd-course-v2',JSON.stringify(saved)]]:legacy?[['sd-course-v1',JSON.stringify(legacy)]]:[]);
 class E{constructor(id){this.id=id;this.value='';this.textContent='';this.innerHTML='';this.dataset={};this.style={};this.listeners={};this.classList={remove(){},toggle(){return false;}};this.open=false;}
  addEventListener(n,f){this.listeners[n]=f;}setAttribute(n,v){this[n]=v;}focus(){}select(){}showModal(){this.open=true;}close(){this.open=false;}getBoundingClientRect(){return{height:70};}get validity(){const range={dau:[1,1e9],requests:[1,1e5],peak:[1,1000],latency:[1,1e6],slo:[0,100],days:[1,366],backlog:[0,1e12],incoming:[0,1e9],capacity:[0,1e9],aiRequests:[0,1e9],aiInput:[0,1e7],aiOutput:[0,1e7],aiInputRate:[0,1e6],aiOutputRate:[0,1e6],aiCalls:[0,1000],aiAccepted:[0,100],aiFixed:[0,1e12]}[this.id];return{valid:!!range&&Number(this.value)>=range[0]&&Number(this.value)<=range[1]};}}
 const defaults={dau:1000000,requests:20,peak:8,latency:200,slo:99.9,days:30,backlog:1800000,incoming:1000,capacity:1500,aiRequests:100000,aiInput:2000,aiOutput:400,aiInputRate:100,aiOutputRate:400,aiCalls:1.15,aiAccepted:80,aiFixed:150000};
 function el(s){if(!elements.has(s)){const e=new E(s.replace(/^#/,''));if(e.id in defaults)e.value=String(defaults[e.id]);elements.set(s,e);}return elements.get(s);}
 const ctx={console,Number,String,JSON,Date,Math,Array,Object,Set,Error,innerWidth:390,location:{hash:''},history:{replaceState(){}},navigator:{},URL,Blob,setTimeout,ResizeObserver:class{observe(){}},localStorage:{getItem(k){if(unavailable)throw Error('denied');return store.get(k)||null;},setItem(k,v){if(unavailable)throw Error('denied');store.set(k,v);}},document:{querySelector:el,querySelectorAll(s){return s==='.calc input'?Object.keys(defaults).map(k=>el('#'+k)):[];},addEventListener(){},documentElement:{dataset:{},style:{setProperty(){}}},body:{classList:{remove(){},toggle(){return false;}}}}};ctx.window={addEventListener(){},scrollTo(){}};vm.createContext(ctx);vm.runInContext(code,ctx);return{ctx,el,store,eval:s=>vm.runInContext(s,ctx)};
}
let r=runtime();assert.match(r.el('#sloResult').textContent,/43,2/);assert.match(r.el('#queueResult').textContent,/60 минут/);
r.el('#capacity').value='1000';r.el('#capacity').listeners.input();assert.match(r.el('#queueResult').textContent,/не догонит/);
r.el('#capacity').value='999';r.el('#capacity').listeners.input();assert.match(r.el('#queueResult').textContent,/не догонит/);
r.el('#backlog').value='0';r.el('#capacity').listeners.input();assert.match(r.el('#queueResult').textContent,/пуста/);
r.el('#dau').value='-1';r.el('#dau').listeners.input();assert.match(r.el('#loadResult').textContent,/допустимые/);
r.el('#dau').value='';r.el('#dau').listeners.input();assert.match(r.el('#loadResult').textContent,/допустимые/);
r.el('#slo').value='101';r.el('#slo').listeners.input();assert.match(r.el('#sloResult').textContent,/Введите/);
for(let i=0;i<13;i++){
 const out=r.eval('moduleHTML(COURSE['+i+'])');assert(!out.includes('undefined'));assert.match(out,/Ваше решение/);assert.equal((out.match(/class="feedback" role="status" hidden/g)||[]).length,r.eval('COURSE['+i+'].quiz.length'));
}
r.eval("state.notes['sd-01']='мой ответ <script>bad()</script>';state.notes['sd-01-recall']='по памяти';state.done['sd-01']=true;save();exportPortfolio()");
let p=JSON.parse(r.el('#portfolioText').value);assert.equal(p.modules.length,13);assert.equal(p.modules[0].recall,'по памяти');assert(r.el('#portfolio').open);assert.equal(p.modules[0].work,'мой ответ <script>bad()</script>');
const saved=JSON.parse(r.store.get('sd-course-v2'));let restored=runtime(saved);assert.equal(restored.eval("state.notes['sd-01']"),p.modules[0].work);assert.equal(restored.eval("state.done['sd-01']"),true);
assert.equal(r.eval("escapeHTML('<script>')"),'&lt;script&gt;');
const corrupt=runtime({module:'missing',notes:[],checks:'bad',theme:'wrong'});assert.equal(corrupt.eval('state.module'),'home');assert.equal(corrupt.eval('state.theme'),'light');
const denied=runtime(null,true);assert.match(denied.el('#storageStatus').textContent,/недоступно/);denied.eval("state.notes['sd-01']='still in memory';exportPortfolio()");assert.equal(JSON.parse(denied.el('#portfolioText').value).modules[0].work,'still in memory');
console.log('PASS: actual JS script; calculators, invalid inputs, thirteen module render strings, hidden explanations, portfolio, state restoration, corrupt/denied storage, escaped user text. Browser layout NOT tested.');

assert.match(r.el('#aiResult').textContent,/191.?400/);assert.match(r.el('#aiResult').textContent,/2,39/);
r.el('#aiAccepted').value='0';r.el('#aiAccepted').listeners.input();assert.match(r.el('#aiResult').textContent,/не определена/);
r.el('#aiRequests').value='0';r.el('#aiRequests').listeners.input();assert.match(r.el('#aiResult').textContent,/150.?000/);
r.el('#aiAccepted').value='101';r.el('#aiAccepted').listeners.input();assert.match(r.el('#aiResult').textContent,/допустимые/);
const legacyState={module:'sd-10',notes:{'sd-10':'legacy capstone','sd-01-recall':'старое'},checks:{'sd-01':[true]},answers:{'sd-01-0':2},done:{'sd-01':true},theme:'dark'};
const migrated=runtime(null,false,legacyState);assert.equal(migrated.eval("state.notes['sd-10']"),'legacy capstone');assert.equal(migrated.eval("state.module"),'sd-10');assert.equal(migrated.eval("state.legacyDone['sd-01']"),true);assert.equal(migrated.eval('Object.keys(state.answers).length'),0);assert.equal(migrated.eval('Object.keys(state.done).length'),0);assert.equal(migrated.eval('state.theme'),'dark');assert.match(migrated.el('#storageStatus').textContent,/Перенесены/);assert.deepEqual(JSON.parse(migrated.store.get('sd-course-v1')),legacyState);
const newState=JSON.parse(migrated.store.get('sd-course-v2')),migratedReload=runtime(newState);assert.equal(migratedReload.eval("state.notes['sd-10']"),'legacy capstone');assert.equal(migratedReload.eval("state.legacyDone['sd-01']"),true);
assert.equal(r.eval('COURSE[COURSE.length-1].id'),'sd-10');assert.equal(r.eval('TOTAL_HOURS'),26);assert.equal(r.eval('TOTAL_DAYS'),7);
r.eval("state.done={};state.done['sd-01']=true;toc()");assert.equal(r.el('.progress')['aria-valuemax'],13);assert.match(r.el('#progressText').textContent,/1 из 13/);assert(Math.abs(parseFloat(r.el('#progressFill').style.width)-100/13)<0.01);
for(let i=9;i<13;i++){const x=r.eval('moduleHTML(COURSE['+i+'])');assert(!x.includes('Следующий модуль →')||i<12);if(i===12)assert(x.includes('Открыть портфель'));}
console.log('PASS: AI unit economics, zero results, invalid values, v1→v2 migration with untouched legacy data and cleared revised quiz answers, dynamic 13-module order/progress and 26-hour route.');
