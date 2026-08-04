import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { getSubjects } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

export function StudyPage() {
  const subjects = useQuery({ queryKey: ["subjects"], queryFn: getSubjects });
  return (
    <AppShell>
      <main className="dashboard-shell">
        <PageHeader eyebrow="2026 · 土木建筑工程" title="四科学习" />
        <p className="page-intro">先理解，再做题。每科只展示当前可学习的章节和已复核内容。</p>
        <div className="subject-grid">
          {subjects.data?.map((subject, index) => (
            <Link className="subject-card" to={`/study/${subject.code}`} key={subject.id}>
              <span className="subject-index">0{index + 1}</span>
              <div>
                <h2>{subject.title}</h2>
                <p>{subject.knowledge_count} 个精讲点 · {subject.question_count} 道已复核题</p>
              </div>
              <span aria-hidden="true">→</span>
            </Link>
          ))}
        </div>
        {subjects.isPending && <div className="card">正在读取科目…</div>}
      </main>
    </AppShell>
  );
}
