# AI Assistant Bootstrapping Prompt Template

This document provides a template for quickly onboarding a new AI assistant (e.g., when switching IDEs or models) to the "AI Office Assistant" project.

## How to Use

1.  **Copy** the entire content of the "Prompt Template" section below.
2.  **Fill in** the `[bracketed]` placeholders with the most current information.
3.  **Paste** the completed prompt as the **very first message** to the new AI assistant.

This structured approach ensures the new assistant has all the necessary context to understand the project's goals, current state, and your immediate needs, enabling seamless and efficient collaboration from the start.

---

## Prompt Template

Hello, you are now my AI pair programming assistant. We are working on a Python Streamlit application called "AI Office Assistant". To get you up to speed, please first read and understand the following "Context Package" before we begin.

**1. Project Goal & Roadmap (The "Why" and "What"):**
*Reference: `docs/project-roadmap.md`*
```markdown
[Paste the latest, most relevant sections of project-roadmap.md here]
```

**2. Current Technical Architecture (The "How"):**
*Reference: `docs/technical-architecture.md`*
```markdown
[Paste the latest, most relevant sections of technical-architecture.md here]
```

**3. Key Architecture Decisions (The "Rationale"):**
*Reference: `docs/adr/`*
```markdown
[Paste the titles of the most recent/relevant ADRs. For example: "001: Use ADRs for logging decisions", "002: Adopt kebab-case for filenames"]
```

**4. Latest Research:**
*Reference: `docs/research-log.md`*
```markdown
[Briefly summarize the conclusion of the latest research entry.]
```

**5. Recent Progress (What just happened):**
*Reference: `git log --oneline -n 5`*
```
[Paste the output of the git log command here to show the last few commits]
```

**6. Summary of Our Last Conversation:**
```
[Provide a one-sentence summary of our last interaction.]
```

**7. My Current Focus:**
*Currently open file(s): `[List the file(s) you are actively working on]`*

---

**My Next Task:**

[State your next, specific instruction clearly here. For example: "Now, please review the code in `src/core/parser.py` and suggest improvements for clarity and efficiency."]

**Your Initial Actions:**

1.  Acknowledge that you have read and understood all the provided context.
2.  Begin working on "My Next Task".

