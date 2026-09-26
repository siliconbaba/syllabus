(function () {
  'use strict';
  const main = document.querySelector('main'), sidebar = document.getElementById('sidebar');
  let gesture = null, suppressClickUntil = 0;
  const hasSelection = () => !!getSelection()?.toString().trim();
  const excluded = 'input,textarea,select,button,[contenteditable="true"],.tbl-wrap,table,pre';
  function reset() {
    gesture = null; document.body.classList.remove('back-gesture-ready','menu-gesture-ready');
  }
  document.addEventListener('touchstart', e => {
    reset();
    if (e.touches.length !== 1 || hasSelection() || e.target.closest(excluded)) return;
    const touch = e.touches[0], menuOpen = document.body.classList.contains('side-open');
    const kind = menuOpen && sidebar.contains(e.target) ? 'menu' :
      !menuOpen && main.contains(e.target) && touch.clientX <= 24 && window.bookNavigation.canBack() ? 'back' : null;
    if (kind) gesture = {kind, x:touch.clientX, y:touch.clientY, started:performance.now(), claimed:false, ready:false};
  }, {passive:true});
  document.addEventListener('touchmove', e => {
    if (!gesture) return;
    if (e.touches.length !== 1 || hasSelection() || performance.now() - gesture.started > 900) { reset(); return; }
    const dx = e.touches[0].clientX - gesture.x, dy = e.touches[0].clientY - gesture.y;
    const progress = gesture.kind === 'back' ? dx : -dx;
    if (!gesture.claimed) {
      if (Math.abs(dy) > 12 && Math.abs(dy) >= Math.abs(dx) || progress < -12) { reset(); return; }
      if (progress < 14 || progress < Math.abs(dy)*1.5) return;
      gesture.claimed = true;
    }
    if (e.cancelable) e.preventDefault();
    gesture.ready = progress >= 72 && progress > Math.abs(dy)*1.5;
    document.body.classList.toggle(gesture.kind === 'back' ? 'back-gesture-ready' : 'menu-gesture-ready', gesture.ready);
  }, {passive:false});
  document.addEventListener('touchend', () => {
    if (!gesture) return;
    const {kind, ready, claimed} = gesture;
    const valid = ready && !hasSelection() && performance.now() - gesture.started <= 900;
    reset();
    if (claimed) suppressClickUntil = performance.now()+400;
    if (valid) {
      if (kind === 'menu') window.bookNavigation.closeMenu();
      else window.bookNavigation.back();
    }
  });
  document.addEventListener('touchcancel', reset);
  document.addEventListener('click', e => {
    if (performance.now() < suppressClickUntil) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  document.addEventListener('visibilitychange', reset);
})();
