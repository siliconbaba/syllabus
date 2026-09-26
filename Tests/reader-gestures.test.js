(async function () {
  const assert = (ok,label) => {if(!ok)throw Error('Gestures: '+label);};
  const frame = () => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const main=document.querySelector('main'), sidebar=document.getElementById('sidebar');
  function touch(target,type,x,y,count=1) {
    const event=new Event(type,{bubbles:true,cancelable:true});
    Object.defineProperty(event,'touches',{value:type==='touchend'||type==='touchcancel'?[]:Array.from({length:count},()=>({clientX:x,clientY:y}))});
    target.dispatchEvent(event); return event;
  }
  function swipe(target,x,y,endX,endY) {touch(target,'touchstart',x,y);touch(target,'touchmove',endX,endY);touch(target,'touchend',endX,endY);}
  // Establish an exact reading offset, then navigate with the same API used by the TOC.
  getSelection().removeAllRanges();
  window.bookNavigateTo('t-10-1',true);await frame();main.scrollTop+=123;window.bookSavePosition();
  const original=window.bookNavigation.snapshot(), top=main.scrollTop;
  window.bookNavigateTo('t-10-2',true);await frame();const destination=main.scrollTop;
  swipe(main,150,300,270,300);await frame();assert(main.scrollTop===destination,'middle swipe ignored');
  swipe(main,10,300,18,450);await frame();assert(main.scrollTop===destination,'vertical scroll not navigation');
  swipe(main,10,300,45,300);await frame();assert(main.scrollTop===destination,'short swipe ignored');
  touch(main,'touchstart',10,300);touch(main,'touchmove',120,300,2);touch(main,'touchend',120,300);await frame();assert(main.scrollTop===destination,'multitouch ignored');
  touch(main,'touchstart',10,300);touch(main,'touchmove',120,300);touch(main,'touchcancel',120,300);await frame();assert(main.scrollTop===destination,'cancelled gesture ignored');
  const table=document.querySelector('#t-10-2 .tbl-wrap') || document.querySelector('.tbl-wrap');
  swipe(table,10,300,120,300);await frame();assert(main.scrollTop===destination,'table swipe ignored');
  const text=document.querySelector('#t-10-2 p').firstChild,range=document.createRange();range.setStart(text,0);range.setEnd(text,3);getSelection().addRange(range);
  swipe(main,10,300,120,300);await frame();assert(main.scrollTop===destination,'selection preserved');getSelection().removeAllRanges();
  swipe(main,10,300,130,305);await frame();assert(Math.abs(main.scrollTop-top)<2,'edge back restores exact reading position');
  assert(document.body.dataset.filter===original.filter,'back restores filter');
  // Wait out intentional suppression of a synthetic click following the completed swipe.
  await new Promise(r=>setTimeout(r,450));document.getElementById('burger').click();assert(document.body.classList.contains('side-open'),'menu opens');
  swipe(sidebar,220,300,215,450);assert(document.body.classList.contains('side-open'),'menu vertical scroll remains open');
  swipe(sidebar,220,300,90,305);assert(!document.body.classList.contains('side-open'),'menu left swipe closes');
  assert(!main.inert && sidebar.inert,'menu focus/inert state restored');
  assert(Math.abs(main.scrollTop-top)<2,'closing menu preserves position');
  window.webkit.messageHandlers.result.postMessage({ok:true,gestures:true});
})().catch(e=>window.webkit.messageHandlers.result.postMessage({ok:false,error:String(e)}));
