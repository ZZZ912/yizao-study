# 内容模型

## 有序课时内容块

`LessonContentBlock` 属于某个 `LessonVersion`，通过不可重复的 `position` 保持顺序。支持以下类型：

- `introduction`：章节导学
- `markdown`：正文讲解
- `key_point`：必背结论
- `formula`：公式
- `example`：典型例题
- `case`：工程案例
- `warning`：易错提示
- `comparison`：对比表
- `mnemonic`：记忆口诀
- `inline_quiz`：课中练习
- `summary`：章节小结

内容块使用类型化字段与受控 JSON 元数据，而不是把所有结构塞进一个无约束 JSON：

- Markdown 类块保存 Markdown 源文和清洗后的渲染结果。
- Formula 块保存 TeX 源、显示模式和无障碍说明。
- Comparison 块保存结构化表头与行数据。
- Inline quiz 关联一个已发布 `QuestionVersion`。
- Example 和 case 块可关联题目组，也可包含仅用于教学展示的受控正文。

`LessonVersion` 上对 `(lesson_version, position)` 设置唯一约束。发布前校验内容块序号连续、必需字段与类型匹配，并且所有引用内容均为可发布状态。

## Markdown 与公式安全

1. 后端保存原始 Markdown，禁止信任作者输入的 HTML。
2. 默认关闭 Markdown 原始 HTML；如未来需要少量 HTML，仅允许明确标签和属性白名单。
3. 链接协议只允许 `https`、`http` 和受控站内相对链接，禁止 `javascript:` 与内联事件。
4. 渲染产物再次经过服务端清洗；前端不直接使用未经清洗的 `dangerouslySetInnerHTML`。
5. TeX 源交给 KaTeX 严格模式渲染，不启用不受信任宏和 HTML 扩展。
6. 公式渲染失败时显示转义后的 TeX 源，不回退为原始 HTML。

## 版本与发布

以下内容采用不可变版本：

- `CourseVersion`
- `LessonVersion`
- `KnowledgeVersion`
- `QuestionVersion`
- `FlashcardVersion`

统一状态：`draft`、`in_review`、`published`、`disputed`、`superseded`、`retired`。

稳定实体记录 `current_published_version`。版本记录版本号、创建者、审核者、审核时间、发布时间、变更说明和内容校验摘要。数据库约束与服务层共同阻止修改已发布版本。

## 案例题

- `QuestionGroup`：一组共享背景材料的题目容器。
- `CaseScenario`：工程背景、已知条件、附件说明和版本信息。
- `QuestionPart`：独立小问、题型、顺序、分值与参考答案。
- `ScoringPoint`：某小问的得分点、分值、匹配规则和顺序。
- `ReferenceStep`：计算或论证步骤、公式、结果、单位与顺序。

用户作答按 `QuestionPart` 保存，不把整道案例题答案合并成一段文本。评分结果同时保存总分和逐评分点明细，便于复核与后续算法升级。

