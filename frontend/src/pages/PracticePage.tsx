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

export function PracticePage() {
  const [search] = useSearchParams();
  const params = useMemo(() => ({
    subject: search.get("subject") || undefined,
    section: search.get("section") || undefined,
    mode: search.get("mode") || "practice",
  }), [search]);
  const queryClient = useQueryClient();
  const question = useQuery({ queryKey: ["next-question", params], queryFn: () => getNextQuestion(params) });
  const [selected, setSelected] = useState<string[]>([]);
  const [startedAt, setStartedAt] = useState(Date.now());
  const [result, setResult] = useState<Awaited<ReturnType<typeof submitAttempt>> | null>(null);
  const [reasonSaved, setReasonSaved] = useState(false);
  useEffect(() => { setSelected([]); setResult(null); setStartedAt(Date.now()); setReasonSaved(false); }, [question.data?.version_id]);
  const submit = useMutation({
    mutationFn: () => submitAttempt({
      question_version_id: question.data!.version_id,
      selected_answer: selected,
      elapsed_seconds: Math.round((Date.now() - startedAt) / 1000),
    }),
    onSuccess: (data) => {
      setResult(data);
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
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
        {question.isPending && <div className="page-state">正在选取精编题…</div>}
        {question.data === null && (
          <div className="empty-practice card">
            <h1>{params.mode === "review" ? "今天的到期错题已清空" : "当前范围暂无已复核题目"}</h1>
            <p>未审核或有争议的题不会进入练习。</p>
            <Link className="button" to="/">返回首页</Link>
          </div>
        )}
        {question.data && (
          <article className="question-card">
            <header className="question-meta">
              <Link to="/">退出</Link>
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
                <Button type="button" onClick={() => void nextQuestion()}>下一题</Button>
              </section>
            )}
          </article>
        )}
      </main>
    </AppShell>
  );
}
