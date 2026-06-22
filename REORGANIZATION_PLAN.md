# Reorganization Plan: Agentic-Ready Modular Structure

## Goal
Transform the current monolithic project structure into a modular, agent-friendly architecture where each presentation is a self-contained module. Ensure Git history is preserved using `git mv`.

## Proposed Structure
```text
/modules/
  ├── jsf-modern-architecture/    # JSF to Modern Architecture module
  │   ├── content.qmd             # Main presentation (formerly presentation.md/qmd)
  │   ├── guide.md                # The technical guide (formerly JSF_to_Modern...)
  │   └── assets/                 # Images and diagrams for this module
  ├── ai-developer-era/           # AI Developer Era module
  │   ├── content.qmd             # AI era contents
  │   └── prompts/                # Specific prompts for this era
  └── ...
/shared/
  ├── styles/                     # CSS (style.css, cinematic.css)
  ├── components/                 # Reusable UI components
  └── assets/                     # Global images/icons
/agents/
  ├── instructions/               # Agent system prompts
/configs/                         # Global configuration
/scripts/                         # Automation (build, deploy)
```

## Execution Steps [REORGANIZED]

### Phase 1: Core Infrastructure [DONE]
1. [x] Create `modules/`, `shared/`, `agents/`, `configs/`, `scripts/` directories.
2. [x] Move global assets (`css/`, `images/`, `diagrams/`) to `shared/`.

### Phase 2: Module Extraction (The `git mv` Phase) [DONE]
**Module: JSF Modern Architecture**
- [x] `git mv presentation.md modules/jsf-modern-architecture/content.qmd`
- [x] `git mv JSF_to_Modern_Architecture_Complete_Guide.md modules/jsf-modern-architecture/guide.md`
- [x] `git mv sunum.qmd modules/jsf-modern-architecture/content.qmd` (Update references)

**Module: AI Developer Era**
- [x] `git mv era_of_ai_developer/ modules/ai-developer-era/`
- [x] `git mv prompt.md modules/ai-developer-era/prompts/system_prompt.md`

**Module: General/Future Studies**
- [x] `git mv future_brainstorming_topics.md modules/future-studies/topics.md`
- [x] `git mv analysis_draft.md modules/analysis/draft.md`

### Phase 3: Cleanup & Refactoring [DONE]
1. [x] Update all internal links (`[text](./path)`) in `.md` files to reflect new paths.
2. [x] Create a `README.md` at the root explaining how to run/build specific modules.
3. [x] Final verification of Git trace.

---
**Status: REORGANIZATION COMPLETED (2024-04-03)**
Project is now in an Agentic-Ready Modular State.
