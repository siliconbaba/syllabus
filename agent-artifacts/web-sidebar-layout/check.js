(async function(){
 const wait=async()=>{ await new Promise(r=>setTimeout(r,200)); for(let i=0;i<4;i++)await new Promise(requestAnimationFrame); };
 const checks=[]; function check(name,ok){checks.push({name,ok});if(!ok)throw Error(name);}
 try {
 await wait();
 const main=document.querySelector('main'), sidebar=document.querySelector('.sidebar');
 const topics=[...document.querySelectorAll('.topic[id]')];
 window.bookNavigateTo(topics[30].id,true); await wait();
 const before=window.bookNavigation.snapshot().location;
 document.getElementById('burger').click(); await wait();
 check('separate columns',sidebar.getBoundingClientRect().right<=main.getBoundingClientRect().left+1);
 check('reader remains interactive',!main.inert && document.getElementById('menuBackdrop').hidden);
 check('reading anchor preserved',window.bookNavigation.snapshot().location.id===before.id);
 main.click(); await wait();
 check('text click keeps menu open',document.body.classList.contains('side-open'));
 document.querySelector('#toc a[href="#'+topics[45].id+'"]').click(); await wait();
 check('navigation keeps menu open',document.body.classList.contains('side-open'));
 checks.push({target:topics[45].id,hash:location.hash,top:topics[45].getBoundingClientRect().top,mainTop:main.getBoundingClientRect().top});
 check('correct destination',Math.abs(topics[45].getBoundingClientRect().top-main.getBoundingClientRect().top-16)<3);
 document.getElementById('closeMenu').click();await wait();
 check('explicit close restores reader width',main.getBoundingClientRect().left===0&&!document.body.classList.contains('side-open'));
 check('close preserves topic',window.bookNavigation.snapshot().location.id===topics[45].id);
 window.webkit.messageHandlers.result.postMessage(JSON.stringify({ok:true,checks}));
 }catch(e){window.webkit.messageHandlers.result.postMessage(JSON.stringify({ok:false,error:String(e),checks}));}
})()
