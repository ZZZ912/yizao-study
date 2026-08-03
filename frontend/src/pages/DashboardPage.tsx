import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router";

import { logoutUser, User } from "../api/client";
import { currentUserQuery } from "../auth";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Dialog } from "../components/ui/Dialog";

export function DashboardPage({ user }: { user: User }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const closeDialog = useCallback(() => setDialogOpen(false), []);
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
    <AppShell>
      <main className="dashboard-shell">
        <PageHeader
          eyebrow="Phase 1 Foundation"
          title="学习空间"
          actions={
            <>
              <Button variant="ghost" type="button" onClick={() => setDialogOpen(true)}>关于</Button>
              <Button
                variant="secondary"
                type="button"
                onClick={() => logoutMutation.mutate()}
                disabled={logoutMutation.isPending}
              >
                退出登录
              </Button>
            </>
          }
        />
        <div className="foundation-layout">
          <Card className="foundation-main">
            <p className="eyebrow">基础骨架</p>
            <h2>你好，{user.display_name || user.email}</h2>
            <p>账户、导航和部署骨架已经就绪。课程、刷题与复习功能将在后续阶段逐步接入。</p>
          </Card>
          <Card className="foundation-support">
            <h2>当前版本</h2>
            <p>{__APP_VERSION__}</p>
          </Card>
          <details className="card foundation-aside">
            <summary>辅助区域</summary>
            <p>宽屏显示三栏；较窄屏幕会按规则自动收起。</p>
          </details>
        </div>
      </main>
      <Dialog isOpen={dialogOpen} onClose={closeDialog} title="关于一造学伴">
        <p>这是第一阶段的可访问性与响应式基础组件示例。</p>
        <Button type="button" onClick={closeDialog}>知道了</Button>
      </Dialog>
    </AppShell>
  );
}
