# Shopify Memory

## Live Theme And Branch Matching

Before pulling or modifying a live Shopify theme, list the store's live theme
using the read-only theme listing command:

```bash
shopify theme list --store=XXXX --role=live --json
```

Use the returned live theme `id` and `name` as the remote evidence. Compare the
meaningful information in `name` with the local Git branch and the requested
task branch. Matching may use the repository's documented naming convention,
but it must be reported explicitly; a theme name does not prove that a Git
branch and a remote Shopify theme are technically linked.

If there is no exact or documented normalized match, report that no branch/theme
match was verified and do not choose a theme or branch by guesswork. A live
theme listing is read-only; `theme pull`, `theme push`, and `theme publish` have
separate local or remote-write implications and must follow the active rules and
approval requirements.

## Store

<!-- Record a verified store domain only when the project explicitly confirms it. -->

## Theme Naming Convention

<!-- Record the project's verified theme/branch naming convention here. -->

## Unknowns

<!-- Keep unverified theme IDs, branch mappings, and deployment details here. -->
