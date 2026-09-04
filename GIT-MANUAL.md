# HS云盘 Git 协作管理手册

> 仓库：https://github.com/little-ran/hs-cloud-disk（Private，邀请制）
> 管理员：little-ran
> 服务器：10.0.124.98:8088

---

## 一、仓库说明

| 项 | 内容 |
|---|---|
| 仓库地址 | https://github.com/little-ran/hs-cloud-disk |
| 可见性 | Private（仅受邀协作者可见） |
| 主分支 | main |
| 存储内容 | HS云盘部署配置与定制代码（不含密码/数据） |

### 仓库结构

```
hs-cloud-disk/
├── .gitignore                    # 忽略规则
├── docker-compose.yml            # Docker 编排配置
├── GIT-MANUAL.md                 # 本文档
└── seafile-custom/               # 所有定制文件
    ├── seafile.nginx.conf        # nginx 配置（含下载缓存修复）
    ├── start.py                  # 容器启动脚本
    ├── seahub_settings.py        # seahub 配置（安全/中间件/品牌）
    ├── seafile.conf              # fileserver 配置
    ├── react_app.html            # 前端入口模板
    ├── sysadmin_react_app.html   # 管理后台模板
    ├── seahub/templates/registration/login.html  # 登录页
    ├── *.js                      # 前端注入脚本
    ├── beautify.css              # 样式
    ├── favicon.ico               # 图标
    └── red-logo*.png             # Logo
```

### 不进仓库的文件

| 文件 | 原因 |
|------|------|
| `.env` | 含数据库密码、管理员密码、JWT密钥 |
| `.admin_passwd` | nginx Basic Auth 密码 |
| `seafile-data/` `seafile-mysql/` `seafile-redis/` | 运行数据 |

---

## 二、协作者加入方式

### 管理员邀请队友

1. 打开 https://github.com/little-ran/hs-cloud-disk/settings/access
2. 点 **Add people**
3. 输入队友的 GitHub 用户名
4. 权限选 **Write**（可编辑推送）
5. 点 **Add**

### 队友接受邀请

队友会收到邮件，或在 GitHub 通知里看到邀请，点 **Accept** 即可。

---

## 三、协作方式

### 方式一：GitHub 网页直接编辑（最简单，无需安装任何工具）

1. 登录 https://github.com/little-ran/hs-cloud-disk
2. 点进要改的文件（如 `seafile-custom/seafile.nginx.conf`）
3. 点右上角 **铅笔图标** ✏️ 编辑
4. 改完点 **Commit changes**
5. 填写提交说明，点 **Commit changes** 确认

> 适合：小改动、改配置、改文案

### 方式二：GitHub Desktop（图形界面，适合不熟命令行的人）

1. 下载安装 https://desktop.github.com/
2. 登录 GitHub 账号
3. Clone 仓库 `little-ran/hs-cloud-disk` 到本地
4. 在本地编辑文件
5. 在 GitHub Desktop 里写提交说明，点 **Commit to main**
6. 点 **Push origin** 推送到 GitHub

> 适合：批量改文件、需要本地编辑器

### 方式三：命令行（适合开发人员）

```bash
# 首次克隆
git clone https://github.com/little-ran/hs-cloud-disk.git
cd hs-cloud-disk

# 修改文件后提交
git add -A
git commit -m "修复：xxx问题"
git push origin main
```

> 注意：国内访问 GitHub 需开 VPN（见第六节）

---

## 四、修改流程规范

### 谁改什么

| 角色 | 可改 | 不可改 |
|------|------|--------|
| 所有人 | 前端JS、模板HTML、CSS、文案 | .env、密码、密钥 |
| 运维 | nginx配置、docker-compose、start.py | — |
| 开发 | seahub_settings.py、中间件 | 生产数据库 |

### 提交信息格式

```
<类型>：<简短描述>
```

| 类型 | 用途 | 示例 |
|------|------|------|
| 修复 | Bug修复 | `修复：下载token缓存失效` |
| 新增 | 新功能 | `新增：用户登录ID注入` |
| 同步 | 从服务器同步 | `同步：拉取最新nginx配置` |
| 安全 | 安全加固 | `安全：关闭注册功能` |
| 品牌 | 品牌定制 | `品牌：帮助页去除Seafile文案` |
| 清理 | 删除无用文件 | `清理：删除.bak备份` |

### 改动前必做

1. **先 Pull**：`git pull origin main`（确保拿到最新代码）
2. **小步提交**：一次改一个功能，不要攒一堆一起提交
3. **写清楚说明**：提交信息让人一看就知道改了什么

### 改动后必做

1. **Push**：`git push origin main`
2. **通知团队**：在群里说一声"改了xxx，已推送"
3. **如涉及服务器**：需要同步到 10.0.124.98 并重启容器

---

## 五、冲突处理

当两个人同时改了同一个文件：

```bash
git pull origin main
# 提示 conflict

# 打开冲突文件，找到 <<<<<<< 标记
# 手动选择保留哪部分，删除 <<<<<<< ======= >>>>>>> 标记

git add 冲突文件
git commit -m "合并：解决xxx冲突"
git push origin main
```

**避免冲突的原则**：改文件前先 `git pull`，改完尽快 `git push`。

---

## 六、网络与代理（国内访问 GitHub）

### 需要翻墙的场景

- `git clone` / `git push` / `git pull`（命令行）
- GitHub Desktop 推送

### 不需要翻墙的场景

- GitHub 网页浏览/编辑（浏览器走系统代理即可）
- 通过 MCP API 操作

### Hiddify VPN 代理配置

```bash
# 设置 git 代理（Hiddify mixed 端口 12334）
git config http.proxy http://127.0.0.1:12334
git config https.proxy http://127.0.0.1:12334

# 关闭代理
git config --unset http.proxy
git config --unset https.proxy
```

### 认证方式

GitHub 已不支持密码 push，需用 Personal Access Token：

1. 打开 https://github.com/settings/tokens
2. Generate new token (classic) → 勾选 `repo` → 生成
3. push 时输入用户名和 token（代替密码）
4. 或直接在 URL 里带 token（push 后记得清除）

---

## 七、服务器同步

代码仓库 ≠ 服务器运行配置。修改仓库后，如需生效到服务器：

```
GitHub 仓库          本地              服务器 10.0.124.98
    │                  │                    │
    │  git pull        │   SCP/SSH 推送     │
    │ <──────────────  │ ─────────────────> │
    │                  │                    │
    │                  │  docker compose    │
    │                  │  restart seafile   │
    │                  │ ─────────────────> │
```

### 从仓库部署到服务器

```bash
# 1. 本地拉取最新代码
cd D:/cloud/seafile-docker
git pull origin main

# 2. 推送到服务器（SCP 或 SSH）
scp seafile-custom/seafile.nginx.conf vsens@10.0.124.98:~/seafile-deploy/seafile-custom/

# 3. 重启容器使配置生效
ssh vsens@10.0.124.98 -p 22022
cd ~/seafile-deploy && docker compose restart seafile
```

### 从服务器同步到仓库

```bash
# 1. 从服务器拉取文件到本地
# （使用同步脚本或手动 SCP）

# 2. 提交到仓库
git add -A
git commit -m "同步：从服务器拉取最新配置"
git push origin main
```

---

## 八、备份与恢复

### 仓库本身就是备份

每次 `git push` 后，代码就备份在 GitHub 上了。即使本地文件丢失，`git clone` 即可恢复。

### 查看历史改动

```bash
git log --oneline                    # 所有提交历史
git log --oneline -10                # 最近10条
git show <commit-hash>               # 查看某次改了什么
git diff <commit-hash> HEAD          # 对比某次到现在的差异
```

### 恢复到某个版本

```bash
# 查看历史，找到要恢复的 commit
git log --oneline

# 恢复某个文件到指定版本
git checkout <commit-hash> -- seafile-custom/seafile.nginx.conf
git commit -m "回退：恢复nginx配置到xxx版本"
git push origin main
```

---

## 九、常见问题

### Q: push 报 "Authentication failed"
**A**: Token 过期了，去 https://github.com/settings/tokens 重新生成。

### Q: push 报 "SSL/TLS connection failed"
**A**: VPN 没开或断了，先开 Hiddify VPN 再 push。

### Q: pull 报 "conflict"
**A**: 两个人改了同一个文件。手动解决冲突（见第五节）。

### Q: 想撤销刚才的提交
**A**: `git reset HEAD~1`（保留改动）或 `git reset --hard HEAD~1`（丢弃改动）。

### Q: 怎么看谁改了什么
**A**: 在 GitHub 网页点 **Commits**，或 `git log --oneline --graph`。

### Q: 新队友怎么加入
**A**: 管理员在 https://github.com/little-ran/hs-cloud-disk/settings/access 添加。
