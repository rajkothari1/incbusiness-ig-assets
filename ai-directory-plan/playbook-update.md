# AI Categories playbook: update for categories 61 to 180

Paste this into the site's AI Categories playbook (the file served at `/api/ai-directory/playbook`), in place of the current step 1. Then add the 120 entries from `new-categories.json` to the topics plan, so `GET /api/ai-directory/topics` returns them as `next`, one by one.

---

## 1. Pick the category

`GET /api/ai-directory/topics`. Build `next` (its `slug`, `name`, `icon`, `intro`) exactly.

If `next` is null, take the first category in the extended plan (`new-categories.json`, entries 61 to 180) whose slug is not already in `categories` in the topics response. Use its `slug`, `name`, `icon` and `intro` exactly. If every entry there is already on the site, stop and report.

Before building a category from the extended plan, check that it has at least 15 real, currently running AI tools available in India. If it doesn't, skip it, take the next one, and say in the report which one you skipped and why.

The response also lists every tool we already have (`tools`). If a tool you choose is already there (same website), send only its `slug`, `name` and `website` (use our existing slug): the site links it to the new category and keeps its checked facts. Write full entries only for new tools.

## 1b. When the plan is finished

If no category is left to build, don't stop there. Fill out the thinnest live category instead: the one with the fewest `published_tools` (under 15) in `categories`. Add new tools until it has 20, following steps 2 to 7, and send the category with its existing slug, name, icon and intro.
