# ADR 0005：4 核 4 GB 生产资源预算

- 状态：已接受
- 日期：2026-08-03

## 决策

第一阶段不引入 Redis、Celery 或 Elasticsearch。Gunicorn 使用 3 个 `gthread` worker、每个 2 threads；数据库连接池保持保守，PostgreSQL、Django 与 Caddy 共享单机资源。

## 原因

常见的 `2 * CPU + 1` worker 公式可能使 4 GB 机器内存压力过大。当前业务以普通 API 和管理后台为主，3 个 worker 足以提供并发余量。

## 后果

需要通过真实流量监控再调整 worker、线程和数据库连接。耗时任务在后续阶段引入队列前只能设计为短事务或受控离线命令。

