import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { getChapters } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

export function PracticeChaptersPage() {
  const { subjectCode = "" } = useParams();
  const chapters = useQuery({
    queryKey: ["chapters", subjectCode],
    queryFn: () => getChapters(subjectCode),
  });

  return (
    <AppShell>
      <main className="dashboard-shell chapter-practice-shell">
        <Link className="back-link" to="/practice">← 返回刷题中心</Link>
        <PageHeader eyebrow="按章、按节定位" title={chapters.data?.subject || "章节练习"} />
        <p className="page-intro">每一节都显示题量、已做数量、当前错题和正确率；没有通过复核的题不会开放。</p>
        {chapters.isPending && <div className="card">正在读取章节题量…</div>}
        <div className="practice-chapter-list">
          {chapters.data?.chapters.map((chapter) => (
            <section className="practice-chapter" key={chapter.number}>
              <header>
                <div><span>第{chapter.number}章</span><h2>{chapter.title}</h2></div>
                <dl>
                  <div><dt>已做/总题</dt><dd>{chapter.attempted_questions}/{chapter.question_count}</dd></div>
                  <div><dt>错题</dt><dd>{chapter.wrong_count}</dd></div>
                </dl>
              </header>
              <div className="practice-section-list">
                {chapter.sections.map((section) => (
                  <article className="practice-section-row" key={section.id}>
                    <span className="practice-section-row__number">{chapter.number}.{section.number}</span>
                    <div>
                      <h3>{section.title}</h3>
                      <p>{section.knowledge_count}个精讲点 · {section.question_count}道已复核题</p>
                    </div>
                    <dl>
                      <div><dt>已做</dt><dd>{section.attempted_questions}/{section.question_count}</dd></div>
                      <div><dt>错题</dt><dd>{section.wrong_count}</dd></div>
                      <div><dt>正确率</dt><dd>{section.attempt_count ? `${section.accuracy}%` : "—"}</dd></div>
                    </dl>
                    <div className="practice-section-row__actions">
                      <Link to={`/study/section/${section.id}`}>学习本节</Link>
                      {section.question_count > 0 && <Link className="button" to={`/practice/session?section=${section.id}`}>开始做题</Link>}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>
    </AppShell>
  );
}
