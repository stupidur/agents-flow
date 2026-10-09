---
description: "Shopify 项目初始化指南：生成/更新项目 AGENTS.md，写入项目梳理、规则匹配与强制开发规范。"
---

# Shopify Project Initialization Guide

这是工作区级初始化指南，不是需要复制到项目里的 Codex command。
在新仓库、接手主题或重大架构变更后，按本指南生成/更新项目根目录的
`AGENTS.md`。

如果 handoff 声明 `global_context`，先读取该全局目录的 `AGENTS.md` 和适用
rules。以下 `.agents/` 路径必须通过 handoff 映射到已安装的全局路径；不要求
在项目重复复制 rules、skills 或客户端配置。初始化器使用
`--global-root <global_context.root>`，并在项目 `AGENTS.md` 添加「全局规则」
小节引用真实路径。全局层只读，项目特例不得静默放宽全局约束。

在执行本指南前，项目内应已安装/复制以下规则文件：

```text
.agents/rules/common/git-push-restriction-rules.md
.agents/rules/common/browser-testing-rules.md
.agents/rules/shopify/new-section-rules.md
.agents/rules/shopify/reuse-section-rules.md
.agents/rules/shopify/modify-section-rules.md
.agents/rules/shopify/seo-rules.md
.agents/rules/shopify/media-asset-rules.md
.agents/rules/shopify/theme-style-variable-rules.md
```

**执行步骤**

1. 通读仓库（`sections/`、`templates/`、`assets/`、`snippets/`、`config/`、`locales/` 等），记录真实目录与技术栈。
2. 在项目根创建或更新 `AGENTS.md`，包含两大块：
   - **「项目梳理」**：按下方「项目梳理提示」中的要求，结合代码逐条写清（可用表格与文件路径引用）。
   - **「团队强制规范」**：将下方「必须遵守的开发指南」至「实施清单」**全文**并入 `AGENTS.md`（若项目有特例，在文内增加「项目特例」小节说明与下文的差异）。
3. 若已有 `AGENTS.md`：保留有用历史内容并合并；冲突处增加「修订记录」（日期 + 摘要）。
4. 在 `AGENTS.md` 中增加 **「规则文件匹配」** 小节，写入下列八条；全局模式使用对应的实际全局路径：
   - **必须** 针对 git 提交及一切可能影响远程仓库的操作时，遵守 **`.agents/rules/common/git-push-restriction-rules.md`**
   - **必须** 用户可见的前端改动及浏览器/响应式验证时，遵守 **`.agents/rules/common/browser-testing-rules.md`**
   - **必须** 新创建 section 时，遵守 **`.agents/rules/shopify/new-section-rules.md`**
   - **必须** 复用（拷贝改版）section 时，遵守 **`.agents/rules/shopify/reuse-section-rules.md`**
   - **必须** 修改现有 section 时，遵守 **`.agents/rules/shopify/modify-section-rules.md`**
   - **必须** 涉及 SEO、页面 metadata、结构化数据、标题层级、链接、图片、面包屑或 SEO 相关性能时，遵守 **`.agents/rules/shopify/seo-rules.md`**
   - **必须** 使用图片附件、转换 WebP、上传 Shopify Content Files 或决定 CSS 存放位置时，遵守 **`.agents/rules/shopify/media-asset-rules.md`**
   - **必须** 编写 Shopify 样式、选择全局变量/design token/utility 或断点时，遵守 **`.agents/rules/shopify/theme-style-variable-rules.md`**
5. 验证当前 handoff 选定的浏览器技能；全局层已经提供时不重复安装。需要补充项目技能且初始化包含依赖安装时，可在项目目录安装 `ego-browser`：

   ```bash
   npx skills add github:CitroLabs/ego-lite/skills/ego-browser -a '*' -y
   ```

   并在项目 `AGENTS.md` 中明确浏览器工具路由：
   - ChatGPT/Codex 环境必须先加载并使用已安装的 Computer Use 插件 Skill/MCP tools；不得因为内置 Browser、Chrome control 或项目 `ego-browser` 已可见、熟悉或方便就跳过 Computer Use。
   - Computer Use 不可用、不支持当前操作或调用失败时，记录证据后使用 Ego Browser；Ego Browser 也不可用、不支持或失败时，使用 Playwright CLI，遵守同一个 `browser-preview` 权限范围。
   - 非 GPT Agent 从 Ego Browser 开始，必要时回退到 Playwright CLI；技能从 handoff 指定的项目或全局路径读取。
   - 浏览器能力不扩大远端操作授权；发布、上传、提交表单、购买或其它远端写操作仍需遵守工作区审批边界。
6. 检查项目 MCP 配置已按工作区模板复制：`.codex/config.toml`、`.claude/mcp.json`、`.opencode/opencode.json`、`.omp/config.yml`、`.omp/mcp.json`。
7. 检查项目 `.env` 已从当前 skill 的 `assets/templates/env/.env` 合并，至少包含 `FIGMA_API_KEY`；不得覆盖已有 `.env`，不得在报告、提交、评论中打印 token。
8. 检查并更新项目 `.gitignore`，合并工作区模板：
   当前 skill 的 `assets/templates/gitignore/shopify-project.gitignore`
   初始化模板会忽略本地 AgentFlow/client 产物 `.agentflow/`、`.omp/`、`.mcp.json`、`opencode.json`、`.env.example`，以及按当前项目约定作为本地任务产物的 `docs/`、`tests/`。如果项目需要提交正式文档或测试源码，必须先收窄或移除对应忽略项。
9. 完成后向用户说明 `AGENTS.md` 路径、规则文件所在位置、`.env` 是否存在且含 Figma token（不要输出 token 值）、Claude/Codex/OpenCode/OMP MCP 配置、`.gitignore` 是否更新、Shopify 官方/项目 skills 是否安装（包括 `https://github.com/stupidur/vibe-coding/tree/main/skills/shopify` 下的全部 Shopify skills 和项目级 `ego-browser`），以及后续日常开发要点。
10. 初始化 `AGENTS.md` 时必须添加「公共记忆」小节，并在项目 `.agents/project.yaml` 的 `context.include` 中包含 `.agents/memory/README.md`、`.agents/memory/global.md`、`.agents/memory/shopify.md`、`.agents/memory/workflows.md` 和 `.agents/memory/integrations.md`。这些文件由 `agentflow bootstrap` 从中央 `memory/` 复制；未知内容保留为空或标记为未知，不得猜测。

全局模式下，第 6、9、10 项改为报告实际全局客户端适配文件、技能和公共记忆
路径；客户端配置文件存在不代表已经激活。没有项目登记文件时不为记忆引用
创建额外登记，更不能修改全局 `project.yaml`。保留项目内已存在的配置与记忆。

---

## 项目梳理提示（写入 AGENTS.md「项目梳理」）

## 了解项目结构

使用一下提示词进行获取项目规则：

```
我正在开发/维护一个 Shopify 主题（或其他类型的主题），希望你能帮我梳理和总结一份详细、系统、实用的开发规范。请你结合项目实际情况，给出如下内容，并结合实际代码和项目结构，给出具体、可操作的建议和代码示例，并整理生成成一份 AGENTS.md Markdown 上下文文档，便于团队协作和长期维护。

1. 全局样式与变量：包括全局宽度、字体、颜色、按钮等统一规范，是否有全局 CSS 变量，如何统一管理和复用。
2. 全局可复用 class 列表：有哪些全局工具类、布局类、按钮类、标题类等可以直接复用？请列举并简要说明用途。
3. 栅格系统与布局规范：主题是否集成了 CSS 框架（如 Bootstrap、Tailwind、Foundation 等）或自定义栅格系统？如何使用？有无响应式设计建议？
4. Section/组件开发规范：如何实现样式和 JS 的隔离？命名、结构、复用、可访问性等方面的最佳实践。
5. JS 代码规范：如何避免全局污染？如何与 Section 关联？事件绑定、解绑、命名等建议。
6. Liquid 代码规范：变量、区块、Snippet 的复用和命名规范。
7. 多语言与资源管理：如何处理多语言、图片、静态资源等。
8. 三方插件与依赖：请梳理项目中是否集成了如 Swiper、Flickity、GSAP、jQuery 等三方 JS/CSS 插件或库，统一用法和引用方式，定制开发时如何复用和避免冲突。
9. 其它注意事项：如与 Shopify 官方规范的兼容性、升级维护建议、团队协作建议等。
```

## 必须遵守的开发指南

### 本地开发命令

- **必须** 使用 `npm run start` 进行本地开发服务器
- **不得** 使用其他命令除非明确要求
- **允许** `npm run pull`、`npm run push`、`npm run sync` 仅在特别要求时

### 页面预览

- **必须** 如果创建了新的 template 在预览的时候，请按照 shopify 的规范进行预览，使用存在的 page、product、collection 添加 view 参数进行预览

示例：`view={{template-name}}` 用于模板，这个格式适合 product、page、collection 等

- **必须** 提供新功能/模板的主题编辑器URL格式：

```
https://{{store-name}}.myshopify.com/admin/themes/{{local-theme-id}}/editor?template={{template-name}}
```

示例：`template=page.quiz-results-preview` 用于页面模板



### 开发范围限制

- **不得** 添加任务描述中未明确要求的功能(包括悬停动画、交互功能)
- **不得** 在没有明确指示的情况下修改现有功能

- **必须** 严格遵循提供的需求
- **必须** 在需求不明确时请求澄清
- **必须** 严格评估修改是否与任务直接相关
- **必须** 只关注任务描述中请求的具体功能
- **必须** 移动端和桌面端一定注意媒体查询的分界点（使用主题的分界点进行编码）

### 规则匹配

- **必须** 针对 git 提交及一切可能影响远程仓库的操作时，匹配 `.agents/rules/common/git-push-restriction-rules.md`
- 用户可见的前端改动及浏览器/响应式验证时匹配 `.agents/rules/common/browser-testing-rules.md`
- 当新创建 section 的时候匹配 `.agents/rules/shopify/new-section-rules.md`
- 当复用 section 的时候匹配 `.agents/rules/shopify/reuse-section-rules.md`
- 当修改 section 的时候匹配 `.agents/rules/shopify/modify-section-rules.md`
- 当涉及 SEO、页面 metadata、结构化数据、标题层级、链接、图片、面包屑或 SEO 相关性能时匹配 `.agents/rules/shopify/seo-rules.md`
- 当使用图片附件、转换 WebP、上传 Shopify Content Files 或决定 CSS 存放位置时匹配 `.agents/rules/shopify/media-asset-rules.md`
- 当编写 Shopify 样式、选择全局变量/design token/utility 或断点时匹配 `.agents/rules/shopify/theme-style-variable-rules.md`

### CSS 开发规则

#### 字体变量使用规则

- **禁止** 直接在 CSS 中硬编码字体名称（如 'Cosi Times', 'Riforma LL' 等）

- **必须** 使用 Figma 中字体的时候，仅可使用全局变量 `--font-heading` 和 `--font-body` 的变量
- **必须** 使用完整的字体变量集合，包括字重、样式、字间距等
- **必须** 通过全局变量确保字体的一致性和可维护性

#### 字体变量使用示例

```css
/* ✅ 正确的字体变量使用 */
.heading-element {
  font-family: var(--font-heading);
  font-weight: var(--font-heading-weight);
  font-style: var(--font-heading-style);
  letter-spacing: var(--font-heading-base-letter-spacing);
  text-transform: var(--font-heading-text-transform);
}

.body-element {
  font-family: var(--font-body);
  font-weight: var(--font-body-weight);
  font-style: var(--font-body-style);
  letter-spacing: var(--font-body-base-letter-spacing);
}

/* ❌ 错误的字体使用方式 */
.wrong-element {
  font-family: 'Cosi Times', serif;  /* 禁止硬编码字体名称 */
  font-family: 'Riforma LL', sans-serif;  /* 禁止硬编码字体名称 */
}
```

#### 其他 CSS 规则

- **必须** 优先检索并调用主题已有的全局 CSS variable、design token、adapter、utility class 和 breakpoint，不得在每个 section 内重复 hardcode 相同样式值
- **不得** 编写可能影响其他组件的全局CSS
- **不得** 除非绝对必要，否则不得修改全局CSS文件
- **不得** 直接修改文件中的现有CSS规则，使用文件末尾添加CSS进行覆盖
- **不得** 写行内样式，需要通过行内定义自定义变量，然后在CSS中使用

- **必须** 使用最简单的选择器以避免冗余，避免不必要地重复现有样式
- **必须** 依赖CSS层叠顺序（后者的样式覆盖前者）
- **必须** 将所有CSS范围限定以防止影响其他部分
- **必须** 使用特定于部分的类命名约定
- **必须** 为新功能创建自定义CSS文件以避免影响加载速度
- **必须** 将新CSS追加到现有文件的末尾以覆盖原始样式
- **必须** 在使用 `!important` 之前评估CSS特定性，仅在现有样式无法通过特定性覆盖时使用 `!important`
- **必须** 使用层叠顺序来覆盖现有样式而不是编辑原始代码

#### CSS 结构示例：
```css
.section-quiz-results {
  /* Section-specific styles only */
}

.section-quiz-results .quiz-item {
  /* Nested elements with parent scope */
}

/* Simple override example - no need to repeat existing styles */
.quiz-item {
  color: red; /* Will override earlier styles due to cascade order */
}
```

#### CSS 覆盖模式：
```css
/* Original styles above... */

/** InsCoder 2025-07-21 B + Custom quiz results styling **/
.existing-class {
  /* Override styles here */
}
/** InsCoder 2025-07-21 E + Custom quiz results styling **/
```

#### CSS修改方法:
```css
/* ❌ WRONG: Direct modification of existing styles */
.original-class {
  color: blue; /* Don't modify this directly */
}

/* ✅ CORRECT: Append override at end of file */
.original-class {
  color: red; /* This will override the original blue color */
}
```

### JavaScript 开发规则

- **禁止** 修改全局 JavaScript 文件，除非绝对必要

- **必须** 为新功能创建单独的定制 JS 文件
- **必须** 避免添加到全局作用域，以防止加载速度影响

### 部分或块设置验证

- **禁止** 渲染空或未定义的内容

- **必须** 在渲染前检查设置值是否为空
- **必须** 对所有动态内容使用条件渲染

#### Liquid 验证为空：

```liquid
{% if section.settings.title != blank %}
  <h2>{{ section.settings.title }}</h2>
{% endif %}

{% if block.settings.image != blank %}
  <img src="{{ block.settings.image | img_url: '800x' }}" alt="{{ block.settings.image.alt }}">
{% endif %}
```

### 代码注释标准

- 如果需要添加注释，使用以下注释模板

#### CSS 注释:
```css
/** InsCoder 2025-07-21 B + Feature description **/
.your-styles {
  /* CSS code here */
}
/** InsCoder 2025-07-21 E + Feature description **/
```

#### JavaScript 注释:
```javascript
/** InsCoder 2025-07-21 B + Feature description **/
function yourFunction() {
  // JavaScript code here
}
/** InsCoder 2025-07-21 E + Feature description **/
```
### 性能优化规则

- **必须**优先考虑自定义文件而非全局修改，最小化对主题加载速度的影响，仅在需要时加载自定义资源
- **必须**通过覆盖方法保留原始CSS文件，通过追加而非编辑来维护文件完整性

### 代码质量标准

- **必须**验证所有来自设置的用户输入
- **必须**为缺失的数据提供回退内容
- **必须**使用语义化的HTML结构
- **必须**遵循Shopify Liquid最佳实践
- **必须**包含适当的可访问性属性

### 附件、图片与 Custom CSS

- **必须** 将任务使用的栅格图片附件转换为 WebP 后再上传或引用
- **必须** 经用户明确批准目标店铺和文件上传后，使用 Shopify CLI 驱动的 staged upload + `fileCreate` 流程上传到 Shopify Admin 的 Content > Files
- **必须** 等待 Content File 状态为 `READY` 后再把 Shopify 托管的文件引用添加到项目
- **禁止** 使用 Theme Editor 的 Custom CSS 字段或 merchant-editable raw CSS setting 进行功能开发；CSS 必须写入项目受控且按组件限定作用域的样式文件

## 实施清单

在提交代码前，请验证以下内容：

- [ ] CSS已正确限定在父节段内
- [ ] 所有设置已验证空值
- [ ] 未添加未经授权的功能
- [ ] 使用自定义文件而非全局修改
- [ ] 新CSS追加在文件末尾以进行覆盖
- [ ] 所有新代码都有适当的InsCoder注释
- [ ] 提供了新模板的主题编辑器URL
- [ ] 指定了本地开发命令
- [ ] 最小化了性能影响
