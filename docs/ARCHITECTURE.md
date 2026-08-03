# 系统架构

## 总体结构

项目采用单仓库、前后端分离、同域部署：

```text
Browser / PWA
      |
      | HTTP(S)
      v
    Caddy --------------------> React static assets
      |
      | /api/*, /admin/*
      v
Gunicorn + Django REST Framework
      |
      v
 PostgreSQL
```

同域部署允许 Web 客户端使用安全的 Session Cookie 和 Django CSRF 机制，不需要把长期令牌放入浏览器存储。

## 仓库边界

- `backend/`：Django、DRF、管理后台、数据库迁移和后端测试。
- `frontend/`：React、Vite、路由、查询缓存、PWA 和前端测试入口。
- `deploy/`：Caddy、生产镜像和运行配置。
- `scripts/`：备份、恢复和运维辅助脚本。
- `docs/`：产品、架构、数据、安全和 ADR。

## 生产运行时

- Caddy 是唯一公网入口，只发布 80 和 443。
- 前端由多阶段 Docker 构建生成静态文件，再复制到 Caddy 镜像。
- Django 由 Gunicorn `gthread` worker 运行，初始配置为 3 workers、每个 2 threads。
- Gunicorn 设置请求超时、`max-requests` 和抖动，降低长期进程内存增长风险。
- PostgreSQL 只加入内部 Compose 网络，使用命名卷持久化，初始最大连接数为 50。
- Django 数据库连接使用有限的 `CONN_MAX_AGE`；生产数据库最大连接数保持保守，并为管理与备份预留容量。
- 所有长期服务使用 `restart: unless-stopped` 和健康检查。

## 请求路径

- `/` 与前端路由：Caddy 提供 SPA 文件，并回退到 `index.html`。
- `/api/*`：Caddy 反向代理到 Gunicorn。
- `/admin/*`：Caddy 反向代理到 Django Admin。
- `/static/admin/*`：由构建阶段收集并交给 Caddy 提供。

## 认证与授权

- 第一阶段使用 Django Session Cookie。
- 登录前调用 CSRF 接口获得 CSRF Cookie；所有状态变更请求携带 `X-CSRFToken`。
- 默认 Cookie 为 `HttpOnly`、`SameSite=Lax`，生产环境启用 `Secure`。
- 公众注册关闭，账户由管理员创建。
- API 默认要求认证，只有登录、CSRF 和健康检查显式匿名开放。

## 内容架构

课程、课时、知识点、题目和背诵卡采用“稳定身份 + 不可变版本”模式。稳定实体承载引用关系；版本实体承载可发布内容。已发布版本不能修改，修订必须创建新草稿并重新审核。

课时正文由有序 `LessonContentBlock` 组成，不存为单个大文本字段。案例题使用组合题、分问、评分点和参考步骤模型，允许后续增加人工或半自动评分。

## 可观测性

- 应用日志输出到标准输出，容器平台负责收集和轮转。
- 存活检查只验证进程可响应。
- 就绪检查验证数据库可执行轻量查询。
- 日志不得包含密码、Session Cookie、CSRF Token、数据库密码或用户完整答案正文。
