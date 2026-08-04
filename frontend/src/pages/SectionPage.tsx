import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { ContentBlock, getSection, updateSectionProgress } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

const blockLabels: Record<string, string> = {
  key_point: "必背结论",
  formula: "公式",
  warning: "易错提示",
  comparison: "对比辨析",
  mnemonic: "记忆口诀",
  example: "典型例题",
  case: "工程案例",
  summary: "小结",
  introduction: "导学",
  markdown: "讲解",
  inline_quiz: "课中练习",
};

function LearningBlock({ block }: { block: ContentBlock }) {
  return (
    <section className={`learning-block learning-block--${block.type}`}>
      <span>{blockLabels[block.type] || "知识点"}</span>
      <p>{block.content}</p>
    </section>
  );
}

export function SectionPage() {
  const { sectionId = "" } = useParams();
  const queryClient = useQueryClient();
  const section = useQuery({ queryKey: ["section", sectionId], queryFn: () => getSection(sectionId) });
  const completeSection = useMutation({
    mutationFn: () => updateSectionProgress(sectionId, "completed"),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["section", sectionId] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["subjects"] }),
        queryClient.invalidateQueries({ queryKey: ["chapters"] }),
      ]);
    },
  });
  return (
    <AppShell>
      <main className="dashboard-shell lesson-page">
        {section.data && (
          <>
            <Link className="back-link" to={`/study/${section.data.subject.code}`}>← 返回章节</Link>
            <PageHeader eyebrow={`${section.data.subject.title} · 第${section.data.chapter.number}章`} title={section.data.title} />
            <div className="lesson-layout">
              <article className="lesson-content">
                {section.data.knowledge_points.length === 0 && (
                  <div className="card"><h2>本节内容正在精编</h2><p>可先进入章节练习，未复核内容不会展示。</p></div>
                )}
                {section.data.knowledge_points.map((point, pointIndex) => (
                  <details className="knowledge-article" key={point.id} open={pointIndex === 0 ? true : undefined}>
                    <summary>
                      <span>{String(pointIndex + 1).padStart(2, "0")}</span>
                      <div><h2>{point.title}</h2><p>{point.summary}</p></div>
                    </summary>
                    <div className="knowledge-article__body">
                      <p className="eyebrow">{point.exam_edition}</p>
                      {point.content_blocks.map((block, index) => <LearningBlock block={block} key={`${point.id}-${index}`} />)}
                    </div>
                  </details>
                ))}
              </article>
              <aside className="lesson-action card">
                <p className="eyebrow">即时巩固</p>
                <h2>{section.data.question_count} 道已复核题</h2>
                <p>{section.data.knowledge_points.length}个精讲点。读完后标记完成，首页会自动安排下一节。</p>
                <button
                  className="button button--secondary"
                  disabled={completeSection.isPending || section.data.progress?.status === "completed"}
                  onClick={() => completeSection.mutate()}
                >
                  {section.data.progress?.status === "completed" ? "✓ 本节已完成" : "完成本节学习"}
                </button>
                <Link className="button" to={`/practice/session?section=${section.data.id}`}>练本节题目</Link>
              </aside>
            </div>
          </>
        )}
      </main>
    </AppShell>
  );
}
