import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";

import { ApiError } from "./api/client";
import { currentUserQuery } from "./auth";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";

function HomeRoute() {
  const currentUser = useQuery(currentUserQuery);

  if (currentUser.isPending) {
    return <div className="page-state">正在读取登录状态…</div>;
  }

  if (currentUser.error instanceof ApiError && [401, 403].includes(currentUser.error.status)) {
    return <Navigate to="/login" replace />;
  }

  if (currentUser.isError) {
    return <div className="page-state error-state">暂时无法连接服务，请稍后重试。</div>;
  }

  return <DashboardPage user={currentUser.data} />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
