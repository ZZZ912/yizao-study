import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { getLearningReport } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

export function LearningReportPage() {
  const report = useQuery({ queryKey: ["learning-report"], queryFn: getLearningReport });
  const data = report.data;
  const maxActivity = Math.max(1, ...(data?.activity.map((day) => day.answered + day.completed_lessons * 2) || [1]));

  return (
    <AppShell>
      <main className="dashboard-shell report-shell">
        <PageHeader eyebrow="基于真实学习记录" title="学习报告" actions={<Link className="button" to="/practice/session?mode=daily&target=20">继续练习</Link>} />
        <p className="page-intro">报告只依据你已经完成的课程和作答，不用全国平均值或虚构排名制造焦虑。</p>
        {report.isPending && <div className="card">正在生成学习报告…</div>}
        {report.isError && <div className="card error-state">报告暂时无法生成，请稍后重试。</div>}
        {data && (
          <>
            <section className="report-scoreboard">
              <div className="report-scoreboard__lead"><span>当前正确率</span><strong>{data.overview.accuracy}%</strong><small>{data.overview.correct_count}/{data.overview.attempt_count}次作答正确</small></div>
              <div><span>已做题目</span><strong>{data.overview.attempted_questions}</strong><small>共{data.overview.question_count}道已复核题</small></div>
              <div><span>完成课程</span><strong>{data.overview.completed_sections}</strong><small>共{data.overview.section_count}节</small></div>
              <div><span>未掌握错题</span><strong>{data.overview.active_wrong}</strong><small>{data.overview.due_reviews}道今日到期</small></div>
              <div><span>累计练习</span><strong>{data.overview.study_minutes}</strong><small>分钟有效作答时间</small></div>
            </section>

            <div className="report-main-grid">
              <section className="report-panel subject-diagnosis">
                <div className="section-heading"><div><p className="eyebrow">四科进度</p><h2>科目掌握情况</h2></div><span>学习与做题分开统计</span></div>
                <div className="diagnosis-table">
                  <div className="diagnosis-table__head"><span>科目</span><span>课程</span><span>已做/题量</span><span>正确率</span><span>错题</span></div>
                  {data.subjects.map((subject) => (
                    <div className="diagnosis-table__row" key={subject.code}>
                      <strong>{subject.title}</strong>
                      <span>{subject.completed_sections}/{subject.section_count}节</span>
                      <span>{subject.attempted_questions}/{subject.question_count}</span>
                      <span>{subject.attempt_count ? `${subject.accuracy}%` : "待练习"}</span>
                      <span>{subject.wrong_count}</span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="report-panel activity-panel">
                <div className="section-heading"><div><p className="eyebrow">最近14天</p><h2>学习活跃度</h2></div></div>
                <div className="activity-chart" aria-label="最近14天学习量">
                  {data.activity.map((day) => {
                    const value = day.answered + day.completed_lessons * 2;
                    return <div key={day.date} title={`${day.date}：${day.answered}题，${day.completed_lessons}节`}><span style={{ height: `${Math.max(4, value / maxActivity * 100)}%` }} /><small>{day.date.slice(5).replace("-", "/")}</small></div>;
                  })}
                </div>
              </section>

              <section className="report-panel weak-panel">
                <div className="section-heading"><div><p className="eyebrow">优先补强</p><h2>薄弱章节</h2></div></div>
                {data.weak_sections.length > 0 ? (
                  <div className="weak-list">{data.weak_sections.map((section, index) => (
                    <article key={section.section_id}>
                      <span>{index + 1}</span><div><small>{section.subject}</small><h3>{section.section}</h3><p>{section.attempt_count}次作答 · 错{section.wrong_count}次 · 正确率{section.accuracy}%</p></div>
                      <Link to={`/practice/session?section=${section.section_id}`}>针对练习</Link>
                    </article>
                  ))}</div>
                ) : <p className="empty-copy">完成一组题后，这里会按错误次数列出真正需要补强的章节。</p>}
              </section>

              <section className="report-panel reason-panel">
                <div className="section-heading"><div><p className="eyebrow">错误归因</p><h2>错因分布</h2></div></div>
                {data.wrong_reasons.length > 0 ? (
                  <div className="reason-list">{data.wrong_reasons.map((reason) => (
                    <div key={reason.code}><span>{reason.label}</span><div><i style={{ width: `${reason.count / Math.max(...data.wrong_reasons.map((item) => item.count)) * 100}%` }} /></div><strong>{reason.count}</strong></div>
                  ))}</div>
                ) : <p className="empty-copy">答错后选择“概念不清、选项混淆、计算失误、审题失误或记忆不牢”，报告才会给出针对建议。</p>}
              </section>
            </div>

            <section className="study-advice">
              <p className="eyebrow">下一步建议</p>
              <h2>{data.overview.attempt_count < 20 ? "先完成一组20题，建立第一份诊断样本" : data.overview.due_reviews ? `先清空${data.overview.due_reviews}道到期错题，再学新内容` : data.weak_sections[0] ? `优先补强：${data.weak_sections[0].section}` : "保持每天一节课、20道题和到期复习"}</h2>
              <div>
                <Link className="button" to={data.overview.due_reviews ? "/practice/session?mode=review" : "/practice/session?mode=daily&target=20"}>执行建议</Link>
                <Link className="button button--secondary" to="/practice/records">查看作答明细</Link>
              </div>
            </section>
          </>
        )}
      </main>
    </AppShell>
  );
}
