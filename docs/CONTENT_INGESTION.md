# 内容导入流程

本流程用于在本地校验、导入和人工复核结构化题目。它不复制来源文件，也不负责发布内容。商业资料只能在仓库外或 Git 忽略目录中处理。

## 输入与命令

输入文件使用 UTF-8 JSONL，每行一条题目记录，并符合 `content/schemas/question.schema.json`。默认报告写入被忽略的 `import-reports/private/`。

```bash
cd backend
python manage.py validate_content ../private-data/incoming/batch/questions.jsonl
python manage.py import_content ../private-data/incoming/batch/questions.jsonl --dry-run
python manage.py import_content ../private-data/incoming/batch/questions.jsonl --commit
python manage.py import_content ../private-data/incoming/batch/questions.jsonl --commit --batch-id <uuid>
```

`import_content` 不带参数时也等同于 dry-run。只有显式提供 `--commit` 才会写数据库；`--batch-id` 只能与 `--commit` 一起使用，并且不能重复使用已有批次 ID。

## 校验和导入语义

- Schema 校验后继续执行选项标签唯一、答案存在于选项、来源文件名不含路径等语义校验。
- 错误包含准确的 JSONL 行号。校验报告只包含计数、外部 ID、警告和错误元数据，不包含题干或选项正文。
- dry-run 对合法记录生成计划；即使同一文件含错误记录，也绝不写数据库，并明确说明正式提交将拒绝整个批次。
- commit 在写入前要求全批合法，并使用数据库事务；失败不会留下半条题目或半个批次。
- `external_id` 是幂等键。相同校验和记为 `skipped`；相同 ID 但内容变化会新增 `QuestionVersion`，不会覆盖历史版本。
- 已发布版本禁止原地修改。后续导入的新版本保持待审核，也不会替换当前已发布版本。
- 商业、第三方或 `public_repo_allowed=false` 的内容始终强制为 `pending_review`，无论输入声称何种审核状态。
- 导入保留 `source_answer`、`canonical_answer` 和 `presented_option_order`。程序不会修正来源答案。

## 重复检测

重复检测是保守提示，不做自动删除或合并：

- 题干和选项规范化前完全一致的 `exact_hash`；
- 去空白、标点等差异后的 `normalized_hash`；
- 有界题干相似度候选；
- 相同 `external_id` 的内容冲突；
- 相同题干的答案冲突；
- 相同题干但选项顺序不同。

候选组进入报告和 `warnings`，由管理员人工判断。

## 第一批本地验证基线

2026-08-03 对仓库外的 `yizao_extraction_batch_01` 只运行了 validate 和 dry-run：总计 1024 条，合法 1023 条，带警告 24 条，错误 1 条；单选 729 条、多选 294 条；章节数量依次为 167、214、150、218、224、50；重复候选 12 组，答案冲突 4 组。错误定位到 JSONL 第 492 行的空选项文本。

这些数字只用于验证导入能力。未执行 `--commit`，实际题目、原始文本和私有报告均未进入 Git。
