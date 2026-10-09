# 输出校验清单

生成 `【XXXX】客户访谈记录-日期.docx` 前须已通过 [`field-collection.md`](field-collection.md) 完整性检查（9 字段均已明确或用户授权待补充）。

生成后逐项检查：

## 结构

- [ ] 解包输出与 `assets/template.docx` 对比：`w:tbl` 仍为 9 行 2 列
- [ ] 第 1 列 9 个标签原文未变
- [ ] 标题「会议」「记录」未改

## 内容

- [ ] 9 个字段第 2 列均已填充（或明确标 `[待补充]`）
- [ ] 无残留 `{{...}}` 占位符
- [ ] 含 `\n` 的字段在 Word 中显示为多行/多段（参会人、议题、访谈记录等），不是挤在一行

## 文件名

- [ ] 符合 `【{project_name}】客户访谈记录-{YYYY-MM-DD}.docx`
- [ ] 不含非法文件名字符

## 可选视觉检查

```bash
soffice --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 150 output.pdf page
```

目视确认表格未跑版、样式与模板一致。
