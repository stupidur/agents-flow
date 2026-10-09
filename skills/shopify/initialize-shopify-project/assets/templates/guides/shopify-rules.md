---
description: "Shopify 主题：按场景引用项目内 .agents/rules 路径（git / 新建 / 复用 / 修改 section）。"
---

# Shopify Rules Guide

这是工作区级说明，不是需要复制到项目里的 command。
在每个 Shopify 项目中，按场景遵守项目内已复制的规则文件：

- **必须** 针对 git 提交及一切可能影响远程仓库的操作时，遵守 **`.agents/rules/common/git-push-restriction-rules.md`**
- **必须** 用户可见的前端改动及浏览器/响应式验证时，遵守 **`.agents/rules/common/browser-testing-rules.md`**
- **必须** 新创建 section 时，遵守 **`.agents/rules/shopify/new-section-rules.md`**
- **必须** 复用（拷贝改版）section 时，遵守 **`.agents/rules/shopify/reuse-section-rules.md`**
- **必须** 修改现有 section 时，遵守 **`.agents/rules/shopify/modify-section-rules.md`**
- **必须** 涉及 SEO、页面 metadata、结构化数据、标题层级、链接、图片、面包屑或 SEO 相关性能时，遵守 **`.agents/rules/shopify/seo-rules.md`**
- **必须** 使用图片附件、转换 WebP、上传 Shopify Content Files 或决定 CSS 存放位置时，遵守 **`.agents/rules/shopify/media-asset-rules.md`**
- **必须** 编写 Shopify 样式、选择全局变量/design token/utility 或断点时，遵守 **`.agents/rules/shopify/theme-style-variable-rules.md`**

需要一次性生成完整项目上下文时，使用当前 skill 内的指南：
`assets/templates/guides/init-shopify-project.md`，
并在产出的项目 **`AGENTS.md`** 中保留与上述一致的「规则文件匹配」小节。
