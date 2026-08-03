import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";

import { logoutUser, User } from "../api/client";
import { currentUserQuery } from "../auth";

export function DashboardPage({ user }: { user: User }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const logoutMutation = useMutation({
    mutationFn: logoutUser,
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: currentUserQuery.queryKey });
      navigate("/login", { replace: true });
    },
  });

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">一造学伴</p>
          <strong>{user.display_name || user.email}</strong>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
        >
          退出登录
        </button>
      </header>

      <section className="dashboard-card">
        <p className="eyebrow">Phase 1 Foundation</p>
        <h1>学习仪表盘</h1>
        <p>账户与部署骨架已经就绪。课程、刷题、复习和统计模块将在后续阶段逐步接入。</p>
      </section>
    </main>
  );
}
