# 模板字段映射

基于 `assets/template.docx` 分析（锚点填充模式）。

## 文档结构

- **标题**：`会议` + `记录`（模板固定，不修改）
- **表格**：1 张，9 行 × 2 列
  - 第 1 列：固定标签（不修改）
  - 第 2 列：待填充内容

## 字段表

| 字段 key | 模板标签（第 1 列） | 填充位置 | 说明 |
|----------|---------------------|----------|------|
| `project_name` | 项目名称 | 第 1 行第 2 列 | 客户/项目名称；用于输出文件名 `【XXXX】` |
| `interview_purpose` | 访谈目的 | 第 2 行第 2 列 | |
| `interview_time` | 访谈时间 | 第 3 行第 2 列 | 用于输出文件名日期部分 |
| `interview_location` | 访谈地点 | 第 4 行第 2 列 | |
| `participants` | 参加人员及其联系方式 | 第 5 行第 2 列 | 多人可换行 |
| `topics` | 访谈议题 | 第 6 行第 2 列 | |
| `interview_notes` | 访谈记录 | 第 7 行第 2 列 | 主体纪要，可多段 |
| `interview_results` | 访谈结果 | 第 8 行第 2 列 | |
| `interviewee_suggestions` | 被访问者的建议 | 第 9 行第 2 列 | |

## 填充规则

1. **只改第 2 列** `w:tc` 内的文本，不改第 1 列标签、不改 `w:tbl` / `w:tr` / `w:tcPr`。
2. **换行**：字段内容中的 `\n`（JSON 里写作 `\\n`）在 Word 中渲染为**独立段落**（多个 `w:p`），保留模板单元格的首段 `pPr` / `rPr` 样式。
3. 连续空行最多保留 1 个空段落，避免 Word 里出现大片空白。
4. 列表项（如 `1. 议题一`）按纯文本写入，每行一条，不依赖 Word 自动编号。
5. 素材无法可靠填写的字段：**先按 [`field-collection.md`](field-collection.md) 询问用户补全**，不要默认静默填 `[待补充]`。
6. 仅用户明确授权「先出草稿」时，方可用 `[待补充]` 占位生成。
7. 从素材提取 `project_name`、`interview_time` 时必须有依据；无依据则列入询问清单。

## 输出文件名

```
【{project_name}】客户访谈记录-{date}.docx
```

| 占位 | 来源 | 规则 |
|------|------|------|
| `{project_name}` | `project_name` 字段 | 去掉 `\ / : * ? " < > \|`；为空则用 `待补充` |
| `{date}` | `interview_time` 字段 | 解析为 `YYYY-MM-DD`；无法解析则用生成当天日期 |

示例：`【Acme科技】客户访谈记录-2026-05-29.docx`

## 快速填充（本仓库脚本）

```bash
python3 scripts/fill_interview_docx.py --fields-json scripts/example-fields.json --output-dir .
```

字段 JSON 键名与上表 `字段 key` 列一致。
