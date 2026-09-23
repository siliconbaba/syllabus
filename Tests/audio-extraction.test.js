(function(){
  function assert(value,label){if(!value)throw Error('Audio extraction: '+label);}
  const fixture=document.createElement('article');fixture.className='topic';fixture.id='audio-fixture';
  fixture.innerHTML='<h3>Заголовок аудио</h3><p>API абзац <a href="https://example.org">документация</a>.</p>'+
    '<p hidden>НЕЧИТАТЬ hidden</p><div style="display:none"><p>НЕЧИТАТЬ css</p></div>'+
    '<button>НЕЧИТАТЬ кнопку</button><label class="studied">НЕЧИТАТЬ Изучено</label>'+
    '<pre>НЕЧИТАТЬ код</pre><p>Текст <code>НЕЧИТАТЬ inline</code> после кода.</p>'+
    '<ul><li>Первый пункт<ul><li>Вложенный пункт</li></ul></li><li>Второй пункт</li></ul>'+
    '<details><summary>НЕЧИТАТЬ управление</summary><p>Закрытый ответ</p></details>'+
    '<details open><summary>НЕЧИТАТЬ управление</summary><p>Открытый ответ</p></details>'+
    '<div data-level="junior"><p>Junior-only</p></div><div data-level="head"><p>Head-only</p></div>'+
    '<p><a href="https://example.org">https://example.org</a></p>'+
    '<div class="tbl-wrap"><table><tr><td>Метрика</td><td>Значение</td></tr></table></div>';
  document.querySelector('main').appendChild(fixture);
  const oldFilter=document.body.dataset.filter;
  document.body.dataset.filter='head';
  try{
    const snapshot=window.bookAudio.extractTopic(fixture.id);
    const text=snapshot.blocks.map(b=>b.text).join('\n');
    assert(snapshot.id===fixture.id&&snapshot.title==='Заголовок аудио','topic identity');
    assert(snapshot.blocks[0].text==='Заголовок аудио','title first');
    assert(!text.includes('НЕЧИТАТЬ')&&!text.includes('https://'),'UI, code and URLs excluded');
    assert(!text.includes('Закрытый ответ')&&text.includes('Открытый ответ'),'closed details excluded');
    assert(!text.includes('Junior-only')&&text.includes('Head-only'),'level filter respected');
    assert(text.split('Вложенный пункт').length===2,'nested lists not duplicated');
    assert(text.includes('Метрика; Значение'),'table row read in order');
    const paragraph=snapshot.blocks.find(b=>b.text.includes('API абзац'));
    window.bookAudio.highlight(fixture.id,paragraph.id);
    assert(fixture.querySelector('.speech-current').textContent.includes('API абзац'),'paragraph highlight');
    window.bookAudio.highlight(fixture.id,null);
    assert(!fixture.querySelector('.speech-current'),'highlight cleared');
    assert(window.bookAudio.extractTopic('not-a-topic')===null,'invalid topic rejected');
  }finally{fixture.remove();document.body.dataset.filter=oldFilter;}
})();
