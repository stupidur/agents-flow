---
description: "Shopify attachment and image workflow: WebP conversion, Shopify Content Files upload, project references, and prohibition of Theme Editor Custom CSS development."
globs:
  - "layout/**/*.liquid"
  - "templates/**/*.{liquid,json}"
  - "sections/**/*.liquid"
  - "snippets/**/*.liquid"
  - "blocks/**/*.liquid"
  - "assets/**/*"
  - "config/**/*.json"
alwaysApply: false
---

# Shopify Media Asset And Theme Editor Rules

Apply this rule whenever a task uses image attachments from Basecamp, Notion,
Figma, Google Drive, email, local files, or another external source, or whenever
CSS placement is being decided.

## Mandatory Attachment Workflow

- **MUST** download or copy the source attachment to a local temporary or ignored
  working location before processing it.
- **MUST** convert every raster image attachment to WebP before it is uploaded,
  referenced, or added to the project.
- **MUST** use a descriptive, lowercase, kebab-case `.webp` filename.
- **MUST** preserve required transparency, aspect ratio, and sufficient visual
  quality during conversion.
- **MUST** verify the converted file opens correctly, has the intended pixel
  dimensions, and uses the WebP format rather than relying on the extension.
- **MUST NOT** add PNG, JPEG, JPG, TIFF, BMP, or other raster source attachments
  to the project when a WebP version can represent the required image.
- **MUST NOT** convert SVG icons or vector artwork to raster WebP unless the task
  explicitly requires raster output.

## Shopify Content Files Upload

- **MUST** upload the converted WebP to the target store's Shopify Admin
  **Content > Files** before adding its reference to theme code.
- **MUST** use the Shopify CLI store workflow. With current Shopify CLI versions,
  this means using `shopify store auth` and `shopify store execute` to run the
  Admin GraphQL `stagedUploadsCreate` and `fileCreate` mutations; the binary is
  sent to the signed staged target returned by Shopify.
- **MUST** request only the required file-writing scope, normally `write_files`,
  and include the exact `--store <store-domain>` target in CLI commands.
- **MUST** treat the upload and both mutations as remote writes. Before running
  them, obtain explicit user approval naming the target store and intended file
  upload. A task attachment alone is not upload approval.
- **MUST** inspect `userErrors` after each mutation and stop on any error.
- **MUST** wait until Shopify reports the created file's `fileStatus` as `READY`
  before using its URL or Liquid reference.
- **MUST** retain useful alt text when creating the Shopify file record.
- **MUST** avoid silently replacing an existing Content File. If the filename
  already exists, report the conflict and confirm whether to reuse, rename, or
  replace it.
- **MUST NOT** upload the unconverted source attachment.
- **MUST NOT** upload to a live store, development store, or any other remote
  store without explicit approval for that exact target and upload.

Official references:

- [Shopify `stagedUploadsCreate`](https://shopify.dev/docs/api/admin-graphql/latest/mutations/stagedUploadsCreate)
- [Shopify `fileCreate`](https://shopify.dev/docs/api/admin-graphql/latest/mutations/fileCreate)

## Adding The Uploaded Image To The Project

- **MUST** add only the Shopify-hosted Content File reference to theme code or
  the appropriate project configuration after the file is `READY`.
- **MUST** prefer an existing theme helper, Liquid file lookup, schema setting,
  or centralized data/config pattern over scattering a raw CDN URL through
  multiple files.
- **MUST** include meaningful `alt` text for informative images and `alt=""` for
  decorative images.
- **MUST** use responsive dimensions, `widths`, `sizes`, and the loading/fetch
  priority required by `.agents/rules/shopify/seo-rules.md`.
- **MUST** record the source attachment, converted filename, target store, and
  project files that reference the uploaded asset in the work summary.

## Theme Editor Custom CSS Prohibition

- **MUST NOT** implement features or fixes in Shopify Theme Editor's **Custom
  CSS** field.
- **MUST NOT** store CSS in a section/block `custom_css` setting or add a new
  merchant-editable raw CSS setting as a development shortcut.
- **MUST** place CSS in the project's existing scoped stylesheet pattern, such
  as an appropriate `assets/*.css` file or an established section stylesheet
  block.
- **MUST** scope CSS to the relevant section, block, component, or feature and
  follow the project's new/reuse/modify section rule as applicable.
- **MUST** migrate task-related Custom CSS into project-controlled source files
  when the task explicitly includes that migration; otherwise report existing
  editor CSS as a dependency or conflict instead of silently editing it.

## Verification Checklist

1. Confirm each raster attachment is a valid `.webp` file.
2. Confirm the user approved the exact target store and upload before any remote
   write.
3. Confirm Shopify Content Files reports `fileStatus: READY` with no user errors.
4. Confirm project references point to the intended Shopify-hosted file.
5. Confirm image alt text, dimensions, responsive behavior, and loading priority.
6. Confirm no task CSS was placed in Theme Editor Custom CSS or a raw custom CSS
   setting.
7. Report any upload, preview, or validation step that could not be completed.
