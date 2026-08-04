import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router";

import { ApiError } from "./api/client";
import { currentUserQuery } from "./auth";
import { PwaStatus } from "./components/pwa/PwaStatus";
import { ChaptersPage } from "./pages/ChaptersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { LearningReportPage } from "./pages/LearningReportPage";
import { PracticeCenterPage } from "./pages/PracticeCenterPage";
import { PracticeChaptersPage } from "./pages/PracticeChaptersPage";
import { PracticePage } from "./pages/PracticePage";
import { PracticeRecordsPage } from "./pages/PracticeRecordsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { QuickStudyPage } from "./pages/QuickStudyPage";
import { ReviewPage } from "./pages/ReviewPage";
import { SectionPage } from "./pages/SectionPage";
import { StudyPage } from "./pages/StudyPage";

function AuthenticatedApp() {
  const currentUser = useQuery(currentUserQuery);

  if (currentUser.isPending) return <div className="page-state">正在读取学习档案…</div>;
  if (currentUser.error instanceof ApiError && [401, 403].includes(currentUser.error.status)) {
    return <Navigate to="/login" replace />;
  }
  if (currentUser.isError) {
    return <div className="page-state error-state">暂时无法连接服务，请稍后重试。</div>;
  }

  return (
    <Routes>
      <Route path="/" element={<DashboardPage user={currentUser.data} />} />
      <Route path="/study" element={<StudyPage />} />
      <Route path="/study/:subjectCode" element={<ChaptersPage />} />
      <Route path="/study/section/:sectionId" element={<SectionPage />} />
      <Route path="/quick-study" element={<QuickStudyPage />} />
      <Route path="/practice" element={<PracticeCenterPage />} />
      <Route path="/practice/session" element={<PracticePage />} />
      <Route path="/practice/chapters/:subjectCode" element={<PracticeChaptersPage />} />
      <Route path="/practice/records" element={<PracticeRecordsPage />} />
      <Route path="/review" element={<ReviewPage />} />
      <Route path="/report" element={<LearningReportPage />} />
      <Route path="/profile" element={<ProfilePage user={currentUser.data} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <>
      <PwaStatus />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<AuthenticatedApp />} />
      </Routes>
    </>
  );
}
