cat > ~/seafile-deploy/seafile-data/seafile/seahub-data/custom/upload-button-inject.js <<'JSEOF'
(function () {
  'use strict';
  if (window.__HZ_UPLOAD_ENHANCE__) return;
  window.__HZ_UPLOAD_ENHANCE__ = true;

  // 真实 DOM：加号是 .dir-operation > span.path-item（图标 sf3-font-new）
  var OPERATION_SEL = '.dir-operation';
  var PLUS_SEL = '.dir-operation > span.path-item';
  var UPLOAD_ITEM_TEXT = ['上传文件', 'Upload files', 'Upload'];
  var ENHANCED_ATTR = 'data-hz-enhanced';

  function findUploadMenuItem() {
    var items = document.querySelectorAll('.dir-operation .dropdown-menu button.dropdown-item, .dropdown-menu button.dropdown-item');
    for (var i = 0; i < items.length; i++) {
      var t = (items[i].textContent || '').trim();
      if (UPLOAD_ITEM_TEXT.indexOf(t) !== -1) return items[i];
    }
    return null;
  }

  function triggerUploadFiles(plusEl) {
    var item = findUploadMenuItem();
    if (item) { item.click(); return; }
    // 先展开菜单，再等“上传文件”项出现后点击
    plusEl.click();
    var obs = new MutationObserver(function () {
      var item = findUploadMenuItem();
      if (item) {
        obs.disconnect();
        setTimeout(function () { item.click(); }, 60);
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
    setTimeout(function () { obs.disconnect(); }, 1000);
  }

  function enhance() {
    var plus = document.querySelector(PLUS_SEL);
    if (!plus || plus.hasAttribute(ENHANCED_ATTR)) return;
    var op = plus.closest(OPERATION_SEL);
    if (!op) return;
    plus.setAttribute(ENHANCED_ATTR, '1');

    // 1) 给原加号补“上传”文字
    plus.classList.add('hz-upload-entry');

    // 2) 左侧插入显眼的“上传文件”主按钮
    var mainBtn = document.createElement('button');
    mainBtn.type = 'button';
    mainBtn.className = 'hz-upload-main-btn';
    mainBtn.innerHTML = '<span class="hz-icon">⬆</span><span>上传文件</span>';
    mainBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      triggerUploadFiles(plus);
    });
    op.insertBefore(mainBtn, plus);
  }

  function injectStyle() {
    if (document.getElementById('hz-upload-style')) return;
    var css = [
      '.hz-upload-main-btn{',
      '  display:inline-flex;align-items:center;gap:6px;',
      '  height:32px;padding:0 14px;margin-right:8px;',
      '  border:none;border-radius:16px;',
      '  background:linear-gradient(135deg,#4facfe,#6f70ff);',
      '  color:#fff;font-size:13px;font-weight:600;line-height:1;',
      '  cursor:pointer;',
      '  box-shadow:0 4px 12px rgba(111,112,255,.35);',
      '  transition:transform .18s,box-shadow .18s;',
      '}',
      '.hz-upload-main-btn:hover{transform:translateY(-1px);box-shadow:0 8px 18px rgba(111,112,255,.5);}',
      '.hz-upload-entry{position:relative;padding-left:44px !important;border-radius:16px !important;}',
      '.hz-upload-entry::before{',
      '  content:"上传";position:absolute;left:14px;top:50%;transform:translateY(-50%);',
      '  font-weight:600;font-size:13px;color:inherit;pointer-events:none;',
      '}',
      '@media (prefers-reduced-motion:reduce){.hz-upload-main-btn{transition:none !important;}}'
    ].join('\n');
    var s = document.createElement('style');
    s.id = 'hz-upload-style';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function boot() {
    injectStyle();
    var obs = new MutationObserver(function () { enhance(); });
    obs.observe(document.body, { childList: true, subtree: true });
    enhance();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
JSEOF
