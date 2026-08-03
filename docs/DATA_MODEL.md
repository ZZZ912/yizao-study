# 数据模型设计

## 通用约定

- 业务主键使用 UUID，用户可见编号另设稳定代码字段。
- 所有核心模型包含 `created_at` 与 `updated_at`。
- 时间以 UTC 存储，展示时转换为 `Asia/Shanghai`。
- 发布内容不使用覆盖更新；历史学习记录始终引用具体版本。
- 状态、排序、外键完整性和唯一性尽可能由数据库约束保护。

## 第一阶段模型

### accounts.User

从项目第一次迁移开始启用的自定义用户模型，基于 `AbstractUser`：

- UUID 主键
- 唯一、规范化邮箱
- `display_name`
- `is_active`、`is_staff`、`date_joined`
- 用户名仅作为内部兼容字段，登录使用邮箱

第一阶段不提供注册模型或注册 API。管理员通过 Django Admin 或 `createsuperuser`/后续管理命令创建用户。

## 后续领域模型

### curriculum

- `Subject` → `Chapter` → `Section`：课程目录层级。
- `Course`：课程稳定身份。
- `CourseVersion`：课程名称、介绍、目标和发布状态。
- `Lesson`：课时稳定身份，关联课程和小节。
- `LessonVersion`：课时标题、预计时长、目标、重难点和发布状态。
- `LessonContentBlock`：有序、类型化课时内容块。
- `LearningObjective`：可复用的学习目标。

### knowledge

- `KnowledgePoint`：知识点稳定身份与目录归属。
- `KnowledgeVersion`：讲解、必背内容、易错点、口诀和适用考试版本。
- `KnowledgeTag`：标签。
- `KnowledgeRelation`：带类型和方向的前置、关联、易混关系；发布前检测前置关系环。
- `ExamEdition`：考试年份或大纲版本。

### questions

- `Question`：题目稳定身份、来源类型和当前发布版本。
- `QuestionVersion`：题干、题型、难度、解析、适用版本和状态。
- `QuestionOption`：选项、正确性、逐项解析与顺序。
- `QuestionKnowledge`：题目版本与知识点版本的主次关联。
- `QuestionGroup`、`CaseScenario`：案例背景容器。
- `QuestionPart`：案例小问及独立分值、题型和参考答案。
- `ScoringPoint`：小问评分点和分值。
- `ReferenceStep`：计算或论证参考步骤。

### practice

- `PracticeSession`：一次练习及其选题范围。
- `AnswerAttempt`：引用 `QuestionVersion`，保存结构化答案、正确性、耗时和错误原因。
- `QuestionPartAttempt`：案例小问答案、得分与评分明细。
- `FavoriteQuestion`：用户收藏，用户与题目唯一。
- `WrongQuestion`：首次/最近错误、错误次数、状态和掌握度。

### review

- `Flashcard`：背诵卡稳定身份。
- `FlashcardVersion`：正反面内容、关联知识点和发布状态。
- `ReviewSchedule`：间隔、难度因子、重复次数和下次复习时间。
- `ReviewLog`：一次复习评分和调度结果。
- `KnowledgeMastery`：用户对知识点的掌握度快照。

### exams、notes、content_updates

- `ExamPaper`、`PaperQuestion`、`ExamAttempt`、`ExamAnswer`、`ExamKnowledgeResult`。
- `Note`：只允许关联知识点或题目中的一种，并由检查约束保证。
- `ContentRelease`、`ContentChange`、`ContentReview`：发布批次、变更项和审核记录。

## 关键索引与约束

- 目录层级代码和排序唯一。
- 每个稳定实体的版本号唯一，且最多一个当前发布版本。
- `LessonContentBlock(lesson_version, position)` 唯一。
- `QuestionPart(question_group, position)` 唯一。
- `ScoringPoint(question_part, position)` 与 `ReferenceStep(question_part, position)` 唯一。
- 用户复习队列索引 `(user, next_review_at)`。
- 错题查询索引 `(user, status, last_wrong_at)`。
- 答题提交使用业务幂等键并按用户唯一。

