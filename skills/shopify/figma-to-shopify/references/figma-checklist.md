# Figma 读图核对清单

读 Figma 时按下列项逐条记录到 plan 文档，每项都要给出**具体值**或**与 Theme 现有 token 的映射**。

## 1. 页面骨架

- [ ] 页面类型（home / product / collection / page / article / custom template）
- [ ] 对应 template 文件（`templates/<type>.<handle>.json`）
- [ ] 现有 section 列表（按出现顺序）
- [ ] 待新增 / 复用 / 修改的 section 候选

## 2. 组件分解

为每个组件记录：

| 字段 | 值 | Theme token 映射 |
|------|----|-----------------|
| 名称 | e.g. hero-banner | — |
| 命名（kebab） | e.g. `cust-hero-banner` | 走 `new-section-rules` |
| 容器宽度 | e.g. `1440px` / `100%` | `--page-width`? |
| 内边距（桌面/移动） | e.g. `80px 0` / `40px 0` | `--section-padding-y`? |
| 背景色 | e.g. `#0A0A0A` | `var(--color-...)`? |
| 字号（desktop） | e.g. `48px` | `var(--font-size-heading-xl)`? |
| 字号（mobile） | e.g. `32px` | 同上 |
| 字重 | e.g. `600` | `var(--font-heading-weight)`? |
| 行高 | e.g. `1.2` | `var(--font-heading-line-height)`? |
| 字间距 | e.g. `-0.02em` | `var(--font-heading-letter-spacing)`? |
| 颜色 | e.g. `#FFFFFF` | `var(--color-...)`? |
| 圆角 | e.g. `8px` | `var(--radius-...)`? |
| 边框 | e.g. `1px solid #EAEAEA` | `var(--color-border)`? |
| 阴影 | e.g. `0 4px 12px rgba(0,0,0,0.08)` | `var(--shadow-...)`? |
| 间距（组件内元素） | e.g. `24px` | `var(--space-...)`? |

## 3. 交互

- [ ] Hover 态：颜色 / 位移 / 阴影变化
- [ ] Focus 态：outline 颜色 / 偏移
- [ ] Active / 点击反馈
- [ ] 滚动行为（sticky / parallax / fade-in）
- [ ] Carousel / Tab / Accordion / Modal

## 4. 响应式

- [ ] 桌面断点（Theme 默认）
- [ ] 平板断点
- [ ] 移动断点
- [ ] 每个断点下字号 / 间距 / 布局变化

## 5. 资源

- [ ] 图片（位置 + 比例 + 描述）
- [ ] 视频（格式 + 时长 + 是否循环 / autoplay / muted）
- [ ] 图标（SVG 路径或图标库）
- [ ] 字体（Figma 自带 vs Theme 已有）

## 6. 文案与多语言

- [ ] 文案是否需在 Theme Settings 中可配置
- [ ] 多语言策略（沿用 Theme locale schema）
- [ ] placeholder / 默认值

## 7. 与现有 Theme 的差异点

- [ ] Figma 中存在但 Theme 没有的颜色 / 字号 / 间距 → 是否需要新增 token（需用户确认）
- [ ] Theme 已有但 Figma 没明确给的 → 沿用 Theme 默认（需用户确认）
- [ ] 现有 section 可复用部分（结构 / 样式 / schema 片段）
