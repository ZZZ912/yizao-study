import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { Link } from "react-router";

import { logoutUser, User } from "../api/client";
import { currentUserQuery } from "../auth";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

export function ProfilePage({ user }: { user: User }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const logout = useMutation({ mutationFn: logoutUser, onSuccess: () => {
    queryClient.removeQueries({ queryKey: currentUserQuery.queryKey });
    navigate("/login", { replace: true });
  }});
  return (
    <AppShell><main className="dashboard-shell narrow-content">
      <PageHeader eyebrow="学习档案" title="我的" />
      <Card><h2>{user.display_name || "学习者"}</h2><p>{user.email}</p><p>目标：2026 一级造价工程师 · 土木建筑工程 · 湖北武汉</p><div className="primary-actions"><Link className="button" to="/report">学习报告</Link><Link className="button button--secondary" to="/practice/records">练习记录</Link></div><Button variant="secondary" type="button" onClick={() => logout.mutate()}>退出登录</Button></Card>
    </main></AppShell>
  );
}
