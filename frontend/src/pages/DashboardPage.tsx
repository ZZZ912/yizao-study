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
            <section className="daily-overview" aria-label="今日学习进度">
              <div>
                <span>总课程进度</span>
                <strong>{dashboard.data.course_progress}%</strong>
              </div>
              <progress value={dashboard.data.completed_section_count} max={dashboard.data.section_count || 1} />
              <small>{dashboard.data.completed_section_count}/{dashboard.data.section_count} 节已完成</small>
            </section>
            <div className="home-grid home-grid--expanded">
              <Card className="today-focus">
                <p className="eyebrow">今天只抓一件事</p>
                <h2>{dashboard.data.next_section?.title || "开始第一组精编题"}</h2>
                <p>
                  {dashboard.data.next_section
                    ? `${dashboard.data.next_section.subject} · ${dashboard.data.next_section.chapter}`
                    : "先完成一组题，系统再根据结果安排复习。"}
                </p>
                {dashboard.data.next_section && (
                  <p className="focus-detail">
                    {dashboard.data.next_section.knowledge_count}个精讲点 · 预计{dashboard.data.next_section.estimated_minutes}分钟
                  </p>
                )}
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
              <Card className="daily-plan-card">
                <p className="eyebrow">今日三步</p>
                <ol className="daily-checklist">
                  <li className={dashboard.data.today.completed_lessons > 0 ? "is-done" : ""}>
                    <span>{dashboard.data.today.completed_lessons > 0 ? "✓" : "1"}</span>
                    <div><strong>学一节重难点</strong><small>理解后再刷题</small></div>
                  </li>
                  <li className={dashboard.data.today.answered >= dashboard.data.today.target_questions ? "is-done" : ""}>
                    <span>{dashboard.data.today.answered >= dashboard.data.today.target_questions ? "✓" : "2"}</span>
                    <div><strong>完成20道精编题</strong><small>已完成{dashboard.data.today.answered}题</small></div>
                  </li>
                  <li className={dashboard.data.today.due_reviews === 0 ? "is-done" : ""}>
                    <span>{dashboard.data.today.due_reviews === 0 ? "✓" : "3"}</span>
                    <div><strong>清空到期复习</strong><small>{dashboard.data.today.due_reviews}道待复习</small></div>
                  </li>
                </ol>
              </Card>
              {dashboard.data.quick_card && (
                <Card className="memory-card-preview">
                  <p className="eyebrow">60秒记忆卡</p>
                  <span>{dashboard.data.quick_card.subject.title}</span>
                  <h2>{dashboard.data.quick_card.title}</h2>
                  <p>{dashboard.data.quick_card.summary}</p>
                  <Link to="/quick-study">开始碎片学习</Link>
                </Card>
              )}
              <div className="compact-task-grid">
                <Card className="compact-task">
                  <p className="eyebrow">今日到期</p>
                  <h2>{dashboard.data.today.due_reviews} 道错题</h2>
                  <p>按1/2/4/7天间隔复习。</p>
                  <Link to="/practice?mode=review">开始复习</Link>
                </Card>
                <Card className="compact-task">
                  <p className="eyebrow">可学内容</p>
                  <h2>{dashboard.data.knowledge_count} 个精讲点</h2>
                  <p>{dashboard.data.question_count}道已复核题，四科持续补充。</p>
                  <Link to="/study">进入四科目录</Link>
                </Card>
              </div>
            </div>
          </>
        )}
      </main>
    </AppShell>
  );
}
