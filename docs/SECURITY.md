# 安全设计

## 身份认证

- 第一阶段禁止公众注册，只允许管理员创建账户。
- 生产环境使用安全 Session Cookie：`HttpOnly`、`Secure`、`SameSite=Lax`。
- 所有状态变更接口执行 CSRF 验证。
- 登录失败统一返回相同错误，避免枚举邮箱。
- Django Admin 只允许 `is_staff` 用户访问，后续部署应增加来源限制或单独身份层。

## 内容安全

- Markdown 原始 HTML 默认关闭。
- 清洗器采用标签、属性和 URL 协议允许列表。
- KaTeX 使用严格模式与受控宏。
- 用户输入不得直接进入 `dangerouslySetInnerHTML`。
- 上传功能不在第一阶段范围；启用前必须增加文件类型、大小、恶意内容和存储隔离策略。

## 密钥与配置

- `.env`、私钥、数据库转储、备份校验文件和生产日志不得提交 Git。
- 仓库只提供无真实值的 `.env.example`。
- Django `SECRET_KEY` 和数据库密码必须由运行环境注入。
- CI 执行敏感文件名和私钥头检查。
- 生产环境必须设置 `DEBUG=False` 和明确的 `ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS`。

## 网络与容器

- 只有 Caddy 映射宿主机 80/443。
- Gunicorn 和 PostgreSQL 仅使用内部网络与 `expose`，不得使用宿主机 `ports`。
- 容器镜像使用明确版本，不使用 `latest`。
- 应用容器尽量使用非 root 用户，并限制可写目录。
- Docker 发布端口可能绕过主机 UFW；生产 Compose 的端口映射必须经过评审。

## 数据保护

- 学习数据按用户隔离，API 查询必须包含所有者约束。
- 答案、笔记和考试记录不写入常规请求日志。
- 管理与审核操作保留操作者和时间审计信息。
- 备份使用 gzip 压缩、SHA256 校验和限制权限，并定期做恢复演练。

## 依赖与 CI

- Python 与 Node 依赖锁定明确版本。
- CI 运行格式、测试、类型检查、生产构建和敏感文件检查。
- 依赖升级通过独立 PR 进行，避免未审查的大版本升级。

