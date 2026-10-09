# 输入格式处理

本 skill **只接受用户直接提供的素材**，不从飞书、妙记、日历等系统拉取内容。

## 1. 纯文本 / 粘贴内容

直接使用。从文本中提取 `template-fields.md` 所列字段，优先识别：

- 项目名称、客户名、访谈对象
- 时间（`YYYY-MM-DD`、`YYYY年M月D日`、`M/D` 等）
- 地点、参会人、议题、结论、建议

## 2. Word（.docx）

读取内容用 pandoc（**不作为输出**）：

```bash
pandoc --track-changes=accept input.docx -o extracted.md
```

若环境无 pandoc，解包 `word/document.xml` 提取纯文本。

## 3. 录音（mp3 / m4a / wav / mp4 等）

本地 Whisper 转写：

```bash
whisper "<audio>" --language Chinese --model medium --output_format txt
```

- 机器较慢时用 `--model small`
- 转写结果进入字段提取；关键决议、责任人可向用户确认后再写入

## 4. 归一化输出

所有输入最终合并为字段字典（见 `template-fields.md`），再进入模板填充步骤。
