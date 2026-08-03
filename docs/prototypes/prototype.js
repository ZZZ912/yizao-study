const params = new URLSearchParams(window.location.search);
const screen = params.get("screen") || "mobile-home";

const navItems = ["首页", "学习", "刷题", "复习", "我的"];

function mobileNav(active) {
  return `<nav class="mobile-nav">${navItems
    .map((item) => `<div class="nav-item ${item === active ? "active" : ""}">${item}</div>`)
    .join("")}</nav>`;
}

function mobileHeader(context = "2026 一级造价工程师") {
  return `<header class="mobile-header">
    <div class="inline"><div class="brand-mini">YZ</div><div class="header-title">一造学伴<br><span class="header-context">${context}</span></div></div>
    <div class="avatar">林</div>
  </header>`;
}

function innerHeader(title, subtitle) {
  return `<div class="screen-heading"><button class="back" aria-label="返回">‹</button><div><div class="eyebrow">${subtitle}</div><h2>${title}</h2></div></div>`;
}

function mobileShell(content, active, immersive = false) {
  return `<main class="mobile-frame"><div class="mobile-content ${immersive ? "immersive" : ""}">${content}</div>${
    immersive ? "" : mobileNav(active)
  }</main>`;
}

function desktopNav(active) {
  return `<aside class="desktop-sidebar">
    <div class="desktop-brand"><div class="brand-mark">YZ</div><div><strong>一造学伴</strong><span>理解 · 练习 · 复习</span></div></div>
    <nav class="side-nav">${navItems.map((item) => `<div class="side-item ${item === active ? "active" : ""}">${item}</div>`).join("")}</nav>
    <div class="side-context"><small>当前目标</small><strong>2026 一级造价工程师<br>建设工程计价</strong><div class="prototype-note" style="margin-top:10px;color:#8fa0b7">原型示意数据</div></div>
  </aside>`;
}

function desktopShell(content, active, context = "建设工程计价 · 2026 教材") {
  return `<main class="desktop-frame">${desktopNav(active)}<section class="desktop-main">
    <header class="desktop-topbar"><div class="context">${context}</div><div class="inline" style="gap:14px"><span class="prototype-note">距离计划测试 24 天</span><div class="avatar">林</div></div></header>
    ${content}
  </section></main>`;
}

const screens = {
  "mobile-home": () =>
    mobileShell(`${mobileHeader()}
      <div class="eyebrow">8 月 3 日 · 今日计划</div>
      <h1>今天，先把计价依据理顺</h1>
      <p class="subtle">系统依据上次课程位置和两次同类失分，为你安排了一个主任务。</p>
      <section class="task-card">
        <div class="task-label">今日优先 · 约 18 分钟</div>
        <h2>继续：工程量清单计价的基本过程</h2>
        <p>从“综合单价的组成”继续，完成讲解后有 3 道即时练习。</p>
        <div class="progress"><span style="width:42%"></span></div>
        <div class="row-between"><span class="subtle">本节 42%</span><button class="btn">继续学习</button></div>
      </section>
      <div class="grid-2" style="margin-top:12px">
        <section class="mini-task"><span class="status copper">今日到期</span><div><div class="count">8</div><strong>张记忆卡</strong></div><span class="link-text">开始复习 →</span></section>
        <section class="mini-task"><span class="status">建议练习</span><div><div class="count" style="color:var(--blue)">6</div><strong>道计价依据题</strong></div><span class="link-text">课后再做 →</span></section>
      </div>
      <div class="section-title row-between"><h2>今天完成即可</h2><span class="prototype-note">原型示意数据</span></div>
      <div class="card"><div class="row-between"><div><strong>预计 32 分钟</strong><div class="subtle">课程 18 分 · 复习 8 分 · 练习 6 分</div></div><div class="ring" style="--value:25%" data-label="1/4"></div></div></div>`, "首页"),

  "mobile-chapters": () =>
    mobileShell(`${mobileHeader("学习目录")}${innerHeader("科目章节", "学习")}
      <div class="stack">
        <div class="selector row-between"><div><span class="subtle">当前科目</span><br><strong>建设工程计价</strong></div><span class="link-text">切换⌄</span></div>
        <div class="selector row-between"><div><span class="subtle">内容版本</span><br><strong>2026 教材 · 第 1 版</strong></div><span class="status">已同步</span></div>
      </div>
      <div class="section-title row-between"><h2>7 个章节</h2><span class="prototype-note">题量为示意</span></div>
      <section class="chapter-group">
        <div class="chapter-row"><div><div class="chapter-title">第一章 建设工程造价构成</div><div class="metric-line"><span>86 题</span><span>已做 62</span><span class="wrong">错题 7</span></div></div><div class="ring" style="--value:72%" data-label="72%"></div></div>
        <div class="chapter-row current"><div><div class="chapter-title">第二章 建设工程计价原理</div><div class="metric-line"><span>112 题</span><span>已做 28</span><span class="wrong">错题 9</span></div><span class="status copper" style="margin-top:7px">继续学习：第 3 节</span></div><div class="ring" style="--value:34%" data-label="34%"></div></div>
        <div class="chapter-row"><div><div class="chapter-title">第三章 项目决策和设计阶段计价</div><div class="metric-line"><span>94 题</span><span>已做 0</span><span>错题 0</span></div></div><span class="status">未开始</span></div>
        <div class="chapter-row"><div><div class="chapter-title">第四章 发承包阶段合同价款约定</div><div class="metric-line"><span>128 题</span><span>已做 0</span><span>错题 0</span></div></div><span class="status">未开始</span></div>
        <div class="chapter-row"><div><div class="chapter-title">第五章 施工阶段合同价款调整</div><div class="metric-line"><span>146 题</span><span>已做 0</span><span>错题 0</span></div></div><span class="status">未开始</span></div>
      </section>`, "学习"),

  "mobile-course": () =>
    mobileShell(`${innerHeader("工程量清单计价的基本过程", "第二章 · 第 3 节")}
      <div class="row-between" style="margin-bottom:10px"><span class="subtle">本节 3 / 7</span><span class="link-text">目录</span></div>
      <div class="progress" style="margin-bottom:18px"><span style="width:42%"></span></div>
      <div class="stack">
        <section class="content-block key"><div class="block-label">必背结论</div><h3>先确定计价依据，再进入单价分析</h3><p style="margin-bottom:0">遇到价格调整问题时，先识别合同约定和适用规则，不能直接从计算结果倒推。</p></section>
        <section class="content-block"><div class="block-label">正文讲解</div><p>计价过程可以拆成“范围确认、依据识别、数量核对、单价形成、费用汇总”五个动作。每一步都应保留可复核的来源。</p><p style="margin-bottom:0">本节先聚焦依据识别，后续例题再处理数量与单价。</p></section>
        <section class="content-block formula"><div class="block-label">公式</div><div class="formula-text">综合单价 = 人工费 + 材料费 + 机具费 + 管理费 + 利润</div><div class="subtle">示意公式仅用于原型排版，不作为学习材料。</div></section>
        <section class="content-block warning"><div class="block-label">易错提示</div><strong>不要把规费和税金直接计入示意综合单价。</strong></section>
        <section class="content-block"><div class="block-label">课中练习 · 1 题</div><h3>开始计算前，第一步应核对什么？</h3><button class="btn secondary full" style="margin-top:8px">展开练习</button></section>
      </div>
      <div style="height:70px"></div>
      <div class="sticky-action"><button class="btn full">继续：典型例题</button></div>`, "学习", true),

  "mobile-practice": () =>
    mobileShell(`${innerHeader("章节巩固", "建设工程计价")}
      <div class="row-between" style="margin-bottom:14px"><span class="status">第 3 / 10 题</span><span class="subtle">已自动保存</span></div>
      <section class="question-card">
        <div class="question-meta"><span>单选题 · 原创示意</span><span>建议 75 秒</span></div>
        <div class="question-title">在本节示例项目中，准备进行综合单价分析时，第一步最适合核对哪项信息？</div>
        <div class="options">
          <div class="option"><span class="keycap">A</span><span>最终汇总后的税额</span></div>
          <div class="option selected"><span class="keycap">B</span><span>合同约定与适用计价依据</span></div>
          <div class="option"><span class="keycap">C</span><span>其他学习者的平均答案</span></div>
          <div class="option"><span class="keycap">D</span><span>尚未核对的结果数值</span></div>
        </div>
      </section>
      <div class="row-between" style="margin-top:14px"><button class="btn secondary">收藏 / 笔记</button><span class="prototype-note">普通练习弱化计时</span></div>
      <div class="sticky-action"><button class="btn full">提交答案</button></div>`, "刷题", true),

  "mobile-analysis": () =>
    mobileShell(`${innerHeader("答题解析", "第 3 / 10 题")}
      <div class="stack large">
        <div class="answer-result"><div class="row-between"><div><strong>这题答错了</strong><div class="subtle">你的答案 A · 正确答案 B</div></div><span class="status copper">待巩固</span></div></div>
        <section class="card"><h3>先确认错因</h3><p class="subtle">这会影响后续推荐，你可以修改系统建议。</p><div class="reason-list"><span class="reason-chip active">建议 · 审题偏差</span><span class="reason-chip">概念不清</span><span class="reason-chip">公式记错</span><span class="reason-chip">猜测作答</span></div></section>
        <section class="content-block key"><div class="block-label">关键解析</div><h3>顺序是“先依据，后计算”</h3><p style="margin-bottom:0">题目问的是开始分析的第一步。税额和最终数值都属于后续结果，不能作为起点。</p></section>
        <section class="card"><div class="row-between"><h3>参考步骤</h3><span class="link-text">收起</span></div><ol class="step-list"><li>识别题目要求的是流程起点，而不是计算结果。</li><li>核对合同约定与适用规则，确定计价边界。</li><li>再核对数量并进行单价分析。</li></ol></section>
        <div class="grid-2"><button class="btn secondary">回看知识点</button><button class="btn">下一题</button></div>
      </div>`, "刷题", true),

  "mobile-review": () =>
    mobileShell(`${mobileHeader("今日复习")}
      <div class="review-progress"><div class="eyebrow">今日到期</div><h1>8 张卡片</h1><div class="subtle">第 3 张 · 预计还需 6 分钟</div></div>
      <section class="review-card">
        <div><span class="status">工程计价 · 核心概念</span><div class="review-prompt">综合单价分析前，为什么必须先确认计价依据？</div></div>
        <div><div class="subtle" style="margin-bottom:12px">先在心里作答，再查看答案。</div><button class="btn full">显示答案</button></div>
      </section>
      <div class="section-title row-between"><h2>显示答案后评价</h2><span class="prototype-note">示意状态</span></div>
      <div class="review-actions"><button>没想起<small>稍后</small></button><button>有点难<small>明天</small></button><button>正常<small>4 天</small></button><button>很熟<small>9 天</small></button></div>`, "复习"),

  "mobile-wrongbook": () =>
    mobileShell(`${mobileHeader("复习")}${innerHeader("错题本", "个人学习资产")}
      <div class="reason-list" style="margin-bottom:16px"><span class="chip active">最值得重练</span><span class="chip">最近错题</span><span class="chip">筛选⌄</span></div>
      <section class="wrong-card recommended"><div class="row-between"><span class="status copper">优先处理</span><span class="subtle">9 题</span></div><h2 style="margin-top:12px">计价依据与费用边界</h2><p>最近 7 天重复出现 3 次，主要错因为审题偏差与概念混淆。</p><div class="row-between"><span class="subtle">建议：先复习 1 个知识点</span><button class="btn">开始重练</button></div></section>
      <div class="section-title row-between"><h2>其他分组</h2><span class="prototype-note">示意数据</span></div>
      <div class="stack">
        <section class="wrong-card"><div class="row-between"><div><h3>工程造价构成</h3><span class="subtle">6 题 · 2 题已验证</span></div><span class="status">待复习</span></div></section>
        <section class="wrong-card"><div class="row-between"><div><h3>合同价款调整</h3><span class="subtle">4 题 · 最近错误 2 天前</span></div><span class="status">学习中</span></div></section>
        <section class="wrong-card"><div class="row-between"><div><h3>案例步骤缺失</h3><span class="subtle">3 个小问 · 后续阶段开放</span></div><span class="status">预留</span></div></section>
      </div>`, "复习"),

  "mobile-report": () =>
    mobileShell(`${mobileHeader("我的")}${innerHeader("学习报告", "8 月 27 日—8 月 2 日")}
      <section class="insight"><span class="status">本周主建议</span><div class="recommendation">先巩固“计价依据”，再进入下一章</div><div class="evidence">证据 1：相关练习 18 题，正确率 61%，低于当前章节其他知识点。</div><div class="evidence">证据 2：4 道错题中有 3 道标记为审题偏差。</div><button class="btn full" style="margin-top:14px">开始 12 分钟巩固</button></section>
      <div class="section-title row-between"><h2>章节证据</h2><span class="link-text">查看详情</span></div>
      <section class="card stack">
        <div class="bar-row"><span>造价构成</span><div class="bar"><span style="width:78%"></span></div><strong>78%</strong></div>
        <div class="bar-row"><span>计价原理</span><div class="bar low"><span style="width:61%"></span></div><strong>61%</strong></div>
        <div class="bar-row"><span>合同价款</span><div class="bar"><span style="width:72%"></span></div><strong>72%</strong></div>
      </section>
      <div class="section-title row-between"><h2>更多数据</h2><span class="link-text">展开⌄</span></div>
      <div class="card"><div class="row-between"><span>学习时长、错因分布、练习记录</span><span class="subtle">默认收起</span></div></div>`, "我的"),

  "desktop-home": () =>
    desktopShell(`<div class="desktop-page">
      <div class="row-between"><div><div class="eyebrow">8 月 3 日 · 今日计划</div><h1>早上好，今天先完成一个关键任务</h1><p class="subtle">系统已根据课程进度、到期复习和近期错因调整顺序。</p></div><span class="prototype-note">全部数据仅作原型示意</span></div>
      <div class="desktop-grid-home"><div class="stack large">
        <section class="task-card desktop-task"><div class="task-label">今日优先 · 约 18 分钟</div><h2>继续：工程量清单计价的基本过程</h2><p>从“综合单价的组成”继续。完成讲解和 3 道即时练习后，再安排错题巩固。</p><div class="progress" style="max-width:520px"><span style="width:42%"></span></div><div class="row-between" style="max-width:520px"><span class="subtle">本节 42%</span><button class="btn">继续学习</button></div></section>
        <div class="grid-2"><section class="desktop-card"><div class="row-between"><div><span class="status copper">今日到期</span><h2 style="margin-top:14px">8 张记忆卡</h2><p class="subtle">预计 8 分钟，包含 3 张易错公式卡。</p></div><button class="btn secondary">开始复习</button></div></section><section class="desktop-card"><div class="row-between"><div><span class="status">课后建议</span><h2 style="margin-top:14px">6 道针对练习</h2><p class="subtle">依据本周的审题偏差自动缩小范围。</p></div><button class="btn secondary">查看范围</button></div></section></div>
      </div><aside class="stack large"><section class="desktop-card"><h2>本周节奏</h2><div class="heat-row">${[1,2,2,3,1,0,0].map((v) => `<span class="heat-cell ${v ? `l${v}` : ""}"></span>`).join("")}</div><div class="row-between" style="margin-top:12px"><span class="subtle">已学习 4 天</span><span class="link-text">调整计划</span></div></section><section class="desktop-card"><h2>当前阶段</h2><p><strong>基础理解 · 第 2 周</strong></p><div class="progress"><span style="width:36%"></span></div><div class="desktop-stats"><div class="stat"><strong>6.4h</strong><span>本周学习</span></div><div class="stat"><strong>72%</strong><span>练习稳定度</span></div><div class="stat"><strong>18</strong><span>待复习</span></div></div></section><section class="desktop-card"><div class="row-between"><div><h3>上次停在</h3><span class="subtle">第二章 · 第 3 节 · 必背结论</span></div><span class="link-text">定位</span></div></section></aside></div>
    </div>`, "首页"),

  "desktop-course": () =>
    desktopShell(`<div class="desktop-page"><div class="row-between" style="margin-bottom:20px"><div><div class="eyebrow">第二章 · 第 3 节</div><h1>工程量清单计价的基本过程</h1></div><div class="inline" style="gap:10px"><button class="btn secondary">标记重点</button><button class="btn">继续下一块</button></div></div>
      <div class="desktop-grid-course"><aside class="desktop-card"><h3>本节目录</h3><div class="outline-list"><div class="outline-item">01 章节导学</div><div class="outline-item">02 计价范围</div><div class="outline-item active">03 计价依据</div><div class="outline-item">04 综合单价组成</div><div class="outline-item">05 典型例题</div><div class="outline-item">06 课中练习</div><div class="outline-item">07 章节小结</div></div><div class="progress" style="margin-top:18px"><span style="width:42%"></span></div><div class="subtle" style="margin-top:8px">本节进度 42%</div></aside>
      <article class="desktop-card desktop-reading stack large"><section><div class="block-label">正文讲解</div><h2>先确认依据，再进行可复核的单价分析</h2><p>计价过程可以拆成范围确认、依据识别、数量核对、单价形成和费用汇总五个动作。本节先聚焦依据识别，后续例题再处理数量与单价。</p><p>当题目给出多个价格、时间点或合同条款时，先判断哪一条规则决定计价边界。这样能够避免从最终数值反推适用依据。</p></section><section class="content-block key"><div class="block-label">必背结论</div><h3>流程题先找约束条件，计算题先定口径。</h3><p style="margin-bottom:0">“先依据、后计算”是本节用于检查答题顺序的核心动作。</p></section><section class="content-block formula"><div class="block-label">公式 · 示意</div><div class="formula-text">综合单价 = 人工费 + 材料费 + 机具费 + 管理费 + 利润</div></section><section class="content-block warning"><div class="block-label">易错提示</div><strong>不要在尚未确定计价口径时直接代入数值。</strong></section></article>
      <aside class="stack"><section class="desktop-card"><h3>本节目标</h3><div class="stack"><div class="row-between"><span class="subtle">识别计价依据</span><span class="status jade">已理解</span></div><div class="row-between"><span class="subtle">说明基本顺序</span><span class="status copper">学习中</span></div><div class="row-between"><span class="subtle">完成即时练习</span><span class="status">未开始</span></div></div></section><section class="desktop-card"><div class="row-between"><h3>我的笔记</h3><span class="link-text">保存</span></div><div class="note-area">先看合同约定，再判断适用规则。这里需要和第一章的费用构成一起复习……</div><div class="subtle" style="margin-top:8px">已自动保存</div></section><section class="desktop-card"><h3>关联复习</h3><p class="subtle">本块关联 2 张记忆卡、6 道练习题。</p><span class="link-text">完成课程后查看 →</span></section></aside></div>
    </div>`, "学习"),

  "desktop-practice": () =>
    desktopShell(`<div class="desktop-page"><div class="row-between" style="margin-bottom:20px"><div><div class="eyebrow">章节巩固 · 普通模式</div><h1>计价依据与费用边界</h1></div><div class="inline" style="gap:12px"><span class="status">已自动保存</span><button class="btn secondary">结束练习</button></div></div>
      <div class="desktop-grid-practice"><aside class="desktop-card"><div class="row-between"><h3>答题卡</h3><span class="subtle">3 / 10</span></div><div class="question-grid">${Array.from({length:10},(_,i)=>`<span class="question-number ${i<2?'done':i===2?'current':''}">${i+1}</span>`).join("")}</div><div style="margin-top:22px" class="stack"><div class="row-between"><span class="subtle">已答</span><strong>2</strong></div><div class="row-between"><span class="subtle">未答</span><strong>8</strong></div><div class="row-between"><span class="subtle">收藏</span><strong>0</strong></div></div><button class="btn secondary full" style="margin-top:18px">练习设置</button></aside>
      <section class="question-card" style="padding:28px"><div class="question-meta"><span>单选题 · 原创示意</span><span>第 3 题</span></div><div class="question-title" style="font-size:20px">在本节示例项目中，准备进行综合单价分析时，第一步最适合核对哪项信息？</div><div class="options"><div class="option"><span class="keycap">A</span><span>最终汇总后的税额</span></div><div class="option selected"><span class="keycap">B</span><span>合同约定与适用计价依据</span></div><div class="option"><span class="keycap">C</span><span>其他学习者的平均答案</span></div><div class="option"><span class="keycap">D</span><span>尚未核对的结果数值</span></div></div><div class="answer-actions row-between" style="margin-top:24px"><div class="inline" style="gap:10px"><button class="btn secondary">收藏</button><button class="btn secondary">写笔记</button></div><button class="btn" style="min-width:140px">提交答案</button></div></section>
      <aside class="stack"><section class="desktop-card"><h3>草稿区</h3><div class="note-area" style="min-height:180px">在这里记录计算过程。普通练习不会强制计时，离开时自动保存。</div></section><section class="desktop-card"><h3>本组范围</h3><div class="stack"><div><span class="subtle">知识点</span><br><strong>计价依据、综合单价</strong></div><div><span class="subtle">推荐原因</span><br><strong>近期两次审题偏差</strong></div></div></section><section class="desktop-card"><h3>键盘操作</h3><p class="subtle" style="margin-bottom:0">A–D 选择 · Enter 提交 · N 下一题</p></section></aside></div>
    </div>`, "刷题"),

  "desktop-report": () =>
    desktopShell(`<div class="desktop-page"><div class="row-between"><div><div class="eyebrow">8 月 27 日—8 月 2 日</div><h1>学习报告</h1><p class="subtle">先看下一步，再按需展开数据证据。</p></div><div class="inline" style="gap:10px"><button class="btn secondary">切换周期</button><button class="btn secondary">导出摘要</button></div></div>
      <div class="desktop-grid-report"><div class="stack large"><section class="insight"><span class="status">本周主建议</span><div class="recommendation">先巩固“计价依据”，再进入下一章</div><div class="grid-2"><div class="evidence">练习证据：相关 18 题正确率 61%，低于本章其他知识点。</div><div class="evidence">错因证据：4 道错题中 3 道标记为审题偏差。</div></div><div class="row-between" style="margin-top:16px"><span class="subtle">预计 12 分钟 · 1 个知识点 + 6 道题</span><button class="btn">开始巩固</button></div></section>
      <section class="desktop-card"><div class="row-between"><h2>章节证据</h2><span class="prototype-note">示意数据，不作为真实评估</span></div><table class="report-table"><thead><tr><th>章节</th><th>学习状态</th><th>练习</th><th>主要错因</th><th>建议</th></tr></thead><tbody><tr><td>造价构成</td><td><span class="status jade">较稳定</span></td><td>78%</td><td>计算失误</td><td>按计划复习</td></tr><tr><td>计价原理</td><td><span class="status copper">待巩固</span></td><td>61%</td><td>审题偏差</td><td><span class="link-text">立即巩固</span></td></tr><tr><td>合同价款</td><td><span class="status">学习中</span></td><td>72%</td><td>步骤缺失</td><td>完成当前课程</td></tr></tbody></table></section></div>
      <aside class="stack large"><section class="desktop-card"><h2>本周概览</h2><div class="desktop-stats"><div class="stat"><strong>6.4h</strong><span>学习时长</span></div><div class="stat"><strong>86</strong><span>练习题</span></div><div class="stat"><strong>4</strong><span>学习天</span></div></div></section><section class="desktop-card"><h2>学习节奏</h2><div class="heat-row">${[1,2,2,3,1,0,0].map((v)=>`<span class="heat-cell ${v?`l${v}`:''}"></span>`).join("")}</div><p class="subtle" style="margin:12px 0 0">周三任务较集中，下周将两组复习拆开。</p></section><section class="desktop-card"><div class="row-between"><h2>更多分析</h2><span class="link-text">展开⌄</span></div><div class="outline-list"><div class="outline-item">错因分布</div><div class="outline-item">正确率趋势</div><div class="outline-item">练习记录</div><div class="outline-item">复习记忆曲线</div></div></section></aside></div>
    </div>`, "我的")
};

const render = screens[screen] || screens["mobile-home"];
document.body.dataset.screen = screen;
document.getElementById("app").innerHTML = render();
