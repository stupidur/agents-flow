---
name: meeting-minutes
description: "从用户提供的文字、Word 或本地录音（Whisper）生成客户访谈记录 .docx，严格按 assets/template.docx 填充。仅处理用户本地素材，不查询飞书/妙记/VC。当用户需要客户访谈记录 Word、整理访谈文字或录音转访谈表时使用。"
metadata:
  requires:
    bins: ["whisper"]
    optional_bins: ["pandoc"]
---

# 客户访谈记录（meeting-minutes）

从多种素材生成**与模板版式一致**的客户访谈记录 Word 文档。

**CRITICAL**：填充前 Read [`references/template-fields.md`](references/template-fields.md)。**禁止** Markdown 转 Word、**禁止** docx-js 从零建文档；必须基于 `assets/template.docx` 只改表格第 2 列。

**禁止调用飞书相关 skill**（与本 skill 无关，不要混用）：

- 不调用 `lark-workflow-meeting-summary`、`lark-vc`、`lark-minutes`、`lark-calendar`
- 不使用 `lark-cli vc +search`、`+notes`、`minutes +search` 等拉取飞书会议/妙记
- 输入**仅来自**：用户粘贴文字、用户提供的 `.docx`、用户提供的本地音视频（Whisper 转写）

## 模板与输出

| 项 | 路径 / 规则 |
|----|-------------|
| 模板 | `assets/template.docx` |
| 字段映射 | [`references/template-fields.md`](references/template-fields.md) |
| 输出文件名 | **`【{project_name}】客户访谈记录-{date}.docx`** |
| `project_name` | 来自字段「项目名称」；文件名非法字符替换为 `-`；空则 `待补充` |
| `date` | 来自字段「访谈时间」，格式 `YYYY-MM-DD`；无法解析则用当天 |

示例：`【Acme科技】客户访谈记录-2026-05-29.docx`

## 工作流

```
输入 → 归一化 → 提取 9 字段 → [有缺失? 询问补全] → 填充 template → 校验 → 【XXX】客户访谈记录-日期.docx
```

### Step 0：前置

- 确认 `assets/template.docx` 存在
- 录音路径确认 `whisper` 可用（见 [`references/input-formats.md`](references/input-formats.md)）

### Step 1：输入归一化

按输入类型处理，见 [`references/input-formats.md`](references/input-formats.md)。

### Step 2：结构化提取

按 [`references/template-fields.md`](references/template-fields.md) 提取 9 个字段：

`project_name`、`interview_purpose`、`interview_time`、`interview_location`、`participants`、`topics`、`interview_notes`、`interview_results`、`interviewee_suggestions`

**内容格式化**：多行内容在 JSON 中用 `\n` 分隔；提取时保留原有换行，不要压成一行。

### Step 2.5：字段完整性检查（必做）

按 [`references/field-collection.md`](references/field-collection.md) 逐项判断上述 9 字段是否**已从素材明确得到**。

- **任一字段不充分** → **不得生成 docx**；用中文模板标签向用户列出缺失项，请其逐条补充（一次列全 9 项中缺的部分）。
- 用户补充后合并字段，重复检查，直至 9 项均可可靠填写。
- **禁止**在未询问的情况下，对大量字段静默填 `[待补充]`。
- 仅当用户明确表示「先出草稿 / 缺的用待补充 / 不用问了直接生成」时，方可对仍缺失项填 `[待补充]` 后生成，并事先告知哪些字段为待补充。

### Step 3：模板填充

**方式 A（推荐，本仓库脚本）**

```bash
python3 scripts/fill_interview_docx.py --fields-json fields.json --output-dir <输出目录>
# 或 stdin
cat fields.json | python3 scripts/fill_interview_docx.py --output-dir .
```

`fields.json` 键名见 `references/template-fields.md`。脚本只改表格第 2 列，自动输出 `【{project_name}】客户访谈记录-{date}.docx`。

**方式 B（外部 [docx skill](https://skills.sh/tfriedel/claude-office-skills/docx)）**

```bash
npx skills add https://github.com/tfriedel/claude-office-skills --skill docx
```

复制模板 → `unpack.py` → 改 `word/document.xml` 第 2 列 → `pack.py` → 按命名规则重命名。

### Step 4：校验

按 [`references/output-verification.md`](references/output-verification.md) 检查结构与文件名。

## 硬性规则

- **先问后填**：素材不足以覆盖 9 字段时，先询问补全，再生成 docx
- **不查飞书**：无用户提供的本地素材时，向用户索要文字/文件/录音，不要自己去飞书拉会议纪要
- 不得新建 Word 替代模板
- 不得改动页眉页脚、logo、表格行列数、第 1 列标签
- 输出文件名**必须**为 `【XXXX】客户访谈记录-日期.docx` 格式，不得用 `meeting-minutes.docx` 等泛名

## 参考

- [`references/field-collection.md`](references/field-collection.md) — 内容不足时的询问与补全
- [`references/template-fields.md`](references/template-fields.md) — 字段与文件名规则
- [`references/input-formats.md`](references/input-formats.md) — 文字 / Word / 录音
- [`references/output-verification.md`](references/output-verification.md) — 校验清单
- [`scripts/fill_interview_docx.py`](scripts/fill_interview_docx.py) — 本地填充脚本
- [docx skill](https://skills.sh/tfriedel/claude-office-skills/docx) — 备选 OOXML 流程
