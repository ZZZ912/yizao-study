# 一造学伴中保真原型说明

## 定位

本目录用于界面方向审核，不是生产业务页面。原型验证信息架构、任务优先级、响应式布局和独立视觉语言；所有题目、进度、正确率和时间均为原创示意数据。

原型未复制 233 网校、环球网校或粉笔的页面、配色、图标、插图和文案。设计采用“工程蓝图 + 纸面批注”的一造学伴自有方向：纸白底色、蓝图蓝主动作、铜色提醒、克制的数据展示。

## 截图清单

### 手机端（390×844）

| 页面 | 截图 | 审核重点 |
| --- | --- | --- |
| 首页 | [mobile-home.png](screenshots/mobile-home.png) | 首屏是否只有一个优先任务 |
| 科目章节 | [mobile-chapters.png](screenshots/mobile-chapters.png) | 科目/版本、题量/已做/错题是否清晰 |
| 课程学习 | [mobile-course.png](screenshots/mobile-course.png) | 有序内容块是否适合连续阅读 |
| 刷题 | [mobile-practice.png](screenshots/mobile-practice.png) | 是否一题一屏、主动作明确 |
| 答题解析 | [mobile-analysis.png](screenshots/mobile-analysis.png) | 错因诊断是否先于大量解析 |
| 今日复习 | [mobile-review.png](screenshots/mobile-review.png) | 是否支持主动回忆而非直接看答案 |
| 错题本 | [mobile-wrongbook.png](screenshots/mobile-wrongbook.png) | 是否按价值推荐而非堆题 |
| 学习报告 | [mobile-report.png](screenshots/mobile-report.png) | 是否先建议后数据 |

### 电脑端（1440×1024）

| 页面 | 截图 | 审核重点 |
| --- | --- | --- |
| 首页 | [desktop-home.png](screenshots/desktop-home.png) | 更多信息是否仍围绕今日任务 |
| 课程学习 | [desktop-course.png](screenshots/desktop-course.png) | 目录、正文、笔记三栏是否平衡 |
| 刷题 | [desktop-practice.png](screenshots/desktop-practice.png) | 题卡、题目、草稿是否互不抢焦点 |
| 学习报告 | [desktop-report.png](screenshots/desktop-report.png) | 建议与证据是否比图表更突出 |

## 查看方式

直接用浏览器打开 `prototype.html` 并传入 `screen` 参数，例如：

```text
prototype.html?screen=mobile-home
prototype.html?screen=desktop-report
```

可用值：

```text
mobile-home
mobile-chapters
mobile-course
mobile-practice
mobile-analysis
mobile-review
mobile-wrongbook
mobile-report
desktop-home
desktop-course
desktop-practice
desktop-report
```

## 设计说明

- 手机首页最多出现一个主任务和两个次任务，底部导航严格保留五项。
- 手机课程、刷题、解析以单任务沉浸为主，目录和高级设置后续使用抽屉。
- 电脑端不是手机页面等比放大；通过侧栏和辅助栏支持长时间学习、草稿与复盘。
- 课程原型展示 `key_point`、`markdown`、`formula`、`warning` 和 `inline_quiz` 的统一内容块语言，其余块类型沿用同一体系扩展。
- 报告使用“发现—证据—动作”结构，不用大型雷达图或数据墙占据首页。
- 原型暂不包含真实图标、插图、品牌摄影、题库内容或完整交互动效。

## 审核后再做

界面方向确认前，不将这些原型批量实现为 React 业务页面。确认后建议先实现一个纵向切片：手机首页 → 课程内容块 → 即时练习 → 解析与错因，再验证闭环后扩展其他页面。
