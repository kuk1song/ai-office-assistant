# 002: Adopt Kebab-Case for Documentation Filenames

**Status**: Accepted

## Context

Our documentation files were initially created with `PascalCase` names (e.g., `PROJECT_ROADMAP.md`). While functional, this naming convention is less common for documentation and can lead to potential issues with case-sensitive systems and URL formatting. We wanted to standardize on a convention that is robust, web-friendly, and aligns with common industry practices.

## Decision

We will use **kebab-case** (lowercase words separated by hyphens) for all documentation files in the `docs/` directory.

For example:
- `PROJECT_ROADMAP.md` becomes `project-roadmap.md`
- `TECHNICAL_ARCHITECTURE.md` becomes `technical-architecture.md`

## Consequences

### Positive
- **Cross-Platform Compatibility**: Eliminates potential conflicts between case-sensitive (Linux) and case-insensitive (Windows, macOS) file systems.
- **URL Friendliness**: Creates clean, readable, and standard-compliant URLs if the documentation is ever served over the web.
- **Consistency**: Aligns with a widely adopted naming convention in the software development community.
- **Readability**: The filenames are easy to read and type.

### Negative
- **Minor Disruption**: Requires a one-time effort to rename all existing files and update any internal links or references (such as in `bootstrapping-prompt.md`).

