import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { getWrongQuestions } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

export function ReviewPage() {
  const wrong = useQuery({ queryKey: ["wrong-questions"], queryFn: getWrongQuestions });
  return (
    <AppShell>
      <main className="dashboard-shell narrow-content">
        <PageHeader eyebrow="错题复习" title="今日复习" actions={<Link className="button" to="/practice?mode=review">开始到期复习</Link>} />
        <p className="page-intro">答错后第 1、2、4、7 天逐步巩固；连续答对三次后转为已掌握。</p>
        <div className="wrong-list">
          {wrong.data?.map((item) => (
            <article className="wrong-row" key={item.id}>
              <div><span>{item.subject} · {item.section}</span><h2>{item.stem}</h2></div>
              <dl><div><dt>错误</dt><dd>{item.wrong_count}次</dd></div><div><dt>连续答对</dt><dd>{item.correct_streak}次</dd></div></dl>
            </article>
          ))}
          {wrong.data?.length === 0 && <div className="card"><h2>还没有错题</h2><p>先完成今日练习，系统会自动建立复习计划。</p></div>}
        </div>
      </main>
    </AppShell>
  );
}
