# ADR 0002：Session Cookie 认证与关闭公众注册

- 状态：已接受
- 日期：2026-08-03

## 决策

同域 Web/PWA 使用 Django Session Cookie 和 CSRF，不签发存储在 localStorage 的 JWT。第一阶段关闭公众注册，只允许管理员创建用户。

## 原因

Session 能直接利用 Django 的成熟安全机制，降低令牌泄露、刷新和撤销复杂度。管理员创建用户符合封闭试运行阶段需求。

## 后果

客户端必须先获取 CSRF Cookie，并在状态变更请求中发送 CSRF Header。未来邀请注册应复用用户模型，并通过一次性、有期限的邀请记录实现。

