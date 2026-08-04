import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { getDashboard, User } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";

export function DashboardPage({ user }: { user: User }) {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });

  return (
    <AppShell>
      <main className="dashboard-shell">
        <PageHeader eyebrow="今日学习" title={`你好，${user.display_name || "同学"}`} />
        {dashboard.isPending && <div className="card">正在生成今日计划…</div>}
        {dashboard.isError && <div className="card error-state">今日计划读取失败，请刷新重试。</div>}
        {dashboard.data && (
          <>
            <section className="exam-strip" aria-label="考试倒计时">
              <div><strong>{dashboard.data.exam.days_remaining}</strong><span>天后考试</span></div>
              <p>{dashboard.data.exam.location} · {dashboard.data.exam.specialty}</p>
              <small>{dashboard.data.exam.syllabus}</small>
            </section>
            <div className="home-grid">
              <Card className="today-focus">
                <p className="eyebrow">今天只抓一件事</p>
                <h2>{dashboard.data.next_section?.title || "开始第一组精编题"}</h2>
                <p>
                  {dashboard.data.next_section
                    ? `${dashboard.data.next_section.subject} · ${dashboard.data.next_section.chapter}`
                    : "先完成一组题，系统再根据结果安排复习。"}
                </p>
                <div className="progress-row">
                  <span>今日完成 {dashboard.data.today.answered}/{dashboard.data.today.target_questions} 题</span>
                  <span>正确率 {dashboard.data.today.accuracy}%</span>
                </div>
                <progress value={dashboard.data.today.answered} max={dashboard.data.today.target_questions} />
                <div className="primary-actions">
                  {dashboard.data.next_section && (
                    <Link className="button button--secondary" to={`/study/section/${dashboard.data.next_section.id}`}>先学重难点</Link>
                  )}
                  <Link className="button" to="/practice">开始今日20题</Link>
                </div>
              </Card>
              <Card className="compact-task">
                <p className="eyebrow">今日到期</p>
                <h2>{dashboard.data.today.due_reviews} 道错题</h2>
                <p>按间隔计划复习，不堆积。</p>
                <Link to="/practice?mode=review">开始复习</Link>
              </Card>
              <Card className="compact-task">
                <p className="eyebrow">可用内容</p>
                <h2>{dashboard.data.question_count} 道已复核题</h2>
                <p>仅展示通过发布门槛的内容。</p>
                <Link to="/study">查看四科目录</Link>
              </Card>
            </div>
          </>
        )}
      </main>
    </AppShell>
  );
}
