# API 约定

## 路径与格式

- 业务 API 使用 `/api/v1/` 前缀。
- 健康检查使用 `/api/health/live/` 与 `/api/health/ready/`。
- 请求和响应正文使用 UTF-8 JSON。
- 资源路径使用复数、短横线和尾部斜杠。
- 时间使用带时区的 ISO 8601 字符串。

## 成功响应

单资源直接放在 `data`：

```json
{
  "data": {
    "id": "..."
  }
}
```

列表响应后续统一增加 `data`、`pagination` 和可选 `meta`。

## 错误响应

所有可预期错误使用统一结构：

```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "邮箱或密码不正确。",
    "field_errors": {}
  }
}
```

- `code` 是稳定机器码。
- `message` 是安全、可展示的中文说明。
- `field_errors` 只在字段校验失败时包含内容。
- 生产响应不得返回异常堆栈、SQL、内部路径或密钥。

## 认证与 CSRF

- `GET /api/v1/auth/csrf/`：设置 CSRF Cookie。
- `POST /api/v1/auth/login/`：建立 Session，只接受邮箱与密码。
- `POST /api/v1/auth/logout/`：销毁当前 Session。
- `GET /api/v1/auth/me/`：返回当前用户；匿名访问返回 `403 + not_authenticated`。
- 不提供注册端点。

前端发送非安全方法时读取 CSRF Cookie 并设置 `X-CSRFToken`。所有请求使用 `credentials: include`。

## 状态码

- `200`：读取或状态变更成功。
- `201`：资源创建成功。
- `204`：无响应正文的成功操作。
- `400`：请求格式或字段无效；登录凭据错误使用 `invalid_credentials`。
- `403`：Session API 未登录使用 `not_authenticated`，权限不足使用 `permission_denied`，CSRF 失败使用 `csrf_failed`。
- `404`：资源不存在或调用者不可见。
- `409`：版本冲突或幂等冲突。
- `422`：后续复杂业务规则校验失败时使用。
- `429`：请求过于频繁；登录限速使用 `login_rate_limited` 并返回 `Retry-After`。

## 兼容性

- 在 `/api/v1/` 内只做向后兼容的字段增加。
- 删除或改变字段语义需要新的 API 版本或明确弃用周期。
- 客户端必须忽略未知字段。
