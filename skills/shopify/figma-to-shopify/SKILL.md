---
name: figma-to-shopify
description: "根据 Figma 设计稿还原 Shopify 主题的 section/page：上传素材到 Shopify content files、按现有 Theme 架构（Variables / CSS Custom Properties / Design Tokens / Theme Settings / Section Settings / Blocks / Snippets）实现、遵循现有 rules（new/reuse/modify section）、最终用 Computer Use 在本地启动并截图比对。触发：用户提供 Figma URL 并要求'还原 Figma / 还原设计稿 / figma to shopify'。"
metadata:
  requires:
    bins: ["shopify", "node", "python3"]
    optional_bins: ["ffmpeg"]
---

# Figma → Shopify 还原

把 Figma 设计稿**像素级**还原到当前 Shopify Theme，遵循现有架构与 rules，最终跑起来截图比对。

**CRITICAL — 必读先决条件**：执行本 skill 之前，**必须**先向用户确认两件事：

1. **Figma 文件 URL**（桌面端 + 移动端两份 URL）。
2. **是否还有需要补充的细节**（品牌色例外、文案、动画、第三方库约束、未在 Figma 标注的边界条件等）。

在用户回复这两项前，**不要**进入任何规划或代码步骤。

---

## 角色与目标

你是 Figma→Shopify 还原工程师。目标：

- 最终视觉与 Figma **像素级一致**（Pixel Perfect）。
- 不为迁就现有实现而修改设计稿；不自行优化或猜测设计意图。
- 优先复用现有 Theme 资产：全局 CSS 变量、字体变量、Design Tokens、Theme Settings、Section Settings、Blocks、Snippets、现有 section / snippet / component。
- 在现有架构上扩展或调整；只有现有组件确实无法达到 Figma 效果时才新增样式/配置，并保持命名与 Theme 整体风格一致。
- 代码易维护、可复用，与 Theme 风格统一。

---

## 硬性规则（MUST）

1. **资源走 Shopify CLI**
   - 任何 Figma 中下载下来的图片 / 视频 / 字体等**资源文件**：
     - **必须**用 Shopify CLI 上传到 Shopify 后端 content files：
       ```bash
       shopify app dev   # 或
       shopify theme push --path <local-path>   # 用于把已有 assets 推上去
       # 推荐：把媒体先放到 assets/ 目录，theme dev / theme push 时由 Shopify 自动上传并生成 shopify:// URL
       ```
     - **必须**在 section / template / settings_schema 中以 `shopify://images/<file_id>` 形式引用（不要用外部 https URL，也不要直接引用本地路径）。
     - 上传后记录下生成的 file ID（从 theme deploy 输出或 `shopify theme info` 获取），写入 references/asset-manifest.md 便于复盘。
2. **严格遵守当前项目 rules**
   - **新建 section** → 必须遵守 `.agents/rules/shopify/new-section-rules.md`（命名 `cust-<kebab-case>`、配套 CSS/JS、schema、InsCoder 注释）。
   - **复用 / 拷贝改版 section** → 必须遵守 `.agents/rules/shopify/reuse-section-rules.md`（版本后缀、新 wrapper class、JSON template 更新）。
   - **修改现有 section** → 必须遵守 `.agents/rules/shopify/modify-section-rules.md`（影响评估、null/blank 检查、保留原行为、注释 + 回滚策略）。
   - **git push** → 必须遵守 `.agents/rules/common/git-push-restriction-rules.md`（远程 + 分支级明确确认）。
3. **不偏离 Figma**
   - 间距、字号、字重、行高、颜色、圆角、边框、阴影、图片比例、动画、交互、响应式断点**全部**按 Figma。
   - 禁止使用未在 Figma 标注的占位/猜测值。
4. **可配置优先**
   - 新增功能优先通过 Theme Settings / Section Settings / Blocks / 现有配置项实现。
   - 只有现有配置无法满足时才新增合理设置项，命名规范、架构与 Theme 一致。
5. **不污染全局**
   - 禁止修改全局 CSS / JS 文件；新功能创建独立 `cust-*.css` / `cust-*.js` 资产。
   - 复用 section 时必须用新 wrapper class 隔离。

---

## 工作流

```
确认 Figma URL（桌面 + 移动） + 补充细节
        ↓
[1] 读 Figma：分层、组件、token
        ↓
[2] 资产清单 + Shopify CLI 上传 → 取得 shopify://images/xxx
        ↓
[3] 决定走 new / reuse / modify 哪条 rules 分支
        ↓
[4] 在现有 Theme 架构上实现（CSS 变量优先 / 复用现有 section）
        ↓
[5] 启动本地开发：shopify theme dev
        ↓
[6] Computer Use 打开预览 → 桌面 + 移动端逐区截图 → 与 Figma 比对
        ↓
[7] 修复差异（CSS / Liquid / Settings）→ 再次截图比对
        ↓
[8] 交付：预览地址 + 截图对比 + 修改测试说明
```

### Step 0：前置确认（BLOCKING）

执行前**必须**问用户：

```text
请确认：
1. Figma 文件 URL（桌面端 + 移动端各一份，例如 https://www.figma.com/file/<id>/...?node-id=...）
2. 是否还有需要补充的细节？例如：
   - 品牌色例外（不在 Theme tokens 范围内的颜色）
   - 文案 / 多语言策略
   - 动画 / 交互（hover / scroll / carousel）
   - 第三方库限制（Swiper / GSAP / Flickity）
   - 响应式断点是否沿用 Theme 默认
```

**未收到这两项确认前，不要进入任何规划或写代码步骤。**

### Step 1：读 Figma

- 从桌面端 URL 读取布局、字体、颜色、间距、组件层级。
- 从移动端 URL 读取响应式布局、字号缩放、间距调整。
- 输出：组件分解表（每个组件的尺寸、颜色 token、字号、字重、行高、间距、圆角、阴影、交互）。

### Step 2：资产清单 + Shopify CLI 上传

对 Figma 中每个图片 / 视频 / 字体文件：

1. 记录原始 URL / 下载到 `assets/figma-source/<asset>`。
2. 用 Shopify CLI 上传：
   ```bash
   shopify theme dev
   # 或显式
   shopify theme push --path assets/<file> --nodelete
   ```
3. 从输出记录生成的 `shopify://images/<file_id>` 映射。
4. 写入 `references/asset-manifest.md`（每次实现时按需覆盖本 skill 的本地 manifest，便于回溯）。

### Step 3：rules 分支决策

根据实现策略决定走哪个 rules：

- 全新组件 / 之前没有的 section → 走 `new-section-rules`。
- 复制现有 section 后改版 → 走 `reuse-section-rules`。
- 在已有 section 上加块 / 改样式 / 改设置 → 走 `modify-section-rules`。

**多分支并存时，每个文件落地前必须先读完对应 rules 全文**。

### Step 4：实现（按现有架构）

实现顺序：

1. **先找现有**：在 `sections/`、`snippets/`、`assets/`、`config/` 中搜索是否有现成可复用 section / snippet / 样式类。
2. **复用现有 CSS 变量**：`--font-heading`、`--font-body`、颜色、间距、圆角等。**禁止硬编码**字体名、颜色十六进制。
3. **新建独立资产**：`assets/cust-<name>.css`、`assets/cust-<name>.js`、`sections/cust-<name>.liquid`，遵守对应 rules。
4. **schema 优先**：能用 Section Settings / Blocks 表达的，就别写死在 Liquid 里。
5. **InsCoder 注释**：所有新代码用 `/** InsCoder WANG.J YYYY-MM-DD B + ... **/` 与 `E + ... **/` 包夹（参考 `init-shopify` 中的注释格式）。
6. **空值保护**：所有动态内容、条件渲染用 `{% if x != blank %}`。

### Step 5：启动本地开发

```bash
shopify theme dev --store <store-name> --theme <local-theme-id>
```

确认本地预览地址（通常是 `http://127.0.0.1:9292` 或打印在终端的 URL）。

### Step 6：Computer Use 截图比对

调用 Computer Use skill：

1. 打开桌面端预览 → 截全屏 → 标注区域差异（间距、颜色、字号、组件对齐）。
2. 调整浏览器视口到移动端断点（375 / 414 之类按 Theme 设定）→ 截全屏 → 标注差异。
3. 把桌面 / 移动端截图分别与 Figma 同区域逐项比对：
   - 间距、字号、字重、行高、颜色、圆角、边框、阴影
   - 图片比例、布局对齐
   - 交互态（hover / focus / active）如 Figma 有标注

截图保存到 `<theme-repo>/screenshots/figma-to-shopify/<timestamp>/desktop.png` 与 `mobile.png`。

### Step 7：修复差异

针对每个差异：

- 优先调整 CSS 变量 / Token 对齐。
- 再调整 section 内样式（注意 wrapper class 隔离）。
- 必要时调整 section settings 让用户可配置。
- 修复后再跑一次 Step 6，直到视觉差异收敛到 ≤ 2px 视差或与用户确认可接受。

### Step 8：交付

输出**三项交付物**，缺一不可：

1. **预览地址**：本地 `shopify theme dev` 的 URL（带可访问 token / query 参数）。
2. **截图对比**：桌面 + 移动端截图，与 Figma 同区域并排 / 标注差异。
3. **修改测试内容描述**：
   - 修改了哪些 section / snippet / asset / settings
   - 走了哪个 rules（new / reuse / modify）
   - 已测试的功能列表（hover / 点击 / 移动端 / 多语言 / 浏览器兼容）
   - 已知差异 / 限制
   - 资源 manifest（哪些 `shopify://images/xxx` 已被引用）

---

## 边界

- **不**修改用户全局 OpenCode / Shopify CLI 配置。
- **不**自动 `git push`（按 `.agents/rules/common/git-push-restriction-rules.md` 等待用户逐次确认 remote + branch）。
- **不**删除其他 section / snippet / 资源。
- **不**修改全局 CSS / JS 已有规则（除非 Figma 要求且经用户确认）。
- **不**调用飞书 / 妙记 / VC 等任何与本任务无关的 skill。
- **不**用 `https://` 外链图片 / 视频（必须 `shopify://images/...`）。

---

## 参考

### 本 skill

- [`references/figma-checklist.md`](references/figma-checklist.md) — 读 Figma 时逐项核对清单
- [`references/asset-manifest.md`](references/asset-manifest.md) — 资源上传 / shopify:// 映射记录模板
- [`references/screenshot-comparison.md`](references/screenshot-comparison.md) — 截图比对规范与命名

### 关联 rules（必读）

rules 已作为本仓库的本地内容随 skill 一起维护，运行时不需要安装任何外部插件。落地前**先 Read 对应 rules 全文**：

- `.agents/rules/shopify/new-section-rules.md` — 新建 section 时必读
- `.agents/rules/shopify/reuse-section-rules.md` — 复用 section 时必读
- `.agents/rules/shopify/modify-section-rules.md` — 修改现有 section 时必读
- `.agents/rules/common/git-push-restriction-rules.md` — git push 前必读

## 启用方式

本 Skill 由 `agentflow bootstrap` 复制到项目的公共 `.agents/skills/figma-to-shopify/`。Codex、OpenCode 与 Oh My Pi 从公共目录发现；Claude Code 通过初始化器生成的 `.claude/skills/figma-to-shopify/` 薄映射读取同一份内容。不要再配置外部 Skill 路径。
