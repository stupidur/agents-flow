# 截图比对规范

## 路径

```
<theme-repo>/screenshots/figma-to-shopify/<task-slug>/<YYYY-MM-DD>/<round>/
├── desktop/
│   ├── full.png
│   ├── 01-hero.png
│   ├── 02-features.png
│   └── ...
├── mobile/
│   ├── full.png
│   ├── 01-hero.png
│   └── ...
└── diff.md
```

- `task-slug`：短横线小写。
- `<YYYY-MM-DD>`：截图日期。
- `<round>`：`r1` 首次 / `r2` 修复后 / ... 累加。

## 截图流程

调用 Computer Use skill，按下列步骤：

1. **桌面端**（viewport 1440×900 或 Theme 设定宽度）：
   1. 打开本地预览 URL（含 `?preview_theme_id=...` query）。
   2. 等待页面 ready（networkidle）。
   3. 截全屏 → `desktop/full.png`。
   4. 逐区滚动 → 截每个关键 section → `desktop/<NN>-<section>.png`。
2. **移动端**（viewport 375×812 或 Theme 移动断点）：
   1. 切到移动视口。
   2. 同上，输出到 `mobile/`。
3. **交互态**（Figma 有标注时）：
   1. hover / focus / active 各截一组 → `desktop/interactions/`。
4. **保存 Figma 同区域参考图** → `figma-ref/`（可手动导出 PNG 后归档）。

## diff.md 模板

```markdown
# Diff Report — <task-slug> round <r>
Date: YYYY-MM-DD
Figma: <desktop url> | <mobile url>
Preview: <local dev url>

## 差异清单

| 区域 | 桌面 | 移动 | 差异 | 修复方案 | 状态 |
|------|------|------|------|----------|------|
| hero title 字号 | 48px ✅ | 32px → 28px ❌ | mobile 字号偏小 | 调整 mobile breakpoint token | TODO |
| hero 间距 | 80px ✅ | 40px ❌ | mobile padding 不够 | 调整 section settings | TODO |
| CTA 圆角 | 8px ✅ | 8px ✅ | — | — | OK |
```

每条差异给出：

- Figma 期望值
- 实际截图测量值
- 根因（CSS 变量 / 媒体查询 / 资产未替换 / Settings 缺项）
- 修复方案（具体到文件:行号 + 改动）
- 状态：OK / TODO / 已修复

## 验收标准

视觉差异 ≤ 2px 视差或与用户确认可接受后，才能进入 Step 8 交付。
