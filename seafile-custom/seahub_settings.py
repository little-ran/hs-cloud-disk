# -*- coding: utf-8 -*-
import os
SECRET_KEY = os.environ.get('SEAHUB_SECRET_KEY', 'change-me-in-production')

TIME_ZONE = 'Asia/Shanghai'

SERVICE_URL = 'http://10.0.124.98:8088'
FILE_SERVER_ROOT = 'http://10.0.124.98:8088/seafhttp'




SITE_NAME = 'HS云盘'
SITE_TITLE = 'HS云盘'
CUSTOM_LOGO_PATH = 'custom/mylogo.png'
FAVICON_PATH = 'custom/favicon.ico'

# 持久化自定义模板覆盖（悬浮球 / 音乐电台 / 阅后即焚 注入）
import sys as _sys
_mod = _sys.modules.get('seahub.settings')
if _mod is not None and hasattr(_mod, 'TEMPLATES'):
    _d = '/opt/seafile/seahub-data/custom/templates'
    if _d not in _mod.TEMPLATES[0]['DIRS']:
        _mod.TEMPLATES[0]['DIRS'].insert(0, _d)
# 受保护资料库改名/删除 服务端拦截（rename_block 中间件）
# 已在下方 expired_share_block 的 try 块内统一挂载，见 MIDDLEWARE 配置。

# === 过期分享链接服务端拦截（2026-08-05 / 报告 B-5a）===
# 报告：Seafile CE 核心 view 不检查 expire_date，导致过期分享页仍 200。
# 本中间件放到 /shared/seafile/conf/（容器内）/seafile-data/seafile/conf/（宿主）。
# SEAFILE_CENTRAL_CONF_DIR 默认未设置，所以这里手动把 conf 目录加入 sys.path[0]，
# 让中间件能被 import，挂到 MIDDLEWARE 顶部拦截 /d/<token>/ 路径。
try:
    import os as _eos
    import sys as _esys
    _conf_dir = _eos.environ.get('SEAFILE_CENTRAL_CONF_DIR', '/shared/seafile/conf')
    if _eos.path.isdir(_conf_dir) and _conf_dir not in _esys.path:
        _esys.path.insert(0, _conf_dir)
    import expired_share_block as _esb  # noqa: E402
    _emod = _esys.modules.get('seahub.settings')
    if _emod is not None and hasattr(_emod, 'MIDDLEWARE'):
        _emw = list(_emod.MIDDLEWARE)
        _entry = 'expired_share_block.ExpiredShareBlockMiddleware'
        if _entry not in _emw:
            _emw.insert(0, _entry)
            _emod.MIDDLEWARE = _emw
            print('[expired-share-block] mounted at MIDDLEWARE[0] from', _conf_dir)

        # —— 在同一个 try 块内挂载 rename_block（B-4 修复，2026-08-06 合并到此处避免独立 try 被吞）——
        # rename_block 在 /opt/seafile/conf/，sys.path 已包含
        try:
            import rename_block as _rb  # noqa: E402
            _rentry = 'rename_block.RenameBlockMiddleware'
            if _rentry not in _emw:
                _emw.insert(0, _rentry)
                _emod.MIDDLEWARE = _emw
                print('[rename-block] mounted at MIDDLEWARE[0]')
        except Exception as _rbe:
            print('[rename-block] mount failed:', _rbe)

        # —— 在同一个 try 块内挂载 share_password_enforcer（B-5b 修复，2026-08-06）——
        try:
            import share_password_enforcer as _spe  # noqa: E402
            _pentry = 'share_password_enforcer.SharePasswordEnforcerMiddleware'
            if _pentry not in _emw:
                _emw.insert(0, _pentry)
                _emod.MIDDLEWARE = _emw
                print('[share-password-enforcer] mounted at MIDDLEWARE[0]')
        except Exception as _spe_e:
            print('[share-password-enforcer] mount failed:', _spe_e)
    else:
        print('[expired-share-block] WARN: seahub.settings not loaded yet')
except Exception as _ee:
    import traceback as _tb
    print('[expired-share-block] mount failed:', _ee)
    _tb.print_exc()

# === rename_block / share_password_enforcer 已合并到上面 expired-share-block 的 try 块内（2026-08-06）===
# 原独立的 mount 段被吞（猜测 gunicorn print 缓冲或 settings.py 第二次 import 跳过部分代码），
# 改为在 expired-share-block 同一 try 内顺序挂载三个中间件。

# === 分享链接安全加固（2026-08-06 / 报告 B-5b）===
# 强制：所有分享必须设置密码（默认 False 允许无密码分享）
SHARE_LINK_FORCE_USE_PASSWORD = True
# 分享密码最少 10 位（Seafile 默认就是 10，显式写一遍便于审计）
SHARE_LINK_PASSWORD_MIN_LENGTH = 10
# 强制：所有分享必须有过期时间（默认 0 = 永不过期）
SHARE_LINK_EXPIRE_DAYS_DEFAULT = 7
SHARE_LINK_EXPIRE_DAYS_MIN = 1
SHARE_LINK_EXPIRE_DAYS_MAX = 30

# 用户登录即自动创建「快速保存-{email}」「我的音乐-{email}」两个库。
# 放在本目录（SEAFILE_CENTRAL_CONF_DIR），已被 seahub 加入 sys.path；
# import 即触发 user_logged_in signal connect。
# 受 rename_block 名字正则保护，登录后这两个库不能再改名。
try:
    import auto_create_user_repos as _auto_create  # noqa: F401
except Exception as _e:
    import traceback as _tb
    print('[auto-create] import failed:', _e)
    _tb.print_exc()


# === 全站 500 根因修复 (v7：复制所有 CONSTANCE_* 属性到 Settings 对象) ===
# 根因（已验证）：Django Settings.__init__ 在 seahub.settings 第 1168 行
# import seahub_settings 之前就 snapshot 了所有大写属性。之后 1323 行起的
# CONSTANCE_CONFIG / CONSTANCE_ENABLED / 等只是给 seahub.settings 模块对象赋值，
# 不会同步到 django.conf.settings 这个 Settings 实例上。
# 修法：seahub_settings.py 注册 request_started 回调，在首个 HTTP 请求时（django
# 已 setup）扫描 seahub.settings 中所有以 CONSTANCE_ 开头的大写属性，全部 setattr
# 到 django.conf.settings 上，并 reload constance.settings 让它重新快照 CONFIG。
import logging as _cf7_log
_cf7_log = _cf7_log.getLogger("constance_fix_v7")

def _cf7_patch():
    try:
        from django.conf import settings as _dj
        import seahub.settings as _shs
        import constance.settings as _cs
        import importlib as _il
        # 1. Copy ALL CONSTANCE_* attrs from seahub.settings module -> Settings obj
        n = 0
        for _name in dir(_shs):
            if _name.isupper() and _name.startswith("CONSTANCE_") and not _name.startswith("__"):
                _val = getattr(_shs, _name, None)
                setattr(_dj, _name, _val)
                n += 1
        _cf7_log.info("copied %d CONSTANCE_* attrs from seahub.settings to django.conf.settings", n)
        # 2. Reload constance.settings to re-snapshot CONFIG
        _il.reload(_cs)
        _cf7_log.info("constance.settings.CONFIG now has %d keys (ENABLE_TERMS=%s)",
                      len(_cs.CONFIG), "ENABLE_TERMS_AND_CONDITIONS" in _cs.CONFIG)
        if "ENABLE_TERMS_AND_CONDITIONS" not in _cs.CONFIG:
            # Fallback: force set
            _full = dict(getattr(_shs, "CONSTANCE_CONFIG", {}) or {})
            _cs.CONFIG.update(_full)
            _cf7_log.info("fallback: forcibly set constance.settings.CONFIG with %d keys", len(_full))
        return True
    except Exception:
        _cf7_log.exception("cf7_patch failed")
        return False

from django.core.signals import request_started as _cf7_rs
_cf7_done = [False]
def _cf7_late(sender, **kwargs):
    if _cf7_done[0]:
        return
    if _cf7_patch():
        _cf7_done[0] = True
        try:
            _cf7_rs.disconnect(_cf7_late, dispatch_uid="constance_v7_late")
        except Exception:
            pass
_cf7_rs.connect(_cf7_late, dispatch_uid="constance_v7_late")
_cf7_log.info("constance_fix v7 registered; will patch on first request")
# === end constance 修复 v7 ===
# === side nav footer: 阅后即焚入口 ===
# 用自定义 HTML 替换左侧栏底部"帮助和资源"整个区域（帮助/客户端/关于全部移除），
# 放入"阅后即焚"链接。点击时用 JS 根据当前主机名动态计算端口 8001 的 URL，新标签打开。
SIDE_NAV_FOOTER_CUSTOM_HTML = '<style>.side-nav-footer{display:block!important;padding:0!important;background:transparent!important;border-top:none!important;}.side-nav-con>h2.heading:last-of-type{display:none!important;}#share-admin-sub-nav .sharp{display:none!important;}#share-admin-sub-nav .nav-item .nav-link{padding-left:2.25rem!important;display:flex!important;align-items:center!important;}#share-admin-sub-nav .sharp{visibility:hidden!important;width:1.25rem!important;margin-right:.325rem!important;color:transparent!important;display:inline-block!important;}.burn-icon{display:inline-flex;align-items:center;justify-content:center;width:1.25rem;height:1.25rem;margin-right:.5rem;color:var(--bs-icon-tertiary-color,#888);flex-shrink:0;}.burn-icon svg{width:1.25rem;height:1.25rem;fill:currentColor;}.side-nav-folded .side-nav-footer .heading{display:none!important;}.side-nav-folded .side-nav-footer .nav-container{padding:0!important;margin:0!important;}.side-nav-folded .side-nav-footer .nav-item{width:100%;display:flex!important;justify-content:center!important;}.side-nav-folded .side-nav-footer .nav-link{justify-content:center!important;padding:.25rem 0!important;}.side-nav-folded .side-nav-footer .nav-text{display:none!important;}.side-nav-folded .side-nav-footer .burn-icon{margin-right:0!important;}</style><h2 class="mb-2 px-2 font-weight-normal heading">拓展功能</h2><ul class="nav nav-pills flex-column nav-container"><li class="nav-item flex-column"><a class="nav-link ellipsis" href="#" title="阅后即焚" onclick="window.open((window.location.protocol===&quot;https:&quot;?&quot;https:&quot;:&quot;http:&quot;)+&quot;//&quot;+window.location.hostname+&quot;:8001/&quot;,&quot;_blank&quot;);return false;"><span class="burn-icon" aria-hidden="true"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M13.5.67s.74 2.65.74 5.08c0 2.57-1.31 4.38-2.91 4.38-.97 0-1.69-.77-1.69-1.94 0-.43.14-.89.37-1.25.39-.63.97-1.11.97-2.07 0-.86-.43-1.58-1.31-2.03.03-.03.59-.31 1.05-.31.25 0 .43.06.65.14C12.79 1.49 13.5.67 13.5.67zM17.18 14.5c0 2.54-2.07 4.5-4.68 4.5-2.61 0-4.68-1.96-4.68-4.5 0-1.49.65-2.85 1.79-3.69.16-.13.39.02.39.21 0 .14-.07.26-.14.38-.21.35-.34.75-.34 1.17 0 .97.77 1.74 1.74 1.74.96 0 1.74-.77 1.74-1.74 0-1.32-1.09-2.39-2.14-3.04 1.31-1.64 3.31-2.68 5.51-2.68.1 0 .19.01.29.01-.09.42-.14.85-.14 1.29 0 1.82 1.01 3.41 2.51 4.24.12.07.27.13.42.17.12.04.24.07.36.09.16.03.32.05.49.05.17 0 .33-.02.49-.05.21-.04.41-.09.61-.16.16-.05.31-.11.46-.18.2-.11.4-.23.58-.37.42-.32.77-.72 1.03-1.18.26.62.41 1.31.41 2.04z"/></svg></span><span class="nav-text">阅后即焚</span></a></li></ul>'
# === end side nav footer ===

# === login captcha 阈值 限制（原默认 5 太严）===
LOGIN_ATTEMPT_LIMIT = 9999   # 调高阈值，几乎不会因输错密码而触发 CAPTCHA；
                            # 该值也在 constance 里，后台“系统管理 → 设置”可随时修改。
FREEZE_USER_ON_LOGIN_FAILED = False  # 明确不冻结账号
# === end login captcha 阈值 ===

# === 2026-08-06 额外安全加固（渗透测试 C-7 / C-6）===
# C-7：DEBUG 显式关闭，500 页不泄露 Django stack trace
DEBUG = False
# === 2026-08-12 渗透测试修复 ===
# F-04: 关闭注册功能
ENABLE_SIGNUP = False

# F-03: sfcsrftoken cookie 加 HttpOnly
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# F-01: 隐藏服务器版本信息（server-info 不返回版本）
# Seafile CE 没有直接隐藏 server-info 的开关，
# 通过 nginx 已限制 admin API（F-06），server-info 不含敏感信息

# F-02: CORS 收紧（已在 nginx 层去掉 ACAO:*）

# F-09/F-10: 分享链接安全加固
# 已有 SHARE_LINK_FORCE_USE_PASSWORD = True
# 已有 SHARE_LINK_EXPIRE_DAYS_DEFAULT = 7
# 额外：禁用预览（防止 can_download=false 的文件通过预览泄露）
# 注意：这会影响正常预览功能，如需要预览则注释掉此行
# SHARE_LINK_PREVIEW = False  # 暂不关闭预览，通过 nginx 层限制

# 禁止匿名用户访问（已有）
# ENABLE_BIND_IP = True  # 不需要

# F-05: 不在 seahub 层处理端口，已由防火墙/网络层处理
