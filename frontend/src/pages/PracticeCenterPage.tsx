import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { getLearningReport } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

const practiceTools = [
  { label: "今日20题", description: "优先未做题，完成后立即看解析", meta: "约20分钟", to: "/practice/session?mode=daily&target=20", tone: "primary" },
  { label: "限时训练", description: "20道随机题，训练节奏和取舍", meta: "建议25分钟", to: "/practice/session?mode=random&target=20&timed=1", tone: "timed" },
  { label: "随机练习", description: "从已复核题中随机抽取，不限数量", meta: "随时退出", to: "/practice/session?mode=random", tone: "default" },
  { label: "错题重做", description: "重做所有未掌握错题，不受日期限制", meta: "针对薄弱项", to: "/practice/session?mode=wrong", tone: "review" },
  { label: "到期复习", description: "按1、2、4、7天间隔清理到期错题", meta: "防止遗忘", to: "/practice/session?mode=review", tone: "review" },
  { label: "练习记录", description: "查看每次作答、答案、用时和错因", meta: "完整留痕", to: "/practice/records", tone: "default" },
];

export function PracticeCenterPage() {
  const report = useQuery({ queryKey: ["learning-report"], queryFn: getLearningReport });
  const data = report.data;

  return (
    <AppShell>
      <main className="dashboard-shell practice-center-shell">
        <PageHeader
          eyebrow="练习、诊断、再巩固"
          title="刷题中心"
          actions={<Link className="button" to="/practice/session?mode=daily&target=20">开始今日20题</Link>}
        />
        <p className="page-intro">按章节定位、按错因复盘。当前只开放答案和解析已经复核的题目。</p>

        {report.isPending && <div className="card">正在读取练习档案…</div>}
        {report.isError && <div className="card error-state">练习数据读取失败，请稍后重试。</div>}
        {data && (
          <>
            <section className="practice-overview" aria-label="练习总览">
              <div><span>已复核题</span><strong>{data.overview.question_count}</strong></div>
              <div><span>已练题目</span><strong>{data.overview.attempted_questions}</strong></div>
              <div><span>累计作答</span><strong>{data.overview.attempt_count}</strong></div>
              <div><span>正确率</span><strong>{data.overview.accuracy}%</strong></div>
              <div><span>未掌握错题</span><strong>{data.overview.active_wrong}</strong></div>
              <div><span>今日到期</span><strong>{data.overview.due_reviews}</strong></div>
            </section>

            <section aria-labelledby="practice-modes-title">
              <div className="section-heading">
                <div><p className="eyebrow">训练方式</p><h2 id="practice-modes-title">今天想怎么练</h2></div>
                <Link to="/report">查看学习报告 →</Link>
              </div>
              <div className="practice-tool-grid">
                {practiceTools.map((tool, index) => (
                  <Link className={`practice-tool practice-tool--${tool.tone}`} to={tool.to} key={tool.label}>
                    <span className="practice-tool__index">{String(index + 1).padStart(2, "0")}</span>
                    <div><h3>{tool.label}</h3><p>{tool.description}</p><small>{tool.meta}</small></div>
                    <span aria-hidden="true">→</span>
                  </Link>
                ))}
              </div>
            </section>

            <section className="subject-practice-section" aria-labelledby="subject-practice-title">
              <div className="section-heading">
                <div><p className="eyebrow">章节练习</p><h2 id="subject-practice-title">按科目查缺补漏</h2></div>
                <span>已做 / 总题 · 错题 · 正确率</span>
              </div>
              <div className="subject-practice-list">
                {data.subjects.map((subject) => (
                  <article className="subject-practice-row" key={subject.code}>
                    <div className="subject-practice-row__title">
                      <h3>{subject.title}</h3>
                      <p>{subject.completed_sections}/{subject.section_count}节已学 · 课程进度{subject.course_progress}%</p>
                    </div>
                    <dl>
                      <div><dt>已做/总题</dt><dd>{subject.attempted_questions}/{subject.question_count}</dd></div>
                      <div><dt>错题</dt><dd>{subject.wrong_count}</dd></div>
                      <div><dt>正确率</dt><dd>{subject.attempt_count ? `${subject.accuracy}%` : "—"}</dd></div>
                    </dl>
                    {subject.question_count ? (
                      <Link className="button button--secondary" to={`/practice/chapters/${subject.code}`}>章节练习</Link>
                    ) : (
                      <Link className="button button--ghost" to={`/study/${subject.code}`}>先学精讲</Link>
                    )}
                  </article>
                ))}
              </div>
            </section>

            <section className="practice-footer-grid">
              <div className="card">
                <p className="eyebrow">复习闭环</p>
                <h2>{data.overview.active_wrong}道错题仍需掌握</h2>
                <p>错题会记录原因和复习日期，连续答对三次后才转为已掌握。</p>
                <Link to="/review">进入错题本 →</Link>
              </div>
              <div className="card">
                <p className="eyebrow">诊断依据</p>
                <h2>{data.overview.attempt_count ? `已积累${data.overview.attempt_count}次作答` : "先建立你的答题样本"}</h2>
                <p>学习报告按科目、章节和错因解释薄弱点，不用大图表制造虚假精确。</p>
                <Link to="/report">查看诊断建议 →</Link>
              </div>
            </section>
          </>
        )}
      </main>
    </AppShell>
  );
}
