<!--
PR template that reminds contributors and agents to read the AI memory docs
before making changes that affect retrieval, embeddings, prompt templates, or
other RAG-critical areas.
-->

## Summary

Describe the change in one sentence.

## Plan

Short bullet list of what this PR does.

## Files changed

List the primary files changed and one-line reason for each.

## Risk check

- [ ] I read `AI/CONTEXT.md`
- [ ] I read `AI/FILE_MAP.md`
- [ ] I read `AI/RULES.md`
- [ ] I read `AI/CURRENT_TASK.md` (if present)

If this change touches any of the fragile files listed in `AI/FILE_MAP.md` then also:

- [ ] I documented RAG impact in the PR body (retrieval accuracy, token/cost change)
- [ ] I added or updated tests for chunking/retrieval where applicable

## Tests

Describe tests added / updated and how to run them.

## Next steps

Any follow-ups or rollout notes.
