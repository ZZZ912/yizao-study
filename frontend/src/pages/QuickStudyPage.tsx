import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";

import { ContentBlock, getQuickCard } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { PageHeader } from "../components/layout/PageHeader";

const blockLabels: Record<string, string> = {
  key_point: "必背结论",
  formula: "公式",
  warning: "易错提示",
  comparison: "对比辨析",
  mnemonic: "记忆口诀",
  summary: "一分钟回顾",
};

function CardBlock({ block }: { block: ContentBlock }) {
  return (
    <section className={`learning-block learning-block--${block.type}`}>
      <span>{blockLabels[block.type] || "重点"}</span>
      <p>{block.content}</p>
    </section>
  );
}

export function QuickStudyPage() {
  const [offset, setOffset] = useState(0);
  const card = useQuery({
    queryKey: ["quick-card", offset],
    queryFn: () => getQuickCard(offset),
    placeholderData: (previous) => previous,
  });

  return (
    <AppShell>
      <main className="dashboard-shell quick-study-shell">
        <Link className="back-link" to="/">← 返回今日计划</Link>
        <PageHeader eyebrow="每天5分钟" title="碎片记忆卡" />
        {card.isPending && <div className="card">正在抽取今天的记忆卡…</div>}
        {card.isError && <div className="card error-state">记忆卡读取失败，请稍后重试。</div>}
        {card.data && (
          <article className="quick-card">
            <header>
              <div>
                <p className="eyebrow">{card.data.subject.title} · 第{card.data.chapter.number}章</p>
                <h2>{card.data.title}</h2>
                <p>{card.data.summary}</p>
              </div>
              <span>{card.data.position}/{card.data.total}</span>
            </header>
            <div className="quick-card__content">
              {card.data.content_blocks.map((block, index) => (
                <CardBlock block={block} key={`${card.data?.id}-${index}`} />
              ))}
            </div>
            <footer>
              <button className="button button--ghost" disabled={offset === 0} onClick={() => setOffset((value) => Math.max(0, value - 1))}>上一张</button>
              <Link className="button button--secondary" to={`/study/section/${card.data.section.id}`}>学习完整小节</Link>
              <button className="button" onClick={() => setOffset((value) => value + 1)}>记住了，下一张</button>
            </footer>
          </article>
        )}
      </main>
    </AppShell>
  );
}
