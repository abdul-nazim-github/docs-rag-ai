Before any task:

1. Read AI/CONTEXT.md
2. Read AI/FILE_MAP.md
3. Read AI/RULES.md
4. Read AI/CURRENT_TASK.md (if present)

## Search Strategy

Before searching code:

1. Read FILE_MAP.md
2. Identify pipeline stage (ingest, chunk, embed, store, retrieve, prompt)
3. Search only related files

Expand search only if required by imports, dependencies, or acceptance criteria.

Never scan the whole repository first.

## RAG Anti-Hallucination Rules

* Retrieval logic not documented → ask before changing.
* Prompt template not documented → ask before modifying.
* Embedding model unclear → ask.
* Vector DB unclear → ask.
* Multiple RAG approaches possible → present options.

## Output Format

When producing changes provide exactly these sections:

### Plan

### Files to change

### Files NOT changed

### Code

### Risk check

### Next steps
