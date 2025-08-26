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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx

GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

if not GITHUB_OWNER or not GITHUB_REPO:
    raise SystemExit("Missing GITHUB_OWNER or GITHUB_REPO")
if not GITHUB_TOKEN:
    raise SystemExit("Missing GITHUB_TOKEN")

app = FastAPI(title="Amara GitHub MCP Adapter", version="0.1.0")

# ---------- Schemas ----------
class ListIssuesParams(BaseModel):
    state: t.Literal["open", "closed", "all"] = "open"
    labels: t.Optional[str] = None
    per_page: int = 20

class CreateIssueParams(BaseModel):
    title: str
    body: t.Optional[str] = None
    labels: t.Optional[t.List[str]] = None

class CommentIssueParams(BaseModel):
    issue_number: int
    body: str

class ListPRsParams(BaseModel):
    state: t.Literal["open", "closed", "all"] = "open"
    per_page: int = 20

# ---------- Helpers ----------
def gh_url(path: str) -> str:
    return f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}{path}"

# ---------- Endpoints ----------
@app.get("/health")
async def health():
    return {"ok": True, "repo": f"{GITHUB_OWNER}/{GITHUB_REPO}"}

@app.post("/tools/listIssues")
async def list_issues(p: ListIssuesParams):
    params = {"state": p.state, "per_page": p.per_page}
    if p.labels:
        params["labels"] = p.labels
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        r = await client.get(gh_url("/issues"), params=params)
        r.raise_for_status()
        return r.json()

@app.post("/tools/createIssue")
async def create_issue(p: CreateIssueParams):
    data = {"title": p.title}
    if p.body:
        data["body"] = p.body
    if p.labels:
        data["labels"] = ",".join(p.labels)
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        r = await client.post(gh_url("/issues"), json=data)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

@app.post("/tools/commentIssue")
async def comment_issue(p: CommentIssueParams):
    data = {"body": p.body}
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        r = await client.post(gh_url(f"/issues/{p.issue_number}/comments"), json=data)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

@app.post("/tools/listPulls")
async def list_pulls(p: ListPRsParams):
    params = {"state": p.state, "per_page": p.per_page}
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        r = await client.get(gh_url("/pulls"), params=params)
        r.raise_for_status()
        return r.json()
