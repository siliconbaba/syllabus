(function () {
  'use strict';
  const handler = window.webkit?.messageHandlers?.saved;
  const excluded = 'button,input,select,textarea,nav,script,style,svg,pre,code,summary,.studied,.topic-actions,.table-hint,[hidden],[aria-hidden="true"]';
  const blocks = 'h3,h4,h5,h6,p,li,td,th,blockquote';
  const normalize = s => s.replace(/\s+/g, ' ').trim();
  let timer, highlighted;
  function index(topic) {
    topic.querySelectorAll(blocks).forEach((el, i) => { el.dataset.savedAnchor = topic.id + '-saved-' + i; });
  }
  function allowed(node, topic) {
    let el = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    if (!topic.contains(el) || el.closest(excluded)) return false;
    while (el) {
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility !== 'visible' || style.opacity === '0' || el.inert) return false;
      if (el.tagName === 'DETAILS' && !el.open) return false;
      if (el === topic) break;
      el = el.parentElement;
    }
    return true;
  }
  function payload() {
    const selection = getSelection();
    if (!selection || selection.rangeCount !== 1 || selection.isCollapsed) return null;
    const range = selection.getRangeAt(0);
    const start = range.startContainer.nodeType === 1 ? range.startContainer : range.startContainer.parentElement;
    const topic = start.closest('main .topic[id]');
    if (!topic || !topic.contains(range.endContainer) || !allowed(range.startContainer, topic) || !allowed(range.endContainer, topic)) return null;
    const walker = document.createTreeWalker(topic, NodeFilter.SHOW_TEXT);
    const pieces = [];
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!range.intersectsNode(node)) continue;
      const text = node.textContent.slice(node === range.startContainer ? range.startOffset : 0, node === range.endContainer ? range.endOffset : undefined);
      if (!normalize(text)) continue;
      if (!allowed(node, topic)) return null;
      pieces.push(text);
    }
    const text = normalize(selection.toString());
    if (!text || text.length > 20000 || !pieces.length) return null;
    index(topic);
    const semanticID = window.bookAudio.selectionBlock(range.startContainer);
    const part = topic.closest('.part');
    return {text, topicID:topic.id, topicTitle:normalize(topic.querySelector('h3')?.textContent || ''),
      ...(semanticID ? {anchor:semanticID}:{}),
      ...(part?.querySelector('h2') ? {sectionTitle:normalize(part.querySelector('h2').textContent)}:{})};
  }
  const actions = document.createElement('div'); actions.className = 'saved-selection'; actions.hidden = true;
  let selected = null, pressed = null, pressing = false, lastTouchAction = 0;
  function refresh() {
    const value = payload();
    if (value) selected = value;
    else if (!pressing) selected = null;
    actions.hidden = !selected;
  }
  for (const [action, title] of [['save','Сохранить'],['listenFrom','Слушать отсюда']]) {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'btn'; button.textContent = title;
    button.dataset.action = action;
    // Freeze the selection before WebKit dismisses its edit menu or moves focus.
    function capture(e) { pressing = true; pressed = payload() || selected; if (e.cancelable) e.preventDefault(); }
    button.addEventListener('pointerdown', capture);
    button.addEventListener('touchstart', capture, {passive:false});
    function perform(e) {
      if (e.cancelable) e.preventDefault();
      const value = pressed || payload() || selected;
      pressed = null; pressing = false;
      if (value && handler) handler.postMessage({action,...value});
    }
    button.addEventListener('touchend', e => { lastTouchAction = Date.now(); perform(e); });
    button.addEventListener('click', e => { if (Date.now()-lastTouchAction>500) perform(e); });
    button.addEventListener('touchcancel', () => { pressing=false;pressed=null;refresh(); });
    actions.appendChild(button);
  }
  if (handler) document.body.appendChild(actions);
  document.addEventListener('selectionchange', refresh);
  document.querySelector('main').addEventListener('scroll', () => { if (!pressing) {selected=null;actions.hidden=true;} }, {passive:true});
  function feedback(text, clear = false) {
    if (clear) { actions.hidden = true; selected = null; pressed = null; pressing = false; getSelection()?.removeAllRanges(); }
    const toast = document.createElement('div'); toast.className = 'saved-toast'; toast.setAttribute('role','status'); toast.textContent = text;
    document.body.appendChild(toast); setTimeout(() => toast.remove(), 2000);
  }
  async function openSource(value) {
    const topic = document.getElementById(value.topicID);
    if (!topic?.matches('main .topic')) return 'missingTopic';
    const origin = window.bookNavigation.snapshot();
    index(topic);
    let target = window.bookAudio.elementForBlock(topic, value.anchor) || Array.from(topic.querySelectorAll('[data-saved-anchor]')).find(el => el.dataset.savedAnchor === value.anchor);
    // An updated curriculum may move a structural anchor: verify its text before using it.
    if (target && !normalize(target.textContent).includes(normalize(value.text))) target = null;
    if (!target) target = Array.from(topic.querySelectorAll(blocks)).find(el => normalize(el.textContent).includes(normalize(value.text)));
    if (target) {
      for (let el = target; el && el !== topic; el = el.parentElement) if (el.tagName === 'DETAILS') el.open = true;
      if (!allowed(target, topic)) document.querySelector('#filter [data-f="all"]')?.click();
    }
    window.bookNavigateTo(topic.id, true, origin);
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    if (target && allowed(target, topic)) {
      const main = document.querySelector('main');
      main.scrollTop += target.getBoundingClientRect().top - main.getBoundingClientRect().top - 20;
      if (highlighted) highlighted.classList.remove('saved-source');
      clearTimeout(timer); highlighted = target; target.classList.add('saved-source');
      timer = setTimeout(() => { target.classList.remove('saved-source'); highlighted = null; }, 1800);
      window.bookSavePosition?.();
      return 'anchor';
    }
    return 'topic';
  }
  if (handler) {
    const entry = document.createElement('button'); entry.className = 'btn'; entry.id = 'saved-entry'; entry.textContent = 'Сохранённое';
    entry.addEventListener('click', () => handler.postMessage({action:'open'}));
    document.querySelector('.topbar').insertBefore(entry, document.getElementById('themeBtn'));
  }
  window.bookSaved = {payload,openSource,feedback};
})();
