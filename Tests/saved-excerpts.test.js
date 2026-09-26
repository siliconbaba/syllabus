(async function () {
  function assert(ok, label) { if (!ok) throw Error('Saved: ' + label); }
  const topic = document.getElementById('t-10-1'), p = topic.querySelector('p');
  function select(node, a, b) { const r=document.createRange();r.setStart(node,a);r.setEnd(node,b);getSelection().removeAllRanges();getSelection().addRange(r); }
  document.querySelector('#filter [data-f="all"]').click();
  select(p.firstChild, 0, Math.min(30,p.firstChild.length));
  const value=window.bookSaved.payload();
  assert(value && value.topicID===topic.id && value.anchor.startsWith(topic.id+'-block-') && value.text.length>0,'selection payload and metadata');
  const button=document.querySelector('[data-action="save"]');
  button.dispatchEvent(new Event('pointerdown',{bubbles:true,cancelable:true}));
  getSelection().removeAllRanges();button.click();
  select(p.firstChild, 0, Math.min(30,p.firstChild.length));
  const listenButton=document.querySelector('[data-action="listenFrom"]');
  listenButton.dispatchEvent(new Event('pointerdown',{bubbles:true,cancelable:true}));listenButton.click();
  const before=value.anchor;
  assert(window.bookSaved.payload().anchor===before,'deterministic anchor');
  const block=window.bookAudio.selectionBlock(p.firstChild);
  assert(block===value.anchor,'shared Saved/audio/listen semantic ID');
  window.bookAudio.extractTopic(topic.id);
  assert(window.bookAudio.selectionBlock(p.firstChild)===block,'repeat extraction stable');
  document.querySelector('#filter [data-f="head"]').click();
  document.querySelector('#filter [data-f="all"]').click();
  assert(window.bookAudio.selectionBlock(p.firstChild)===block,'filter-stable block ID');
  // Exercise the real native persistence bridge in the standalone WebKit harness.
  window.webkit.messageHandlers.saved.postMessage({action:'save',...value});
  getSelection().removeAllRanges();assert(window.bookSaved.payload()===null,'empty selection');
  const btn=topic.querySelector('button') || document.getElementById('themeBtn');
  select(btn.firstChild,0,btn.firstChild.length);assert(window.bookSaved.payload()===null,'UI selection rejected');
  getSelection().removeAllRanges();
  const hidden=document.createElement('p');hidden.hidden=true;hidden.textContent='скрыто';topic.appendChild(hidden);
  select(hidden.firstChild,0,6);assert(window.bookSaved.payload()===null,'hidden text rejected');hidden.remove();
  const closed=document.createElement('details');closed.innerHTML='<summary>ответ</summary><p>закрыто</p>';topic.appendChild(closed);
  select(closed.querySelector('p').firstChild,0,7);assert(window.bookSaved.payload()===null,'closed answer rejected');closed.remove();
  const other=document.getElementById('t-10-2').querySelector('p');
  const cross=document.createRange();cross.setStart(p.firstChild,0);cross.setEnd(other.firstChild,1);getSelection().removeAllRanges();getSelection().addRange(cross);
  assert(window.bookSaved.payload()===null,'cross-topic rejected');getSelection().removeAllRanges();
  assert(await window.bookSaved.openSource(value)==='anchor','source anchor navigation');
  assert(p.classList.contains('saved-source'),'temporary source highlight');
  assert(await window.bookSaved.openSource({...value,anchor:'missing'})==='anchor','missing anchor text fallback');
  assert(await window.bookSaved.openSource({...value,anchor:'missing',text:'несуществующая цитата'})==='topic','missing anchor topic fallback');
  assert(await window.bookSaved.openSource({...value,topicID:'t-999-999'})==='missingTopic','missing topic retained');
  window.webkit.messageHandlers.result.postMessage({ok:true, saved:true});
})().catch(e=>window.webkit.messageHandlers.result.postMessage({ok:false,error:String(e)}));
