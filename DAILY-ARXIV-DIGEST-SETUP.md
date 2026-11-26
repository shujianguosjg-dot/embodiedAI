# Daily embodied-AI paper source bundle

This workflow is a networked collector for the daily Chinese paper brief. It avoids relying on the ChatGPT Scheduled Task runtime to fetch arbitrary websites.

## What it does

- Runs daily at 08:35 Asia/Taipei, leaving a buffer before the 09:00 ChatGPT brief.
- Queries arXiv cs.RO, cs.CV, and cs.LG independently, sorted by last update, and keeps records updated within 14 days.
- Uses keyword relevance to prepare a shortlist, but does not claim that keyword score is scientific quality.
- Checks Hugging Face Daily Papers for upvotes/comments and searches GitHub README references for code signals.
- Tries arXiv HTML and ar5iv for full-text excerpts; marks papers as abstract-only if neither works.
- Commits JSON evidence to data/paper-digests/YYYY-MM-DD.json and data/paper-digests/latest.json.

No model API key is required. The ChatGPT task can use the connected GitHub app to read the JSON evidence and write the human-facing analysis itself.

## Enable it

1. Merge this PR into the repository default branch (main). GitHub scheduled workflows run only from the default branch.
2. In GitHub, open Settings > Actions > General > Workflow permissions and allow Read and write permissions if the workflow cannot push its daily JSON file.
3. Open Actions > Collect daily embodied-AI papers > Run workflow once to test immediately.
4. Confirm that data/paper-digests/latest.json appears and that the run log reports the arXiv/HF/GitHub source status.

The workflow uses the built-in GITHUB_TOKEN; do not add a personal access token or put credentials in the repository.

## Connect it to the 09:00 ChatGPT task

After the first successful Actions run, update the existing ChatGPT task to:

- Read data/paper-digests/latest.json from shujianguosjg-dot/embodiedAI using the connected GitHub app.
- Use the bundle source_status, published, updated, affiliations, HF engagement, GitHub repositories and full-text excerpts as evidence.
- Select 1–5 papers based on scientific value. Community popularity and institution names are corroborating signals, not substitutes for technical quality.
- If the bundle is missing or the collector failed, report that the collector did not produce evidence. Do not claim that arXiv is down and do not invent papers.

The existing ChatGPT task remains scheduled for 09:00 Asia/Taipei. The collector is scheduled for 08:35 to reduce the chance of a race.

## Limitations and provenance

- arXiv author affiliations may be absent from metadata. If absent, the ChatGPT brief must verify them from an official lab/project page or mark them unknown.
- Hugging Face upvotes and GitHub search results are point-in-time signals, not independent validation.
- A missing HTML full-text excerpt means only metadata/abstract was collected; the brief must not invent method or experiment details.
- GitHub scheduled workflows can be delayed under load. Check the Actions run timestamp if the 09:00 task reports a missing bundle.
