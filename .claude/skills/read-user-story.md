---
name: read-user-story
description: Fetch the user story from Confluence using the MCP server, extract structured content, and save it to artifacts/user-story.md.
---

# Read User Story

Fetch and parse the user story for the current SDLC cycle.

## Instructions

1. Use the `confluence-requirements` MCP server tool `read_user_story` to fetch the story from Confluence.
   - Page ID is set in `.env` as `CONFLUENCE_PAGE_ID` (currently `44498945`).
   - Space key: `CONFLUENCE_SPACE_KEY` from `.env`.

2. If the MCP tool is unavailable, fall back to reading `artifacts/user_story.md` directly.

3. Extract the following structured fields:
   - **Story statement**: As a… I want… So that…
   - **Acceptance criteria** (numbered list)
   - **Business rules**
   - **Assumptions and constraints**
   - **Definition of Done**

4. Save the parsed output to `artifacts/user-story.md`.

5. Confirm the JIRA story key from `.env` (`JIRA_STORY_KEY`) for traceability.

## MCP Tool Reference

```
Tool: read_user_story
Server: confluence-requirements (configured in .claude/settings.local.json)
Parameters: page_id (string), space_key (string, optional)
```

## Output Format

```markdown
# User Story — <JIRA_STORY_KEY>

## Story Statement
As a <role>, I want <goal>, so that <benefit>.

## Acceptance Criteria
1. ...
2. ...

## Business Rules
- ...

## Assumptions and Constraints
- ...

## Definition of Done
- [ ] ...
```

## Notes

- MCP credentials live in `mcp_server/.env` — do not print or log them.
- If the Confluence page is not found, check that `CONFLUENCE_PAGE_ID` in `.env` is correct and the MCP server is running.
