# 一造学伴

## 私有内容导入

题库导入默认只执行 dry-run，只有显式 `--commit` 才写入数据库。商业资料、完整提取结果和私有报告不得提交到本公开仓库。

```bash
cd backend
python manage.py validate_content ../private-data/incoming/batch/questions.jsonl
python manage.py import_content ../private-data/incoming/batch/questions.jsonl --dry-run
```

详见[内容导入流程](docs/CONTENT_INGESTION.md)、[来源政策](docs/SOURCE_POLICY.md)和[内容质检](docs/CONTENT_QA.md)。

面向一级造价工程师的章节培训、知识学习、智能刷题与复习平台。本分支只建立第一阶段工程基础，不包含完整课程、题库或案例题答题界面。

## 当前范围

- Django 5.2 LTS、PostgreSQL、自定义用户模型、Session Cookie 登录、CSRF、Admin 与健康检查。
- React、TypeScript、Vite、React Router、TanStack Query、响应式应用壳、登录页和可控更新的基础 PWA。
- 开发/生产 Compose、Gunicorn、Caddy 静态文件与反向代理、数据库备份恢复脚本。
- 产品、架构、数据、内容、安全、API、路线图和关键 ADR。

公众注册关闭。用户由管理员通过 Django Admin 创建；已发布内容的版本化模型在文档中定义，业务模型与页面将在后续阶段实现。

## Docker 本地启动

开发环境只将 Caddy 的 `8080` 端口发布到宿主机；PostgreSQL、Django 和 Vite 均只存在于内部网络。

```bash
docker compose up --build
docker compose exec backend python manage.py createsuperuser
```

访问：

- 应用：<http://localhost:8080>
- 管理后台：<http://localhost:8080/admin/>
- 存活检查：<http://localhost:8080/api/health/live/>
- 就绪检查：<http://localhost:8080/api/health/ready/>

停止环境：

```bash
docker compose down
```

## 不使用 Docker 的本地开发

后端（Python 3.12.13）：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --requirement requirements/dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

前端（Node.js 24.14.0、pnpm 11.9.0）：

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

## 测试与检查

```bash
cd backend
ruff format --check .
ruff check .
python manage.py makemigrations --check --dry-run
pytest

cd ../frontend
pnpm typecheck
pnpm build
pnpm e2e

cd ..
bash scripts/check-secrets.sh
```

CI 还会在 PostgreSQL 上运行后端测试，执行依赖审计、ShellCheck、Compose/Caddy 校验、固定版本 Gitleaks 全历史扫描、生产镜像构建，以及 360/390/768/1366/1440 视口的 Playwright 截图、横向溢出和 CSS 200% 缩放重排模拟。截图只作为临时 CI Artifact 保存。

## 生产 Compose

先复制环境变量示例并替换全部 `change-me` 值、域名和可信来源：

```bash
cp .env.example .env
docker compose --env-file .env -f docker-compose.prod.yml config
docker build --target production -t yizao-backend:predeploy backend
docker build -f deploy/caddy/Dockerfile -t yizao-caddy:predeploy .
docker run --rm -e SITE_ADDRESS=example.com -v "$PWD/deploy/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2.10.2-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose --env-file .env -f docker-compose.prod.yml run --rm --no-deps --entrypoint python backend manage.py check --deploy --fail-level ERROR
docker compose --env-file .env -f docker-compose.prod.yml run --rm --no-deps --entrypoint python backend manage.py migrate --check
docker compose --env-file .env -f docker-compose.prod.yml up --build -d
docker compose --env-file .env -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

生产环境仅 Caddy 发布 `80`、`443/tcp` 和 `443/udp`。前端在镜像构建阶段生成，由 Caddy 直接提供；运行时没有 Node 服务。Gunicorn 默认采用 3 个 `gthread` worker、每个 2 线程，适合先在 4 核 4 GB 主机上保守运行，再根据指标调整。

## 数据库备份与恢复

备份脚本通过生产 Compose 中的 PostgreSQL 容器执行 `pg_dump`，生成 gzip 压缩文件和 SHA256 校验文件。默认保留 7 份日备份；每个 UTC 周日从日备份复制一份周备份并保留 4 份。`ENV_FILE`、`COMPOSE_FILE` 和 `BACKUP_DIR` 均可显式指定：

```bash
ENV_FILE=.env BACKUP_DIR=/srv/yizao-backups bash scripts/backup-db.sh
```

恢复具有破坏性，必须提供明确确认值。脚本会验证 SHA256 和 gzip 完整性、停止 Backend、创建恢复前安全备份、使用单事务导入，并在恢复后检查迁移与就绪状态：

```bash
RESTORE_CONFIRM=restore ENV_FILE=.env bash scripts/restore-db.sh backups/daily/yizao-study-YYYYMMDDTHHMMSSZ.sql.gz
```

单事务保证 SQL 导入失败时整体回滚。若导入后的迁移或就绪检查失败，脚本不会自动再次导入安全备份；应先保持维护状态、核查原因，再由运维人员明确执行恢复。

可在隔离的临时 PostgreSQL 容器中执行“备份→修改→恢复→核对”演练：

```bash
bash scripts/test-backup-restore.sh
```

服务器本机备份不等于异地备份。正式运营前还需建立加密异地副本、监控和定期恢复记录。

真实 `.env`、密钥和备份均被 Git 忽略，不应提交。

## 文档

- [产品需求](docs/PRODUCT_REQUIREMENTS.md)
- [系统架构](docs/ARCHITECTURE.md)
- [数据模型](docs/DATA_MODEL.md)
- [内容模型](docs/CONTENT_MODEL.md)
- [API 约定](docs/API_CONVENTIONS.md)
- [安全设计](docs/SECURITY.md)
- [路线图](docs/ROADMAP.md)
- [竞品拆解](docs/COMPETITOR_ANALYSIS.md)
- [信息架构](docs/INFORMATION_ARCHITECTURE.md)
- [UX 原则](docs/UX_PRINCIPLES.md)
- [响应式设计](docs/RESPONSIVE_DESIGN.md)
- [设计系统](docs/DESIGN_SYSTEM.md)
- [页面流程](docs/SCREEN_FLOWS.md)
- [中保真原型与截图](docs/prototypes/README.md)
- [架构决策记录](docs/adr/)
