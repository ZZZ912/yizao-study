import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";

import { getLearningReport } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

type RecordFilter = "all" | "correct" | "wrong";

export function PracticeRecordsPage() {
  const [filter, setFilter] = useState<RecordFilter>("all");
  const report = useQuery({ queryKey: ["learning-report"], queryFn: getLearningReport });
  const records = (report.data?.recent_attempts || []).filter((attempt) => (
    filter === "all" || (filter === "correct" ? attempt.is_correct : !attempt.is_correct)
  ));

  return (
    <AppShell>
      <main className="dashboard-shell records-shell">
        <Link className="back-link" to="/practice">← 返回刷题中心</Link>
        <PageHeader eyebrow="最近50次作答" title="练习记录" actions={<Link className="button button--secondary" to="/report">查看学习报告</Link>} />
        <div className="record-filters" role="group" aria-label="筛选练习记录">
          {([ ["all", "全部"], ["correct", "答对"], ["wrong", "答错"] ] as const).map(([value, label]) => (
            <button className={filter === value ? "is-active" : ""} type="button" onClick={() => setFilter(value)} key={value}>{label}</button>
          ))}
        </div>
        <div className="record-list">
          {records.map((attempt) => (
            <article className="record-row" key={attempt.id}>
              <span className={attempt.is_correct ? "record-result is-correct" : "record-result is-wrong"}>{attempt.is_correct ? "对" : "错"}</span>
              <div>
                <p>{attempt.subject} · {attempt.section}</p>
                <h2>{attempt.stem}</h2>
                <small>{new Date(attempt.created_at).toLocaleString("zh-CN")} · 用时{attempt.elapsed_seconds}秒</small>
              </div>
              <dl>
                <div><dt>你的答案</dt><dd>{attempt.selected_answer.join("、")}</dd></div>
                <div><dt>正确答案</dt><dd>{attempt.correct_answer.join("、")}</dd></div>
              </dl>
            </article>
          ))}
          {!report.isPending && records.length === 0 && <div className="card"><h2>当前筛选下没有记录</h2><p>完成练习后，每次答案和用时都会保留在这里。</p></div>}
        </div>
      </main>
    </AppShell>
  );
}
