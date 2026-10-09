(function () {
  'use strict';
  const handler = window.webkit?.messageHandlers?.trainer;
  if (!handler) return;
  const entry = document.createElement('button');
  entry.type = 'button'; entry.className = 'btn'; entry.id = 'trainer-entry';
  entry.textContent = 'Тренажёр управленческого мышления';
  entry.style.cssText = 'position:sticky;top:0;z-index:2;background:var(--bg-elev);display:block;width:100%;white-space:normal;text-align:left;margin:12px 0;min-height:44px';
  entry.addEventListener('click', function () {
    window.bookSavePosition?.();
    window.bookNavigation?.closeMenu();
    handler.postMessage({action: 'open'});
  });
  document.getElementById('toc').before(entry);
})();
