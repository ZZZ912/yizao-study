import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { getChapters } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

export function ChaptersPage() {
  const { subjectCode = "" } = useParams();
  const chapters = useQuery({
    queryKey: ["chapters", subjectCode],
    queryFn: () => getChapters(subjectCode),
  });
  return (
    <AppShell>
      <main className="dashboard-shell narrow-content">
        <Link className="back-link" to="/study">← 返回四科</Link>
        <PageHeader eyebrow="章节路径" title={chapters.data?.subject || "科目章节"} />
        <div className="chapter-list">
          {chapters.data?.chapters.map((chapter) => (
            <section className="chapter-group" key={chapter.number}>
              <header><span>第{chapter.number}章</span><h2>{chapter.title}</h2></header>
              <div>
                {chapter.sections.map((section) => (
                  <Link to={`/study/section/${section.id}`} className="section-row" key={section.id}>
                    <span>{chapter.number}.{section.number}</span>
                    <strong>{section.title}</strong>
                    <small>{section.knowledge_count} 个精讲点 · {section.question_count} 题</small>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>
    </AppShell>
  );
}
