import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { getNextQuestion, submitAttempt, updateWrongReason } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";

const wrongReasons = [
  ["concept", "概念不清"],
  ["confusion", "选项混淆"],
  ["calculation", "计算失误"],
  ["reading", "审题失误"],
  ["memory", "记忆不牢"],
] as const;

const modeLabels: Record<string, string> = {
  daily: "今日练习",
  practice: "顺序练习",
  random: "随机训练",
  wrong: "错题重做",
  review: "到期复习",
};

export function PracticePage() {
  const [search] = useSearchParams();
  const params = useMemo(() => ({
    subject: search.get("subject") || undefined,
    section: search.get("section") || undefined,
    mode: search.get("mode") || "practice",
  }), [search]);
  const target = Math.max(0, Math.min(Number(search.get("target") || 0) || 0, 100));
  const isTimed = search.get("timed") === "1";
  const queryClient = useQueryClient();
  const question = useQuery({ queryKey: ["next-question", params], queryFn: () => getNextQuestion(params) });
  const [selected, setSelected] = useState<string[]>([]);
  const [startedAt, setStartedAt] = useState(Date.now());
  const [result, setResult] = useState<Awaited<ReturnType<typeof submitAttempt>> | null>(null);
  const [reasonSaved, setReasonSaved] = useState(false);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [sessionStartedAt] = useState(Date.now());
  const [sessionSeconds, setSessionSeconds] = useState(0);
  useEffect(() => {
    if (!isTimed) return undefined;
    const timer = window.setInterval(() => setSessionSeconds(Math.round((Date.now() - sessionStartedAt) / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, [isTimed, sessionStartedAt]);
  useEffect(() => { setSelected([]); setResult(null); setStartedAt(Date.now()); setReasonSaved(false); }, [question.data?.version_id]);
  const submit = useMutation({
    mutationFn: () => submitAttempt({
      question_version_id: question.data!.version_id,
      selected_answer: selected,
      elapsed_seconds: Math.round((Date.now() - startedAt) / 1000),
    }),
    onSuccess: (data) => {
      setResult(data);
      setAnsweredCount((value) => value + 1);
      if (data.is_correct) setCorrectCount((value) => value + 1);
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["learning-report"] });
    },
  });
  const saveReason = useMutation({
    mutationFn: (reason: string) => updateWrongReason(result!.attempt_id, reason),
    onSuccess: () => setReasonSaved(true),
  });

  function toggle(label: string) {
    if (!question.data || result) return;
    if (question.data.question_type === "single_choice") setSelected([label]);
    else setSelected((current) => current.includes(label) ? current.filter((item) => item !== label) : [...current, label]);
  }

  async function nextQuestion() {
    setSelected([]); setResult(null); setReasonSaved(false); setStartedAt(Date.now());
    await question.refetch();
  }

  return (
    <AppShell>
      <main className="practice-shell">
        <section className="practice-session-bar" aria-label="本组练习进度">
          <div><Link to="/practice">← 退出本组</Link><strong>{modeLabels[params.mode] || "章节练习"}</strong></div>
          <dl>
            <div><dt>进度</dt><dd>{answeredCount}{target ? `/${target}` : "题"}</dd></div>
            <div><dt>答对</dt><dd>{correctCount}</dd></div>
            {isTimed && <div><dt>用时</dt><dd>{Math.floor(sessionSeconds / 60)}:{String(sessionSeconds % 60).padStart(2, "0")}</dd></div>}
          </dl>
          {target > 0 && <progress value={answeredCount} max={target} />}
        </section>
        {question.isPending && <div className="page-state">正在选取精编题…</div>}
        {question.data === null && (
          <div className="empty-practice card">
            <h1>{params.mode === "review" ? "今天的到期错题已清空" : "当前范围暂无已复核题目"}</h1>
            <p>未审核或有争议的题不会进入练习。</p>
            <Link className="button" to="/practice">返回刷题中心</Link>
          </div>
        )}
        {question.data && (
          <article className="question-card">
            <header className="question-meta">
              <span>第{answeredCount + (result ? 0 : 1)}题{target ? ` / 共${target}题` : ""}</span>
              <span>{question.data.subject.title} · {question.data.section.title}</span>
              <span>{question.data.question_type === "multiple_choice" ? "多选题" : "单选题"}</span>
            </header>
            <h1>{question.data.stem}</h1>
            <p className="selection-hint">{question.data.question_type === "multiple_choice" ? "请选择两个或以上答案" : "请选择一个答案"}</p>
            <div className="option-list">
              {question.data.options.map((option) => {
                const isSelected = selected.includes(option.label);
                const isCorrect = result?.correct_answer.includes(option.label);
                const isWrongSelected = result && isSelected && !isCorrect;
                return (
                  <button
                    className={`option-button${isSelected ? " is-selected" : ""}${isCorrect ? " is-correct" : ""}${isWrongSelected ? " is-wrong" : ""}`}
                    type="button"
                    key={option.label}
                    onClick={() => toggle(option.label)}
                    disabled={Boolean(result)}
                  >
                    <span>{option.label}</span><strong>{option.text}</strong>
                  </button>
                );
              })}
            </div>
            {!result && (
              <Button type="button" onClick={() => submit.mutate()} disabled={selected.length === 0 || submit.isPending}>
                提交答案
              </Button>
            )}
            {result && (
              <section className={`analysis-panel ${result.is_correct ? "is-correct" : "is-wrong"}`}>
                <p className="eyebrow">{result.is_correct ? "回答正确" : `正确答案 ${result.correct_answer.join("、")}`}</p>
                <h2>答案解析</h2>
                <p>{result.analysis || "本题解析正在补充，答案已通过结构校验。"}</p>
                {!result.is_correct && !reasonSaved && (
                  <div className="wrong-reason">
                    <strong>这次为什么错？</strong>
                    <div>{wrongReasons.map(([value, label]) => (
                      <button type="button" onClick={() => saveReason.mutate(value)} key={value}>{label}</button>
                    ))}</div>
                  </div>
                )}
                {reasonSaved && <p className="saved-note">已记录错因，将用于后续复习。</p>}
                {target > 0 && answeredCount >= target ? (
                  <div className="session-complete-actions">
                    <p>本组完成：答对{correctCount}/{answeredCount}题，正确率{Math.round(correctCount / Math.max(answeredCount, 1) * 100)}%。</p>
                    <Link className="button" to="/report">查看训练报告</Link>
                    <Link className="button button--secondary" to="/practice">返回刷题中心</Link>
                  </div>
                ) : <Button type="button" onClick={() => void nextQuestion()}>下一题</Button>}
              </section>
            )}
          </article>
        )}
      </main>
    </AppShell>
  );
}
