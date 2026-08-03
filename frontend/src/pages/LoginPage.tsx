import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Navigate, useNavigate } from "react-router";

import { ApiError, loginUser } from "../api/client";
import { currentUserQuery } from "../auth";
import { Button } from "../components/ui/Button";
import { FormField } from "../components/ui/FormField";

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData(currentUserQuery.queryKey);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (user) => {
      queryClient.setQueryData(currentUserQuery.queryKey, user);
      navigate("/", { replace: true });
    },
  });

  if (currentUser) {
    return <Navigate to="/" replace />;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginMutation.mutate({ email, password });
  }

  const errorMessage =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.message
      : loginMutation.isError
        ? "登录失败，请稍后重试。"
        : null;

  return (
    <main className="auth-shell">
      <section className="brand-panel" aria-labelledby="brand-heading">
        <p className="eyebrow">一级造价工程师学习平台</p>
        <h1 id="brand-heading">一造学伴</h1>
        <p>把章节培训、知识记忆与复习节奏整理成一条清晰的学习路径。</p>
      </section>

      <section className="login-card" aria-labelledby="login-heading">
        <div>
          <p className="eyebrow">管理员已创建账户</p>
          <h2 id="login-heading">登录学习空间</h2>
        </div>

        <form onSubmit={handleSubmit}>
          <FormField
            id="email"
            name="email"
            label="邮箱"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <FormField
            id="password"
            name="password"
            label="密码"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {errorMessage ? <p className="form-error" role="alert">{errorMessage}</p> : null}
          <Button type="submit" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "正在登录…" : "登录"}
          </Button>
        </form>

        <p className="helper-text">第一阶段不开放公众注册，请联系管理员创建账户。</p>
      </section>
    </main>
  );
}
