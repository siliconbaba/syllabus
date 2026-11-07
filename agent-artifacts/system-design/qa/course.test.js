(function(){
 const checks=[];function assert(v,n){if(!v)throw Error(n);checks.push(n);}function go(id){document.querySelector('[data-go="'+id+'"]').click();}function input(id,value){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}));}
 try{
  assert(document.querySelectorAll('#toc [data-go]').length===14,'thirteen modules and overview');
  assert(document.body.textContent.includes('26 часов с практикой'),'duration stated honestly');
  input('search','идемпотент');assert(document.querySelectorAll('#toc [data-go]').length>1,'full content search finds term');input('search','zzzz-no-match');assert(document.querySelectorAll('#toc [data-go]').length===1,'no-match search');input('search','');
  input('dau','86400');input('requests','1');input('peak','1');input('latency','1000');assert(document.getElementById('loadResult').textContent.includes('1 RPS в среднем'),'load calculator units');
  input('dau','-1');assert(document.getElementById('loadResult').textContent.includes('допустимые'),'negative input validation');
  input('slo','99.9');input('days','30');assert(document.getElementById('sloResult').textContent.includes('43,2'),'error budget 43.2 minutes');
  input('capacity','1000');assert(document.getElementById('queueResult').textContent.includes('не догонит'),'queue equal capacity cannot catch up');input('capacity','1500');assert(document.getElementById('queueResult').textContent.includes('60 минут'),'queue catchup net throughput');
  document.querySelector('[data-decision="reconcile"]').click();assert(document.getElementById('decisionResult').textContent.includes('operation_id'),'scenario feedback');
  for(let i=1;i<=13;i++){go('sd-'+String(i).padStart(2,'0'));assert(!!document.querySelector('h1')&&document.querySelectorAll('.lesson').length>=5,'module '+i+' renders');assert(document.documentElement.scrollWidth<=innerWidth+1,'module '+i+' has no page overflow');assert(document.querySelectorAll('.quiz').length>=3,'module '+i+' quizzes present');}
  go('sd-01');input('work','QA: мой ответ <script>window.bad=true</script>');input('recall','QA: вспомнил по памяти');
  assert(!window.bad,'user notes rendered as text');
  const f=document.querySelector('.quiz');assert(f.querySelector('.feedback').hidden,'answer explanation hidden initially');f.querySelector('input[value="1"]').click();assert(f.querySelector('.feedback').hidden,'choice alone does not reveal answer');f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));assert(!f.querySelector('.feedback').hidden,'confirmed answer reveals explanation');
  document.querySelector('[data-check="0"]').click();document.getElementById('complete').click();assert(document.getElementById('progressText').textContent.includes('1 из 13'),'self-reported progress');
  document.getElementById('theme').click();assert(document.documentElement.dataset.theme==='dark','dark theme');
  document.getElementById('export').click();assert(document.getElementById('portfolio').open,'portfolio opens without native download');const portfolio=JSON.parse(document.getElementById('portfolioText').value);assert(portfolio.modules.length===13&&portfolio.modules[0].work.includes('мой ответ'),'portfolio includes all work');document.getElementById('closePortfolio').click();
  assert(JSON.parse(localStorage.getItem('sd-course-v2')).notes['sd-01-recall'].includes('вспомнил'),'recall saved');
  assert((window.__qaErrors||[]).length===0,'no JavaScript runtime errors');window.webkit.messageHandlers.result.postMessage({ok:true,checks});
 }catch(e){window.webkit.messageHandlers.result.postMessage({ok:false,error:String(e),checks});}
})();
