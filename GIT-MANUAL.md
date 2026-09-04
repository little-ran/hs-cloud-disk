# HS云盘 Git 协作管理手册

> 仓库：https://github.com/little-ran/hs-cloud-disk（Public，分支保护+PR审查）
> 管理员：little-ran
> 服务器：10.0.124.98:8088

---

## 一、核心规则

**main 分支受保护，任何人不能直接 push。** 所有改动必须：
1. 创建分支 → 2. 提交 Pull Request → 3. 至少1人审查通过 → 4. 合并到 main

这是唯一入口，没有例外。这样能防止任何一个人改错配置把云盘搞挂。

---

## 二、协作者加入

### 管理员邀请队友

1. 打开 https://github.com/little-ran/hs-cloud-disk/settings/access
2. 点 **Add people**，输入队友 GitHub 用户名
3. 权限选 **Write**（可创建分支、提 PR）
4. 队友收到邮件 → Accept

### 队友首次操作

1. 注册 GitHub 账号（如果没有）
2. 接受邀请邮件
3. 打开 https://github.com/little-ran/hs-cloud-disk

---

## 三、改动流程（所有人必读）

### 方式一：GitHub 网页操作（无需安装任何工具）

1. 打开 https://github.com/little-ran/hs-cloud-disk
2. 点进要改的文件
3. 点右上角 **铅笔图标** ✏️ 编辑
4. 修改内容
5. 提交时选择 **Create a new branch**（不要提交到 main）
6. 填分支名如 `fix/nginx-cache`，点 **Propose changes**
7. 在 Pull Request 页面填写说明，点 **Create pull request**
8. 等待至少1人审查通过后点 **Merge pull request**

### 方式二：GitHub Desktop（图形界面）

1. 下载安装 https://desktop.github.com/
2. 登录 GitHub → Clone 仓库到本地
3. 创建新分支：点 **Current branch** → **New branch** → 命名如 `fix/nginx-cache`
4. 在本地编辑文件
5. 写提交说明 → **Commit to fix/nginx-cache**
6. 点 **Publish branch** 推送
7. 在 GitHub 网页上会出现 **Compare & pull request** → 点它 → **Create pull request**
8. 等1人审查通过后 **Merge**

### 方式三：命令行

```bash
# 克隆（首次）
git clone https://github.com/little-ran/hs-cloud-disk.git
cd hs-cloud-disk

# 创建分支（每次改动前）
git checkout -b fix/nginx-cache

# 修改文件后提交
git add -A
git commit -m "修复：nginx缓存配置"

# 推送分支
git push origin fix/nginx-cache

# 在 GitHub 网页上创建 Pull Request
# 等审查通过后合并
```

---

## 四、分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `fix/` | Bug修复 | `fix/download-403` |
| `feat/` | 新功能 | `feat/burn-after-read` |
| `sync/` | 从服务器同步 | `sync/nginx-config` |
| `sec/` | 安全加固 | `sec/disable-signup` |
| `brand/` | 品牌定制 | `brand/help-page` |
| `clean/` | 清理 | `clean/remove-bak` |

---

## 五、提交信息格式

```
<类型>：<简短描述>
```

| 类型 | 示例 |
|------|------|
| 修复 | `修复：下载token缓存失效` |
| 新增 | `新增：用户登录ID注入` |
| 同步 | `同步：拉取最新nginx配置` |
| 安全 | `安全：关闭注册功能` |
| 品牌 | `品牌：帮助页去除Seafile文案` |
| 清理 | `清理：删除.bak备份` |

---

## 六、PR 审查规范

### 审查者职责

1. **看改动内容**：点 Files changed，逐行看改了什么
2. **检查安全性**：有没有硬编码密码、有没有删错配置
3. **检查语法**：nginx 配置语法、Python 语法是否正确
4. **批准或打回**：点 Review changes → Approve（通过）或 Request changes（打回）

### 合并规则

- 至少 **1人 Approve** 才能合并
- 有 Request changes 必须先解决
- 合并方式选 **Squash and merge**（把多个提交压缩成1个）

### 审查时限

- 普通 PR：24小时内审查
- 紧急修复（影响线上）：立即审查

---

## 七、仓库结构

```
hs-cloud-disk/
├── .gitignore                    # 忽略规则
├── .env.example                  # 环境变量模板（进仓库，无真实密码）
├── .env                          # 真实环境变量（gitignore，不进仓库）
├── docker-compose.yml            # Docker 编排配置
├── GIT-MANUAL.md                 # 本文档
└── seafile-custom/               # 所有定制文件
    ├── seafile.nginx.conf        # nginx 配置
    ├── start.py                  # 容器启动脚本
    ├── seahub_settings.py        # seahub 配置
    ├── seafile.conf              # fileserver 配置
    ├── react_app.html            # 前端模板
    ├── *.js                      # 前端注入脚本
    └── ...                       # 品牌资源
```

### 敏感文件保护

| 文件 | 状态 | 说明 |
|------|------|------|
| `.env` | gitignore | 含数据库/管理员密码 |
| `.admin_passwd` | gitignore | nginx Basic Auth |
| `seahub_settings.py` 里的 SECRET_KEY | 改为环境变量 | `os.environ.get('SEAHUB_SECRET_KEY')` |
| `docker-compose.yml` 里的密码 | `${}`引用 | 指向 .env，不硬编码 |

---

## 八、网络与认证

> 国内访问 GitHub 可能需要挂代理，请自行解决网络问题。GitHub 网页操作通常无需额外配置，命令行 push/pull 如遇连接失败请检查网络。

### 认证（Token）

GitHub 不支持密码 push，需用 Personal Access Token：

1. https://github.com/settings/tokens → Generate new token (classic) → 勾选 `repo`
2. push 时用户名填 GitHub 用户名，密码填 token

---

## 九、服务器同步

代码合并到 main 后，如需部署到服务器：

```bash
# 1. 本地拉取最新
cd D:/cloud/seafile-docker
git pull origin main

# 2. 推送到服务器
scp -P 22022 seafile-custom/xxx vsens@10.0.124.98:~/seafile-deploy/seafile-custom/

# 3. 重启容器
ssh -p 22022 vsens@10.0.124.98
cd ~/seafile-deploy && docker compose restart seafile
```

> 部署到服务器属于运维操作，仅管理员执行。

---

## 十、常见问题

### Q: 为什么不能直接 push 到 main？
**A**: main 分支已保护。必须走 PR 流程，至少1人审查通过才能合并。这是为了防止误操作。

### Q: 我是管理员也不能直接 push？
**A**: 对，分支保护对所有人生效（enforce_admins=false 意味着管理员也受约束）。如需紧急修复，管理员可在 GitHub 网页临时关闭分支保护，改完再开。

### Q: push 报 "Authentication failed"
**A**: Token 过期，去 https://github.com/settings/tokens 重新生成。

### Q: push 报 "SSL/TLS connection failed"
**A**: 网络问题，可能需要挂代理访问 GitHub。

### Q: 怎么看谁改了什么
**A**: GitHub 网页点 **Commits** 或 **Pull requests**。

### Q: 新队友怎么加入
**A**: 管理员在 Settings → Access 添加，队友 Accept 邀请后即可提 PR。
