// 隐藏 Seafile 管理员后台「系统信息」菜单项 与 「升级到专业版」链接
// 注入方式：覆盖 sysadmin_react_app.html，在 render_bundle 'sysAdmin' 后加载本脚本
(function () {
  'use strict';

  // 1) 「升级到专业版」链接：按外站 href 精准隐藏（最稳，不依赖文案）
  var PRO_HREF_FRAGMENTS = [
    'migrate_ce_to_pro',
    'manual.seafile.com'
  ];

  // 2) 左侧「系统信息 / Info」菜单项：在 .side-panel 内，按 nav-text 文字匹配
  //    中文环境 gettext('Info') => "信息"，英文 => "Info"
  var MENU_TEXTS = ['信息', 'Info', 'System Info', '系统信息'];

  function hideProLinks() {
    var links = document.querySelectorAll('a[href]');
    links.forEach(function (a) {
      var href = (a.getAttribute('href') || '').toLowerCase();
      for (var i = 0; i < PRO_HREF_FRAGMENTS.length; i++) {
        if (href.indexOf(PRO_HREF_FRAGMENTS[i].toLowerCase()) !== -1) {
          hideAncestor(a);
          break;
        }
      }
    });
  }

  function hideInfoMenu() {
    // 只处理后台侧边栏内的菜单，避免误伤页面正文里的 "Info" 字样
    var sidePanels = document.querySelectorAll('.side-panel, .sysadmin-side-panel, nav');
    sidePanels.forEach(function (panel) {
      var nodes = panel.querySelectorAll('a, li, .nav-item, [role="menuitem"]');
      nodes.forEach(function (node) {
        var txt = (node.textContent || '').trim();
        if (MENU_TEXTS.indexOf(txt) !== -1) {
          hideAncestor(node, panel);
        }
      });
    });
  }

  // 向上找合适的菜单容器隐藏（优先 NavLink/li/a，其次 node 自身）
  function hideAncestor(node, scope) {
    var candidate = node;
    var tags = ['A', 'LI', 'DIV'];
    while (candidate && candidate !== document.body) {
      if (scope && !scope.contains(candidate)) break;
      var tag = candidate.tagName;
      if (tags.indexOf(tag) !== -1) {
        // 仅当该容器恰好只承载这一个菜单文字时隐藏，避免隐藏整个分组
        var cls = (candidate.className || '').toString();
        if (/nav|menu|item|side|link/i.test(cls) || tag === 'LI' || tag === 'A') {
          candidate.style.display = 'none';
          candidate.setAttribute('data-hidden-by-pro', '1');
          return;
        }
      }
      candidate = candidate.parentNode;
    }
    node.style.display = 'none';
  }

  function run() {
    hideProLinks();
    hideInfoMenu();
  }

  // React 异步渲染，多次尝试
  run();
  setTimeout(run, 300);
  setTimeout(run, 1000);
  setTimeout(run, 2500);

  // 监听 SPA 路由切换（后台为单页应用，切页面后重新渲染）
  var lastHref = location.href;
  setInterval(function () {
    if (location.href !== lastHref) {
      lastHref = location.href;
      setTimeout(run, 300);
      setTimeout(run, 1200);
    }
    // 也兜底轮询一次，应对同 URL 内的局部重渲染
    run();
  }, 1500);
})();
