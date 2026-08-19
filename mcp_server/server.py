#!/usr/bin/env python3
"""
Capstone MCP Server  -  Requirements Gathering
Reads user stories from Confluence/JIRA, facilitates Q&A, creates JIRA stories,
and generates requirements.md for the Agentic SDLC pipeline.
"""

import os
import sys
import json
import re
from typing import Any, Optional, List, Dict
from datetime import datetime

try:
    import requests
    from requests.auth import HTTPBasicAuth
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError as e:
    print(f"Error importing requests: {e}", file=sys.stderr)
    sys.exit(1)

try:
    import docx
except ImportError as e:
    print(f"Error importing python-docx: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None

try:
    from mcp.server import MCPServer
except ImportError as e:
    print(f"Error importing MCP: {e}", file=sys.stderr)
    sys.exit(1)

# Load .env from same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "EPMCDMETST")

confluence_auth = None
if CONFLUENCE_URL and CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN:
    confluence_auth = HTTPBasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)

jira_headers = None
if JIRA_URL and JIRA_API_TOKEN:
    jira_headers = {
        "Authorization": f"Bearer {JIRA_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

app = MCPServer("capstone-requirements-automation")
qa_sessions: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _confluence_base() -> str:
    base = CONFLUENCE_URL.rstrip('/')
    return base if base.endswith('/wiki') else base + '/wiki'


def read_confluence_page(page_id: str = None, space_key: str = None, page_title: str = None) -> str:
    if not confluence_auth:
        raise Exception("Confluence credentials not configured.")
    base = _confluence_base()
    if page_id:
        r = requests.get(f"{base}/rest/api/content/{page_id}?expand=body.storage", auth=confluence_auth)
        r.raise_for_status()
        page = r.json()
    elif space_key and page_title:
        url = f"{base}/rest/api/content?spaceKey={space_key}&title={requests.utils.quote(page_title)}&expand=body.storage"
        r = requests.get(url, auth=confluence_auth)
        r.raise_for_status()
        results = r.json().get('results', [])
        if not results:
            raise ValueError(f"Page '{page_title}' not found in space '{space_key}'")
        page = results[0]
    else:
        raise ValueError("Provide page_id or (space_key + page_title).")
    html = page['body']['storage']['value']
    text = re.sub('<[^<]+?>', '', html)
    text = re.sub(r'&ndash;', '-', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    return text


def read_jira_issue_data(issue_key: str) -> Dict[str, Any]:
    if not jira_headers:
        raise Exception("JIRA credentials not configured.")
    r = requests.get(f"{JIRA_URL}/rest/api/2/issue/{issue_key}", headers=jira_headers, verify=False)
    r.raise_for_status()
    issue = r.json()
    f = issue.get('fields', {})
    return {
        "key": issue.get('key'),
        "summary": f.get('summary', ''),
        "description": f.get('description') or '',
        "issue_type": (f.get('issuetype') or {}).get('name', ''),
        "status": (f.get('status') or {}).get('name', ''),
        "priority": (f.get('priority') or {}).get('name', 'None'),
        "assignee": (f.get('assignee') or {}).get('displayName', 'Unassigned'),
        "reporter": (f.get('reporter') or {}).get('displayName', 'Unknown'),
        "created": f.get('created', ''),
        "updated": f.get('updated', ''),
        "url": f"{JIRA_URL}/browse/{issue.get('key')}",
    }


def _create_jira_story(summary: str, description: str, project_key: str = None) -> Dict[str, Any]:
    if not jira_headers:
        raise Exception("JIRA credentials not configured.")
    pkey = project_key or JIRA_PROJECT_KEY
    r = requests.post(
        f"{JIRA_URL}/rest/api/2/issue",
        headers=jira_headers,
        json={"fields": {"project": {"key": pkey}, "summary": summary,
                         "issuetype": {"name": "Story"}, "description": description}},
        verify=False
    )
    r.raise_for_status()
    data = r.json()
    key = data.get('key')
    return {"key": key, "id": data.get('id'), "url": f"{JIRA_URL}/browse/{key}", "project": pkey}


def _word_text(file_path: str) -> str:
    doc = docx.Document(file_path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    return "\n".join(parts)


def _generate_questions(story: str) -> List[str]:
    lower = story.lower()
    q = []
    if "user" in lower or "customer" in lower:
        q += ["Who are the primary users/personas?",
              "What key user workflows should this support?"]
    if "acceptance" not in lower and "criteria" not in lower:
        q.append("What are the specific acceptance criteria?")
    if "api" in lower or "integration" in lower:
        q += ["What are the API/integration requirements and data formats?",
              "Are there rate limiting or performance requirements?"]
    if "ui" in lower or "interface" in lower or "screen" in lower:
        q += ["What are the UI/UX design requirements and mockups?",
              "Should the UI be responsive? What devices should be supported?"]
    if "security" in lower or "auth" in lower or "permission" in lower:
        q += ["What are the security and authentication requirements?",
              "What data privacy considerations should be addressed?"]
    if "data" in lower or "database" in lower:
        q += ["What are the data model and schema requirements?",
              "What are the data retention and backup requirements?"]
    q += [
        "What are the performance requirements (response time, throughput)?",
        "What are the scalability requirements?",
        "Are there accessibility requirements (WCAG compliance)?",
        "What are the dependencies on other systems or components?",
        "Are there third-party services or libraries required?",
        "What are the technical constraints or limitations?",
        "What is the expected timeline and priority?",
        "What are the testing requirements (unit, integration, e2e)?",
        "What is the expected test coverage?",
        "What are the deployment and rollback strategies?",
        "Are there infrastructure or environment requirements?",
        "What are the success metrics for this feature?",
        "Are there known edge cases or error scenarios to handle?",
        "What documentation needs to be created or updated?",
    ]
    return q


def _format_doc(user_story, source_info, qa_pairs, func_reqs, nonfunc_reqs, constraints, ac) -> str:
    doc = f"""# Requirements Document

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Source:** {source_info.get('source_type', 'Unknown')}
**Reference:** {source_info.get('reference', 'N/A')}

---

## 1. User Story

{user_story}

---

## 2. Stakeholder Q&A

"""
    if qa_pairs:
        for i, qa in enumerate(qa_pairs, 1):
            doc += f"### Q{i}: {qa['question']}\n\n**Answer:** {qa['answer']}\n\n"
    else:
        doc += "*No Q&A session conducted.*\n\n"

    def section(title, items, numbered=True):
        s = f"---\n\n## {title}\n\n"
        if items:
            for i, it in enumerate(items, 1):
                s += (f"{i}. {it}\n" if numbered else f"- [ ] {it}\n")
        else:
            s += "*To be defined*\n"
        return s + "\n"

    doc += section("3. Functional Requirements", func_reqs)
    doc += section("4. Non-Functional Requirements", nonfunc_reqs)
    doc += section("5. Constraints & Limitations", constraints)
    doc += section("6. Acceptance Criteria", ac, numbered=False)
    doc += "---\n\n## 7. Success Metrics\n\n*To be defined*\n\n"
    doc += "---\n\n## 8. Dependencies\n\n*To be defined*\n\n"
    doc += "---\n\n## 9. Risks & Mitigations\n\n*To be defined*\n\n"
    doc += "---\n\n## 10. Documentation & Training Needs\n\n*To be defined*\n\n"
    return doc


# ---------------------------------------------------------------------------
# MCP Tools (MCP 2.0)
# ---------------------------------------------------------------------------

@app.tool()
def read_user_story(
    source_type: str,
    session_id: Optional[str] = None,
    confluence_page_id: Optional[str] = None,
    confluence_space_key: Optional[str] = None,
    confluence_page_title: Optional[str] = None,
    jira_issue_key: Optional[str] = None,
    word_file_path: Optional[str] = None,
) -> str:
    """Read a user story from Confluence (page_id or space_key+title), JIRA, or Word. First step."""
    sid = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    source_info = {"source_type": source_type}
    content = ""

    if source_type == "confluence":
        content = read_confluence_page(confluence_page_id, confluence_space_key, confluence_page_title)
        source_info["reference"] = confluence_page_id or f"{confluence_space_key}/{confluence_page_title}"
    elif source_type == "jira":
        data = read_jira_issue_data(jira_issue_key)
        content = (f"**Summary:** {data['summary']}\n\n**Description:**\n{data['description']}\n\n"
                   f"**Type:** {data['issue_type']}  **Status:** {data['status']}\n"
                   f"**URL:** {data['url']}\n")
        source_info["reference"] = jira_issue_key
    elif source_type == "word":
        content = _word_text(word_file_path)
        source_info["reference"] = word_file_path
    else:
        raise ValueError(f"Unknown source_type: {source_type}")

    qa_sessions[sid] = {
        "user_story": content, "source_info": source_info,
        "qa_pairs": [], "created_at": datetime.now().isoformat(), "status": "active"
    }
    return json.dumps({"success": True, "session_id": sid, "user_story": content,
                       "source_info": source_info,
                       "message": f"User story loaded from {source_type}. Session: {sid}"}, indent=2)


@app.tool()
def generate_questions(session_id: str, additional_context: Optional[str] = None) -> str:
    """Generate clarifying questions based on the user story."""
    if session_id not in qa_sessions:
        raise ValueError(f"Session {session_id} not found")
    session = qa_sessions[session_id]
    questions = _generate_questions(session["user_story"] + "\n" + (additional_context or ""))
    session["generated_questions"] = questions
    return json.dumps({"success": True, "session_id": session_id, "questions": questions,
                       "total_questions": len(questions),
                       "message": "Present these questions to the user one by one."}, indent=2)


@app.tool()
def record_answer(session_id: str, question: str, answer: str) -> str:
    """Record the user's answer to a clarifying question."""
    if session_id not in qa_sessions:
        raise ValueError(f"Session {session_id} not found")
    qa_sessions[session_id]["qa_pairs"].append(
        {"question": question, "answer": answer, "timestamp": datetime.now().isoformat()}
    )
    return json.dumps({"success": True, "session_id": session_id,
                       "total_qa_pairs": len(qa_sessions[session_id]["qa_pairs"]),
                       "message": "Answer recorded."}, indent=2)


@app.tool()
def capture_requirements(
    session_id: str,
    functional_requirements: Optional[List[str]] = None,
    non_functional_requirements: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
) -> str:
    """Generate the final requirements document (markdown). Agent saves it to artifacts/requirements.md."""
    if session_id not in qa_sessions:
        raise ValueError(f"Session {session_id} not found")
    session = qa_sessions[session_id]
    doc = _format_doc(
        session["user_story"], session["source_info"], session["qa_pairs"],
        functional_requirements or [], non_functional_requirements or [],
        constraints or [], acceptance_criteria or []
    )
    session["requirements_content"] = doc
    session["status"] = "completed"
    ref = re.sub(r'[^\w\-_]', '_', session["source_info"].get("reference", "unknown"))
    return json.dumps({"success": True, "session_id": session_id,
                       "requirements_content": doc, "suggested_filename": f"requirements_{ref}.md",
                       "message": "Requirements generated. Save to artifacts/requirements.md."}, indent=2)


@app.tool()
def get_session_status(session_id: str) -> str:
    """Get the status of a requirements gathering session."""
    if session_id not in qa_sessions:
        raise ValueError(f"Session {session_id} not found")
    s = qa_sessions[session_id]
    return json.dumps({"success": True, "session_id": session_id, "status": s["status"],
                       "created_at": s["created_at"], "source_type": s["source_info"]["source_type"],
                       "qa_pairs_count": len(s["qa_pairs"]),
                       "requirements_generated": "requirements_content" in s}, indent=2)


@app.tool()
def list_active_sessions() -> str:
    """List all active requirements gathering sessions."""
    sessions_list = [
        {"session_id": sid, "status": s["status"], "source_type": s["source_info"]["source_type"],
         "created_at": s["created_at"], "qa_pairs_count": len(s["qa_pairs"])}
        for sid, s in qa_sessions.items()
    ]
    return json.dumps({"success": True, "total_sessions": len(sessions_list), "sessions": sessions_list}, indent=2)


@app.tool()
def create_jira_story(
    summary: str,
    description: str,
    project_key: Optional[str] = None,
) -> str:
    """Create a new Story in JIRA (default project: EPMCDMETST). Call after reading the user story."""
    result = _create_jira_story(summary, description, project_key)
    return json.dumps({"success": True, "jira_key": result["key"], "jira_id": result["id"],
                       "url": result["url"], "project": result["project"],
                       "message": f"JIRA story created: {result['key']}  -  {result['url']}"}, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run_stdio_async())
