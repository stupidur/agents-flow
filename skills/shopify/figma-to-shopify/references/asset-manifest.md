# Asset Manifest — `shopify://images/...` 映射

每个 Figma 还原任务，**必须**维护一份本表。文件放在任务工作目录，路径示例：

```
<theme-repo>/.figma-to-shopify/<task-slug>/asset-manifest.md
```

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| 任务 slug | ✅ | 短横线小写，对应一次还原任务 |
| figma_url | ✅ | 该资源的 Figma 节点 URL |
| local_path | ✅ | 落地到 theme `assets/figma-source/<task>/<file>` 的路径 |
| type | ✅ | image / video / font / svg / other |
| upload_cmd | ✅ | 实际执行的 `shopify` 命令 |
| shopify_url | ✅ | 上传后生成的 `shopify://images/<file_id>` |
| used_in | ✅ | 被哪些 section / settings_schema 引用，列出文件:行号 |
| notes | — | 备注：动图? 跨设备尺寸? 字体授权? |

## 模板

```markdown
# Task: <task-slug>
Date: YYYY-MM-DD
Figma: <desktop url> | <mobile url>

| figma_url | local_path | type | shopify_url | used_in | notes |
|-----------|------------|------|-------------|---------|-------|
| https://.../node-id=123 | assets/figma-source/landing/hero-bg.jpg | image | shopify://images/abc123 | sections/cust-hero-banner.liquid:14 | 1920x1080 |
```

## 上传流程（Shopify CLI）

```bash
# 1. 把媒体放到 theme assets/
mkdir -p assets/figma-source/<task>
cp /path/from/figma/* assets/figma-source/<task>/

# 2. theme dev 模式（自动 watch & upload assets 变化）
shopify theme dev --store <store> --theme <id>

# 3. 或显式 push 单文件
shopify theme push --path assets/figma-source/<task>/<file> --nodelete
```

读取生成的 `shopify://images/<id>`：

- `theme dev` 输出在终端日志中；
- 或 `shopify theme info` 查 asset 列表；
- 或 Shopify Admin → Content → Files 拿到 ID。

## 引用规范

```liquid
<!-- 正确 -->
<img src="{{ 'cust-hero-banner.jpg' | file_url }}" alt="...">
<!-- 进一步：用 settings 注入 shopify:// URL -->
{% if section.settings.hero_image != blank %}
  <img src="{{ section.settings.hero_image | image_url: 'master' }}" alt="...">
{% endif %}
```

**禁止**：

```liquid
<!-- 禁止 -->
<img src="https://www.figma.com/...?node-id=...">
<img src="/assets/figma-source/...">  <!-- 本地路径，不进生产 -->
```
