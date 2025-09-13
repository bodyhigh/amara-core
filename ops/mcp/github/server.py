#!/usr/bin/env python3
# --- Amara Script Metadata ---
# Repo: amara-core
# Role: GitHub MCP adapter server
# Owner: core
# Secrets: none
# Notes: Used by pre-commit (validate-amara-script-headers)
# --------------------------------

import os
import typing as t
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx

# --- Env & constants ---
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_OWNER or not GITHUB_REPO:
    raise SystemExit("Missing GITHUB_OWNER or GITHUB_REPO")
if not GITHUB_TOKEN:
    raise SystemExit("Missing GITHUB_TOKEN")

UA = "amara-core-mcp/0.1 (+https://github.com/bodyhigh/amara-core)"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": UA,
}

def gh_url(path: str) -> str:
    return f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}{path}"

async def _gh_get(url: str, *, params: dict | None = None):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=HEADERS, params=params)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

async def _gh_post(url: str, *, json: dict):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=HEADERS, json=json)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

app = FastAPI(title="Amara GitHub MCP Adapter", version="0.1.1")

# ---------- Schemas ----------
class ListIssuesParams(BaseModel):
    state: t.Literal["open", "closed", "all"] = "open"
    labels: t.Optional[str] = None
    per_page: int = 20
    page: int = 1

class CreateIssueParams(BaseModel):
    title: str
    body: t.Optional[str] = None
    labels: t.Optional[t.List[str]] = None  # GitHub expects a list

class CommentIssueParams(BaseModel):
    issue_number: int
    body: str

class ListPRsParams(BaseModel):
    state: t.Literal["open", "closed", "all"] = "open"
    per_page: int = 20
    page: int = 1

# ---------- Endpoints ----------
@app.get("/health")
async def health():
    return {"ok": True, "repo": f"{GITHUB_OWNER}/{GITHUB_REPO}"}

@app.get("/contents")
async def list_contents(
    path: str = Query("", description="Path within the repo (default root)"),
    ref: t.Optional[str] = Query(None, description="Git ref/branch/sha (optional)"),
):
    """
    List contents at `path` in the configured {OWNER}/{REPO}.
    Mirrors GET /repos/{owner}/{repo}/contents[/path]?ref=<ref>
    """
    url_path = f"/contents/{path}".rstrip("/")
    params = {"ref": ref} if ref else None
    return await _gh_get(gh_url(url_path), params=params)

@app.post("/tools/listIssues")
async def list_issues(p: ListIssuesParams):
    params = {"state": p.state, "per_page": p.per_page, "page": p.page}
    if p.labels:
        params["labels"] = p.labels
    return await _gh_get(gh_url("/issues"), params=params)

@app.post("/tools/createIssue")
async def create_issue(p: CreateIssueParams):
    data: dict = {"title": p.title}
    if p.body:
        data["body"] = p.body
    if p.labels:
        # GitHub expects an array of label names
        data["labels"] = p.labels
    return await _gh_post(gh_url("/issues"), json=data)

@app.post("/tools/commentIssue")
async def comment_issue(p: CommentIssueParams):
    data = {"body": p.body}
    return await _gh_post(gh_url(f"/issues/{p.issue_number}/comments"), json=data)

@app.post("/tools/listPulls")
async def list_pulls(p: ListPRsParams):
    params = {"state": p.state, "per_page": p.per_page, "page": p.page}
    return await _gh_get(gh_url("/pulls"), params=params)
