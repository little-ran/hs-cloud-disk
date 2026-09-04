# HS云盘 Git 项目管理手册

> 仓库：https://github.com/little-ran/hs-cloud-disk（私有）
> 本地：`D:\cloud\seafile-docker`
> 服务器：`/home/vsens/seafile-deploy`

---

## 一、仓库结构

```
hs-cloud-disk/
├── .gitignore                    # 忽略规则（敏感文件/数据目录/备份）
├── docker-compose.yml            # Docker 编排配置（引用 .env 变量）
├── .env                          # 环境变量（含密码，已 gitignore，不进仓库）
└── seafile-custom/               # 所有定制文件
    ├── seafile.nginx.conf        # nginx 站点配置（含下载缓存修复）
    ├── start.py                  # 容器启动脚本（含 proxy_cache_path 自动注入）
    ├── seahub_settings.py        # seahub 全部配置（安全加固/中间件/品牌）
    ├── seafile.conf              # fileserver 配置
    ├── react_app.html            # React 前端入口模板
    ├── sysadmin_react_app.html   # 管理后台模板
    ├── seahub/
    │   └── templates/
    │       └── registration/
    │           └── login.html    # 登录页模板
    ├── *.js                      # 前端注入脚本（悬浮球/改名防护/标签页等）
    ├── beautify.css              # 美化样式
    ├── favicon.ico               # 网站图标
    ├── red-logo.png              # 品牌Logo
    └── red-logo-dark.png         # 深色Logo
```

### 不进仓库的文件（.gitignore）

| 文件 | 原因 |
|------|------|
| `.env` | 含数据库密码、管理员密码、JWT密钥 |
| `.admin_passwd` | nginx Basic Auth 密码文件 |
| `seafile-data/` | Seafile 运行数据（用户文件、日志） |
| `seafile-mysql/` | 数据库数据 |
| `seafile-redis/` | 缓存数据 |
| `*.bak` / `*.bak_*` | 备份文件 |
| `*.tar` / `*.zip` | 大文件 |

---

## 二、网络与代理配置

本机通过 Hiddify VPN 翻墙访问 GitHub。Git 需配置代理：

```bash
# 设置代理（Hiddify mixed 端口 12334）
git config http.proxy http://127.0.0.1:12334
git config https.proxy http://127.0.0.1:12334

# 取消代理（VPN 关闭后）
git config --unset http.proxy
git config --unset https.proxy
```

> **注意**：VPN 关闭后 push/pull 会失败，需先开 VPN 再操作。

---

## 三、认证方式

### 方式一：Personal Access Token（推荐）

```bash
# 设置 remote URL 带 token（临时，push 后清除）
git remote set-url origin https://little-ran:<TOKEN>@github.com/little-ran/hs-cloud-disk.git

# push 完后立即清除 token
git remote set-url origin https://github.com/little-ran/hs-cloud-disk.git
```

Token 生成：https://github.com/settings/tokens → Generate new token (classic) → 勾选 `repo`

### 方式二：Git Credential Manager（交互式）

```powershell
# 在 PowerShell 中执行（会弹出浏览器登录窗口）
$env:HTTPS_PROXY="http://127.0.0.1:12334"
git push -u origin main
```

### Push 时绕过 Credential Manager

```bash
GIT_TERMINAL_PROMPT=0 git -c credential.helper= push https://little-ran:<TOKEN>@github.com/little-ran/hs-cloud-disk.git main
```

---

## 四、日常操作

### 1. 修改文件后提交推送

```bash
cd D:/cloud/seafile-docker

# 查看改了什么
git status
git diff

# 添加改动
git add -A                    # 添加所有改动
git add seafile-custom/start.py  # 只添加指定文件

# 提交（写清楚改了什么）
git commit -m "修复：下载token缓存持久化到start.py"

# 推送（确保 VPN 已开启）
git push origin main
```

### 2. 从服务器同步最新配置到本地

```bash
# 用脚本从服务器拉取文件（见下方"同步脚本"）
# 然后提交到 git
git add -A
git commit -m "同步：从服务器拉取最新配置"
git push origin main
```

### 3. 从 GitHub 拉取到新机器

```bash
git clone https://github.com/little-ran/hs-cloud-disk.git
# 然后手动创建 .env（从安全渠道获取）
```

### 4. 查看历史

```bash
git log --oneline              # 简洁历史
git log --oneline -5           # 最近5条
git show <commit-hash>         # 查看某次提交的详细改动
```

### 5. 回退错误提交

```bash
# 撤销最近1次提交（保留改动在工作区）
git reset HEAD~1

# 撤销最近1次提交（丢弃改动）
git reset --hard HEAD~1

# 推送回退到远程（危险！会覆盖远程历史）
git push origin main --force
```

---

## 五、服务器↔本地↔GitHub 三方同步流程

```
服务器 (10.0.124.98)          本地 (D:\cloud\seafile-docker)        GitHub
    │                                │                               │
    │  1. SSH拉取文件到本地           │                               │
    │ ────────────────────────────> │                               │
    │                                │  2. git add + commit          │
    │                                │  3. git push                  │
    │                                │ ────────────────────────────> │
    │                                │                               │
    │  4. 需要部署时从本地推到服务器   │                               │
    │ <──────────────────────────── │                               │
```

### 从服务器同步到本地的脚本

```python
# 用法：在本地执行，从服务器拉取所有定制文件
# python sync_from_server.py
import paramiko, os, base64

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.0.124.98", port=22022, username="vsens",
          password="dhy0s2vRaEOEbxGb", timeout=15, look_for_keys=False, allow_agent=False)

LOCAL_BASE = r"D:\cloud\seafile-docker"
files = [
    ("/home/vsens/seafile-deploy/seafile-custom/seafile.nginx.conf", r"seafile-custom\seafile.nginx.conf"),
    ("/home/vsens/seafile-deploy/seafile-custom/start.py", r"seafile-custom\start.py"),
    ("/home/vsens/seafile-deploy/seafile-custom/react_app.html", r"seafile-custom\react_app.html"),
    # ... 其他文件按需添加
]
for remote, rel in files:
    local = os.path.join(LOCAL_BASE, rel)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    _, o, _ = c.exec_command('cat "%s" | base64' % remote, timeout=15, get_pty=True)
    content = base64.b64decode(o.read().decode().strip())
    with open(local, "wb") as f:
        f.write(content)
    print("OK:", rel)
c.close()
```

---

## 六、提交规范

提交信息格式：

```
<类型>：<简短描述>

<可选的详细说明>
```

类型：

| 类型 | 含义 | 示例 |
|------|------|------|
| `修复` | Bug 修复 | `修复：下载token一次性消费导致403` |
| `新增` | 新功能 | `新增：阅后即焚入口注入` |
| `同步` | 从服务器同步 | `同步：从服务器拉取最新seahub_settings` |
| `清理` | 删除无用文件 | `清理：删除.bak备份文件` |
| `安全` | 安全加固 | `安全：关闭注册功能+Cookie HttpOnly` |
| `品牌` | 品牌定制 | `品牌：帮助页去除Seafile文案` |

---

## 七、注意事项

1. **永远不要提交 `.env`**——它含数据库密码和管理员密码
2. **push 前确认 VPN 已开启**——Hiddify 端口 12334
3. **push 后清除 URL 里的 token**——`git remote set-url origin https://github.com/little-ran/hs-cloud-disk.git`
4. **服务器改动后及时同步**——避免本地/远程仓库与服务器配置脱节
5. **不要在 main 分支直接做大改动**——建议创建分支：`git checkout -b fix-xxx`，改完合并
6. **.bak 文件不要提交**——.gitignore 已排除，但新增备份时注意命名格式为 `*.bak_*`
