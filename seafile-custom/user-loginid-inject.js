/*
 * user-loginid-inject.js —— 在「系统管理 → 用户」添加用户弹窗中增加「Login ID」输入框
 * ----------------------------------------------------------------------------
 * 适用：Seafile CE 13.0 系统管理后台「添加用户」弹窗（Bootstrap 模态框）
 * 弹窗结构（实测）：
 *   .modal-content > .modal-body > form > .mb-3 > label.form-label + input.form-control
 *   .modal-footer > button.btn-primary（提交，创建时 disabled）
 *
 * 机制：
 *   1. 探测「添加用户」弹窗，在「邮箱」字段(.mb-3)之后注入一个 Login ID 输入框(.mb-3)；
 *   2. 拦截创建用户的 POST 响应，拿到新用户 email，若用户填了 Login ID，则自动
 *      PUT /api/v2.1/admin/users/<email>/（multipart/form-data, login_id）补写；
 *   3. 是否注入成功不影响正常创建，Login ID 为可选增强。
 *
 * 部署：
 *   - 本文件放在 seahub-data/custom/（对外 /media/custom/user-loginid-inject.js）
 *   - sysadmin_react_app.html 中 render_bundle 之后已引用本脚本。
 *   - 挂载即生效，硬刷新（Ctrl+F5）即可。
 */
(function () {
  "use strict";

  var VERSION = "20260826v2";
  if (window.__USER_LOGINID_INJECTED__) return;
  window.__USER_LOGINID_INJECTED__ = true;

  var injectedInput = null;

  function getCookie(name) {
    var m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : "";
  }
  function log() {
    if (console && console.log) console.log.apply(console, ["[user-loginid-inject]"].concat([].slice.call(arguments)));
  }

  // 判断是否为「添加用户」弹窗（标题含 添加用户 / 新建用户 / Add User）
  function isAddUserDialog(dlg) {
    if (!dlg) return false;
    var txt = (dlg.textContent || "").replace(/\s+/g, "");
    return /添加用户|新建用户|AddUser|CreateUser|NewUser/i.test(txt);
  }

  // 找「邮箱」字段所在的 .mb-3，作为插入锚点
  function findEmailAnchor(dlg) {
    var labels = dlg.querySelectorAll("label.form-label, label");
    for (var i = 0; i < labels.length; i++) {
      var t = (labels[i].textContent || "").replace(/\s+/g, "");
      if (/邮箱|email|帐号|账号|account/i.test(t)) {
        // 向上找 .mb-3 容器
        var node = labels[i];
        while (node && node !== dlg) {
          if (node.classList && node.classList.contains("mb-3")) return node;
          node = node.parentNode;
        }
        return labels[i].closest(".mb-3") || labels[i].parentNode;
      }
    }
    return null;
  }

  function buildLoginIdField() {
    var wrap = document.createElement("div");
    wrap.className = "mb-3";
    wrap.setAttribute("data-hz-loginid", "1");

    var label = document.createElement("label");
    label.className = "form-label";
    label.textContent = "Login ID（可选）";

    var input = document.createElement("input");
    input.type = "text";
    input.className = "form-control hz-loginid-input";
    input.placeholder = "创建后可在用户资料中修改";
    input.autocomplete = "off";

    wrap.appendChild(label);
    wrap.appendChild(input);
    injectedInput = input;
    return wrap;
  }

  function injectIntoDialog(dlg) {
    if (!dlg || dlg.querySelector("[data-hz-loginid]")) return;
    var anchor = findEmailAnchor(dlg);
    var field = buildLoginIdField();
    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(field, anchor.nextSibling);
      log("已插入 Login ID 输入框（锚点：", (anchor.textContent || "").slice(0, 16), "）");
    } else {
      // 兜底：插到 form 末尾
      var form = dlg.querySelector("form") || dlg.querySelector(".modal-body");
      if (form) { form.appendChild(field); log("未找到锚点，已插到 form 末尾"); }
    }
  }

  function scanDialogs() {
    var candidates = document.querySelectorAll(".modal-content, .modal, [role='dialog']");
    for (var i = 0; i < candidates.length; i++) {
      if (isAddUserDialog(candidates[i])) injectIntoDialog(candidates[i]);
    }
  }

  /* ---------- 创建成功后自动 PUT login_id ---------- */
  function doUpdateLoginId(email, loginId) {
    if (!email || !loginId) return;
    var fd = new FormData();
    fd.append("login_id", loginId);
    fetch("/api/v2.1/admin/users/" + encodeURIComponent(email) + "/", {
      method: "PUT",
      credentials: "include",
      headers: { "X-CSRFToken": getCookie("sfcsrftoken") || getCookie("csrftoken") },
      body: fd
    }).then(function (r) {
      if (r.ok) log("已为用户", email, "写入 Login ID:", loginId);
      else log("写入 Login ID 失败，HTTP", r.status);
    }).catch(function (e) { log("写入 Login ID 异常:", e); });
  }

  function tryConsume(email) {
    var loginId = (injectedInput && injectedInput.value || "").trim();
    if (email && loginId) doUpdateLoginId(email, loginId);
    if (injectedInput) injectedInput.value = "";
  }

  // 拦截 XMLHttpRequest（axios 底层用 XHR）
  var origOpen = XMLHttpRequest.prototype.open;
  var origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__hz_method = (method || "GET").toUpperCase();
    this.__hz_url = url || "";
    return origOpen.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function (body) {
    var self = this;
    if (this.__hz_method === "POST" && /\/api\/v2\.1\/admin\/users\/?$/.test(this.__hz_url)) {
      this.addEventListener("load", function () {
        try {
          if (self.status === 200 || self.status === 201) {
            var data = JSON.parse(self.responseText || "{}");
            var email = data && (data.email || data.contact_email);
            tryConsume(email);
          }
        } catch (e) {}
      });
    }
    return origSend.apply(this, arguments);
  };

  // 拦截 fetch（备用）
  var origFetch = window.fetch;
  if (typeof origFetch === "function") {
    window.fetch = function (input, init) {
      var url = (typeof input === "string") ? input : (input && input.url) || "";
      var method = ((init && init.method) || (input && input.method) || "GET").toUpperCase();
      var p = origFetch.apply(this, arguments);
      if (method === "POST" && /\/api\/v2\.1\/admin\/users\/?$/.test(url)) {
        p.then(function (resp) {
          if (resp.status === 200 || resp.status === 201) {
            return resp.clone().json().then(function (data) {
              var email = data && (data.email || data.contact_email);
              tryConsume(email);
            }).catch(function () {});
          }
        }).catch(function () {});
      }
      return p;
    };
  }

  /* ---------- 启动 ---------- */
  function boot() {
    log("已加载 v" + VERSION);
    scanDialogs();
    if (window.MutationObserver) {
      var mo = new MutationObserver(function (muts) {
        var need = false;
        for (var i = 0; i < muts.length; i++) {
          if (muts[i].addedNodes && muts[i].addedNodes.length) { need = true; break; }
        }
        if (need) scanDialogs();
      });
      mo.observe(document.documentElement, { childList: true, subtree: true });
    } else {
      setInterval(scanDialogs, 500);
    }
    var lastHref = location.href;
    setInterval(function () {
      if (location.href !== lastHref) { lastHref = location.href; setTimeout(scanDialogs, 200); }
    }, 800);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
