// No animation or persisted progress: readers control each diagram at their own pace.
function visualTransition(current,action,total){
  let next={mode:current.mode==='all'?'all':'steps',index:Math.max(0,Math.min(total-1,Number.isInteger(current.index)?current.index:0))};
  if(action==='all'||action==='steps')next.mode=action;
  else if(action==='prev')next={mode:'steps',index:Math.max(0,next.index-1)};
  else if(action==='next')next={mode:'steps',index:Math.min(total-1,next.index+1)};
  else if(/^step:\d+$/.test(action))next={mode:'steps',index:Math.min(total-1,Number(action.slice(5)))};
  return next;
}
function visualLabels(visual){const comparison=visual.presentation==='comparison';return {one:comparison?'Схема':'Шаг',mode:comparison?'По схемам':'По шагам',all:comparison?'Сравнить':'Весь процесс',prev:comparison?'← Предыдущая схема':'← Предыдущий шаг',next:comparison?'Следующая схема →':'Следующий шаг →'};}
function visualExplainersFor(c,section){
  return (DATA.visualExplainers||[]).filter(v=>v.chapter===c.id&&v.afterSection===section).map(v=>`<section class="visual-explainer" data-visual="${v.id}" aria-labelledby="visual-heading-${v.id}"><div class="eyebrow">Увидеть механизм</div><h3 id="visual-heading-${v.id}">${esc(v.title)}</h3><p>${esc(v.intro)}</p><div class="visual-modes" role="group" aria-label="Как смотреть: ${esc(v.title)}"><button data-v-action="steps" aria-pressed="true">${visualLabels(v).mode}</button><button data-v-action="all" aria-pressed="false">${visualLabels(v).all}</button></div><div class="visual-steps" role="group" aria-label="Выбрать шаг">${v.frames.map((f,i)=>`<button data-v-action="step:${i}" aria-pressed="${i===0}"><span>${i+1}</span> ${esc(f.title)}</button>`).join('')}</div><p class="visual-status" data-v-status aria-live="polite" aria-atomic="true">${visualLabels(v).one} 1 из ${v.frames.length}: ${esc(v.frames[0].title)}</p>${v.frames.map((f,i)=>`<figure class="visual-frame" data-v-frame="${i}" ${i?'hidden':''}><div class="visual-scroll" tabindex="0" role="region" aria-label="${esc(f.title)}. Схему можно прокрутить горизонтально"><svg xmlns="http://www.w3.org/2000/svg" viewBox="${esc(f.viewBox)}" role="img" aria-labelledby="visual-title-${v.id}-${i}" aria-describedby="visual-desc-${v.id}-${i}"><title id="visual-title-${v.id}-${i}">${esc(f.title)}</title><desc id="visual-desc-${v.id}-${i}">${esc(f.description)}</desc>${f.svg}</svg></div><figcaption><strong>${i+1}. ${esc(f.title)}.</strong> ${esc(f.description)}</figcaption></figure>`).join('')}<div class="visual-controls"><button data-v-action="prev" disabled>${visualLabels(v).prev}</button><button data-v-action="next">${visualLabels(v).next}</button></div><p class="visual-takeaway"><strong>Что запомнить.</strong> ${esc(v.takeaway)}</p><p class="visual-caveat"><strong>Условия схемы.</strong> ${esc(v.caveat)}</p></section>`).join('');
}
function bindVisualExplainers(){
  document.querySelectorAll('[data-visual]').forEach(root=>{
    const visual=(DATA.visualExplainers||[]).find(v=>v.id===root.dataset.visual);if(!visual)return;
    let current={mode:'steps',index:0};
    function apply(){
      root.querySelectorAll('[data-v-frame]').forEach(frame=>{frame.hidden=current.mode==='steps'&&Number(frame.dataset.vFrame)!==current.index;});
      root.querySelectorAll('[data-v-action]').forEach(button=>{
        const action=button.dataset.vAction;
        if(action==='all'||action==='steps')button.setAttribute('aria-pressed',String(current.mode===action));
        else if(action.startsWith('step:'))button.setAttribute('aria-pressed',String(current.mode==='steps'&&Number(action.slice(5))===current.index));
        else button.disabled=current.mode==='all'||(action==='prev'?current.index===0:current.index===visual.frames.length-1);
      });
      root.querySelector('[data-v-status]').textContent=current.mode==='all'?'Показаны все схемы: '+visual.frames.length+'.':visualLabels(visual).one+' '+(current.index+1)+' из '+visual.frames.length+': '+visual.frames[current.index].title;
    }
    root.querySelectorAll('[data-v-action]').forEach(button=>{button.onclick=()=>{current=visualTransition(current,button.dataset.vAction,visual.frames.length);apply();};});
    apply();
  });
}
