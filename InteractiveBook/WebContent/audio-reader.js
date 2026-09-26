(function () {
  'use strict';
  var handler = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.speech;
  var currentTopic = null, highlighted = null;
  var excluded = 'script,style,nav,button,input,select,textarea,pre,code,svg,img,summary,.studied,.speech-listen,.table-hint,[hidden],[aria-hidden="true"]';
  var containers = new Set(['ARTICLE','SECTION','DIV','HEADER','FOOTER','P','H1','H2','H3','H4','H5','H6','UL','OL','LI','DL','DT','DD','BLOCKQUOTE','DETAILS','TABLE','THEAD','TBODY','TFOOT','TR','TD','TH','LABEL']);
  function post(message) { if (handler) handler.postMessage(message); }
  function topicFor(id) {
    var element = id && document.getElementById(id);
    return element && element.classList.contains('topic') ? element : null;
  }
  function visible(element) {
    if (element.matches(excluded)) return false;
    var style = getComputedStyle(element);
    return style.display !== 'none' && style.visibility !== 'hidden' && style.visibility !== 'collapse' && style.opacity !== '0' && style.contentVisibility !== 'hidden';
  }
  function blockID(topic, element) {
    var path = [];
    for (var el = element; el && el !== topic; el = el.parentElement) {
      var siblings = Array.from(el.parentElement.children).filter(function(sibling) { return sibling.tagName === el.tagName && !sibling.matches(excluded); });
      path.unshift(el.tagName.toLowerCase() + siblings.indexOf(el));
    }
    return topic.id + '-block-' + path.join('.');
  }
  function elementForBlock(topic, id) {
    return Array.from(topic.querySelectorAll('*')).find(function(el) { return !el.matches(excluded) && blockID(topic, el) === id; }) || null;
  }
  function selectionBlock(node) {
    var element = node.nodeType === 1 ? node : node.parentElement;
    var topic = element.closest('.topic[id]');
    if (!topic) return null;
    var snapshot = extractTopic(topic.id);
    if (!snapshot) return null;
    var ids = new Set(snapshot.blocks.map(function(block) { return block.id; }));
    for (var el = element; el && topic.contains(el); el = el.parentElement) {
      var id = blockID(topic, el);
      if (ids.has(id)) return id;
    }
    return null;
  }
  function extractTopic(id) {
    var topic = topicFor(id);
    if (!topic || !visible(topic)) return null;
    var blocks = [], counter = 0;
    function emit(element, text) {
      text = text.replace(/\s+/g, ' ').trim();
      if (!text || !/[\p{L}\p{N}]/u.test(text)) return;
      var semanticID = blockID(topic, element);
      element.dataset.speechId = semanticID;
      var kind = /^H[1-6]$/.test(element.tagName) ? 'heading' : element.closest('li') ? 'list' : 'paragraph';
      blocks.push({id: semanticID, text:text, kind:kind});
    }
    // Reset extraction markers so the same visible snapshot produces stable IDs.
    topic.querySelectorAll('[data-speech-id]').forEach(function(el) { delete el.dataset.speechId; });
    function inlineText(element) {
      if (!visible(element) || (element.tagName === 'DETAILS' && !element.open)) return '';
      if (element.tagName === 'A' && /^\s*(https?:\/\/|www\.|[\w.-]+\.[a-z]{2,}(?:\/|$))/i.test(element.textContent)) return '';
      return Array.from(element.childNodes).map(function(node) {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;
        if (node.nodeType === Node.ELEMENT_NODE) return inlineText(node);
        return '';
      }).join(' ');
    }
    function walk(element) {
      if (!visible(element)) return;
      if (element.tagName === 'DETAILS' && !element.open) return;
      if (element.tagName === 'TR') {
        emit(element, Array.from(element.children).filter(visible).map(inlineText).join('; ')); return;
      }
      var buffer = '';
      function flush() { emit(element, buffer); buffer = ''; }
      Array.from(element.childNodes).forEach(function(node) {
        if (node.nodeType === Node.TEXT_NODE) { buffer += ' ' + node.textContent; return; }
        if (node.nodeType !== Node.ELEMENT_NODE || !visible(node)) return;
        if (containers.has(node.tagName)) { flush(); walk(node); }
        else { buffer += ' ' + inlineText(node); }
      });
      flush();
    }
    walk(topic);
    return {id:id, title:topic.querySelector('h3').textContent.trim(), blocks:blocks};
  }
  function highlight(id, blockID) {
    if (highlighted) highlighted.classList.remove('speech-current');
    highlighted = null;
    var topic = topicFor(id);
    if (topic && blockID) {
      highlighted = topic.querySelector('[data-speech-id="' + CSS.escape(blockID) + '"]');
      if (highlighted) highlighted.classList.add('speech-current');
    }
    // Highlight only: automated scrolling must never trigger a topic change.
  }
  function topicChanged(id) {
    var topic = topicFor(id), next = topic ? topic.id : null;
    if (currentTopic === next) return;
    currentTopic = next;
    post({action:'context', id:next || ''});
  }
  function invalidate(id) {
    if (id && id !== currentTopic) return;
    post({action:'context', id:currentTopic || '', invalidate:true});
  }
  window.bookAudio = {extractTopic:extractTopic, highlight:highlight, selectionBlock:selectionBlock, elementForBlock:elementForBlock, topicChanged:topicChanged, invalidate:invalidate};
  if (handler) {
    document.querySelectorAll('.topic[id]').forEach(function(topic) {
      var head = topic.querySelector('.topic-head'), studied = head.querySelector('.studied');
      var actions = document.createElement('div'); actions.className = 'topic-actions';
      if (studied) actions.appendChild(studied);
      var listen = document.createElement('button'); listen.className = 'btn speech-listen';
      listen.type = 'button'; listen.textContent = 'Слушать';
      listen.setAttribute('aria-label','Слушать тему ' + topic.querySelector('h3').textContent.trim());
      listen.addEventListener('click',function() {
        currentTopic = topic.id;
        post({action:'listen',id:topic.id,title:topic.querySelector('h3').textContent.trim()});
      });
      actions.appendChild(listen); head.appendChild(actions);
    });
  }
})();
