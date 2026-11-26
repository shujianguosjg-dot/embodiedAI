#!/usr/bin/env python3
"""Collect a daily source bundle for the embodied-AI / computer-vision paper brief.

This script gathers evidence; it does not pretend to rank scientific quality.
ChatGPT reads the resulting bundle and writes the human-facing analysis.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TZ = ZoneInfo("Asia/Taipei")
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "paper-digests"
HEADERS = {"User-Agent": "EmbodiedAIPaperDigest/1.0 (research digest; contact repository owner)"}

KEYWORDS = [
    "vision-language-action", "vision language action", "robot learning",
    "robot manipulation", "robotic manipulation", "embodied ai", "embodied intelligence",
    "imitation learning", "dexterous manipulation", "dexterous hand", "robot hand",
    "grasping", "visuomotor", "diffusion policy", "action chunking", "world model",
    "robot foundation model", "human-to-robot", "egocentric", "first-person",
    "3d reconstruction", "stereo matching", "multi-view", "multi view geometry",
    "novel view synthesis", "point cloud", "visual slam", "rgb-d", "depth estimation",
    "3d perception", "3d vision", "visual perception", "gaussian splatting",
    "neural radiance field", "nerf", "spatial intelligence", "scene understanding",
]
CATEGORIES = ["cs.RO", "cs.CV", "cs.LG"]
ID_RE = re.compile(r"(\d{4}\.\d{4,5})")


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=4, connect=4, read=4, backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update(HEADERS)
    return s


HTTP = session()


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def arxiv_id(value: str) -> str | None:
    match = ID_RE.search(value or "")
    return match.group(1) if match else None


def relevance(title: str, abstract: str, category: str) -> int:
    t, a = title.lower(), abstract.lower()
    score = 0
    for phrase in KEYWORDS:
        if phrase in t:
            score += 5
        elif phrase in a:
            score += 1
    if category == "cs.RO":
        score += 2
    if any(x in t for x in ("robot", "vla", "manipulation", "stereo", "reconstruction")):
        score += 2
    return score


def parse_feed(xml_text: str, requested_category: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    rows = []
    for entry in root.findall(f"{ATOM}entry"):
        abs_url = clean(entry.findtext(f"{ATOM}id"))
        pid = arxiv_id(abs_url)
        if not pid:
            continue
        title = clean(entry.findtext(f"{ATOM}title"))
        abstract = clean(entry.findtext(f"{ATOM}summary"))
        published = clean(entry.findtext(f"{ATOM}published"))
        updated = clean(entry.findtext(f"{ATOM}updated"))
        authors, affiliations = [], []
        for author in entry.findall(f"{ATOM}author"):
            name = clean(author.findtext(f"{ATOM}name"))
            if name:
                authors.append(name)
            aff = clean(author.findtext(f"{ARXIV}affiliation"))
            if aff and aff not in affiliations:
                affiliations.append(aff)
        cats = [x.attrib.get("term", "") for x in entry.findall(f"{ATOM}category")]
        primary = entry.find(f"{ARXIV}primary_category")
        category = primary.attrib.get("term", requested_category) if primary is not None else requested_category
        rows.append({
            "arxiv_id": pid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "affiliations_from_arxiv_metadata": affiliations,
            "published": published,
            "updated": updated,
            "categories": cats,
            "primary_category": category,
            "arxiv_url": f"https://arxiv.org/abs/{pid}",
            "html_url": f"https://arxiv.org/html/{pid}",
        })
    return rows


def fetch_category(category: str, start_date: str, end_date: str) -> tuple[str, list[dict], str]:
    params = {
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": 1000,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }
    try:
        response = HTTP.get("https://export.arxiv.org/api/query", params=params, timeout=(15, 90))
        response.raise_for_status()
        rows = parse_feed(response.text, category)
        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
        rows = [
            r for r in rows
            if r["updated"] and start_dt <= datetime.fromisoformat(r["updated"].replace("Z", "+00:00")) < end_dt
        ]
        return category, rows, f"ok: {len(rows)} recent/updated records"
    except Exception as exc:
        return category, [], f"error: {type(exc).__name__}: {exc}"


def fetch_hf_signals(days: int) -> tuple[dict, str]:
    signals: dict[str, dict] = {}
    errors = []
    today = datetime.now(TZ).date()
    for offset in range(days):
        date_str = (today - timedelta(days=offset)).isoformat()
        try:
            response = HTTP.get(
                "https://huggingface.co/api/daily_papers",
                params={"p": 0, "limit": 100, "date": date_str, "sort": "trending"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            for item in data if isinstance(data, list) else []:
                paper = item.get("paper") if isinstance(item, dict) else {}
                paper = paper if isinstance(paper, dict) else {}
                pid = arxiv_id(str(paper.get("id") or item.get("id") or item.get("paperId") or ""))
                if not pid:
                    continue
                signals[pid] = {
                    "date": date_str,
                    "upvotes": item.get("numUpvotes", item.get("upvotes", paper.get("upvotes"))),
                    "comments": item.get("numComments", item.get("comments", paper.get("numComments"))),
                    "hf_url": f"https://huggingface.co/papers/{pid}",
                    "title": paper.get("title") or item.get("title"),
                }
        except Exception as exc:
            errors.append(f"{date_str}: {type(exc).__name__}: {exc}")
    status = f"ok: {len(signals)} papers with HF daily-paper signals"
    if errors:
        status += f"; {len(errors)} date request(s) failed: " + " | ".join(errors[:3])
    return signals, status


def fetch_github_signals(pid: str) -> list[dict]:
    headers = dict(HEADERS)
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = HTTP.get(
            "https://api.github.com/search/repositories",
            params={"q": f'"{pid}" in:readme', "sort": "updated", "order": "desc", "per_page": 5},
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()
        return [
            {
                "name": x.get("full_name"),
                "url": x.get("html_url"),
                "description": x.get("description"),
                "stars": x.get("stargazers_count"),
                "updated_at": x.get("updated_at"),
            }
            for x in response.json().get("items", [])
        ]
    except Exception as exc:
        return [{"lookup_error": f"{type(exc).__name__}: {exc}"}]


def fetch_full_text(pid: str) -> tuple[str, str]:
    for url in (f"https://arxiv.org/html/{pid}", f"https://ar5iv.labs.arxiv.org/html/{pid}"):
        try:
            response = HTTP.get(url, timeout=(15, 60))
            if response.status_code != 200 or len(response.text) < 1000:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()
            text = clean(soup.get_text(" ", strip=True))
            if len(text) > 1000:
                return text[:36000], url
        except Exception:
            continue
    return "", ""


def resolve_llm_chat_completions_url(base_url: str) -> str:
    """Resolve legacy and current OpenCode Go base URLs to the documented endpoint."""
    base_url = base_url.strip().rstrip("/")
    if base_url.startswith("https://opencode.ai/zen/go"):
        # Migrate the legacy URL used by the first version of this workflow.
        return "https://opencode.ai/inference/go/openai/v1/chat/completions"
    if base_url == "https://opencode.ai/inference/go":
        return "https://opencode.ai/inference/go/openai/v1/chat/completions"
    if base_url.endswith("/inference/go/openai/v1"):
        return f"{base_url}/chat/completions"
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def stable_opencode_session_id(arxiv_pid: str) -> str:
    """Return a stable, non-secret OpenCode session ID for this paper's analysis."""
    digest = hashlib.sha256(
        f"embodied-ai-paper-digest:{arxiv_pid}".encode("utf-8")
    ).hexdigest()[:32]
    return f"ses_{digest}"


def describe_llm_http_error(response: requests.Response) -> str:
    """Keep useful API diagnostics without ever logging request credentials."""
    try:
        body = response.json()
    except ValueError:
        body = response.text
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            body = error.get("message") or error.get("type") or body
        elif isinstance(error, str):
            body = error
        else:
            body = body.get("message") or body
    detail = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    detail = clean(detail)[:1200] or response.reason or "no response body"
    request_id = (
        response.headers.get("x-request-id")
        or response.headers.get("request-id")
        or response.headers.get("cf-ray")
    )
    suffix = f"; request_id={request_id}" if request_id else ""
    return f"error: HTTP {response.status_code}: {detail}{suffix}"


def extract_chat_text(message: dict) -> str:
    """Extract only user-visible assistant text; never expose reasoning_content."""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
        return "\\n".join(chunks).strip()
    return ""


def chat_response_diagnostic(result: dict, message: dict | None) -> str:
    choices = result.get("choices") or []
    choice = choices[0] if choices and isinstance(choices[0], dict) else {}
    usage = result.get("usage") or {}
    usage_summary = {
        key: usage.get(key)
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        if key in usage
    }
    message = message if isinstance(message, dict) else {}
    return (
        "empty assistant content"
        f"; finish_reason={choice.get('finish_reason')}"
        f"; message_keys={sorted(message.keys())}"
        f"; reasoning_content_present={bool(message.get('reasoning_content'))}"
        f"; tool_calls={len(message.get('tool_calls') or [])}"
        f"; usage={json.dumps(usage_summary, ensure_ascii=False)}"
    )


def call_chat_completion(
    *,
    endpoint: str,
    api_key: str,
    model: str,
    messages: list[dict],
    session_id: str,
    max_tokens: int,
) -> tuple[str | None, str]:
    payload = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "stream": False,
        "messages": messages,
    }
    try:
        response = HTTP.post(
            endpoint,
            headers={
                **HEADERS,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "x-opencode-session": session_id,
            },
            json=payload,
            timeout=(20, 180),
        )
        response.raise_for_status()
        result = response.json()
        choices = result.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            return None, f"error: invalid chat-completions response; top_level_keys={sorted(result.keys())}"
        message = choices[0].get("message")
        if not isinstance(message, dict):
            return None, f"error: missing assistant message; choice_keys={sorted(choices[0].keys())}"
        content = extract_chat_text(message)
        if not content:
            return None, f"error: {chat_response_diagnostic(result, message)}"
        return content, "ok"
    except requests.HTTPError as exc:
        if exc.response is not None:
            return None, describe_llm_http_error(exc.response)
        return None, f"error: HTTP request failed: {exc}"
    except Exception as exc:
        return None, f"error: {type(exc).__name__}: {exc}"


def probe_llm() -> tuple[str | None, str]:
    """One cheap end-to-end probe before spending tokens on paper analysis."""
    base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    if not (base_url and api_key and model):
        return None, "not configured"
    endpoint = resolve_llm_chat_completions_url(base_url)
    return call_chat_completion(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        messages=[
            {"role": "system", "content": "你是一个简短的连通性测试助手。"},
            {"role": "user", "content": "请只回复：API测试成功。"},
        ],
        session_id=stable_opencode_session_id("daily-digest-preflight"),
        max_tokens=128,
    )


def summarize_with_llm(row: dict, full_text: str) -> tuple[str | None, str]:
    base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    if not (base_url and api_key and model):
        return None, "not configured; only metadata/abstract collected"
    prompt = (
        "请作为严谨的论文技术分析员，仅依据提供的论文元数据、摘要和正文摘录，生成中文结构化分析。"
        "依次说明：1)研究问题与任务设定；2)方法模块、信息流和关键机制；"
        "3)训练数据、监督信号与损失（正文未提供则明确写未披露/摘录未覆盖）；"
        "4)实验数据集、指标、基线和定量结果（没有明确数字就不要编造）；"
        "5)优势、局限与复现所需资源。"
        "区分作者声称与正文中可直接核对的证据；不得补写论文未提供的信息。"
        "控制在 500–800 个中文字符。"
    )
    endpoint = resolve_llm_chat_completions_url(base_url)
    return call_chat_completion(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        messages=[
            {"role": "system", "content": "你是谨慎的学术论文分析员，禁止臆测或编造实验细节。"},
            {"role": "user", "content": (
                f"{prompt}\\n\\n论文 ID：{row['arxiv_id']}\\n标题：{row['title']}\\n"
                f"作者：{', '.join(row.get('authors', []))}\\n摘要：{row['abstract']}\\n"
                f"正文摘录：{full_text}"
            )},
        ],
        session_id=stable_opencode_session_id(row["arxiv_id"]),
        max_tokens=4096,
    )


def main() -> int:
    now = datetime.now(TZ)
    today = now.date()
    start_date = (today - timedelta(days=14)).isoformat()
    end_date = today.isoformat()

    category_rows: dict[str, list[dict]] = {}
    category_status: dict[str, str] = {}
    for i, category in enumerate(CATEGORIES):
        cat, rows, status = fetch_category(category, start_date, end_date)
        category_rows[cat] = rows
        category_status[cat] = status
        if i < len(CATEGORIES) - 1:
            time.sleep(3)

    merged: dict[str, dict] = {}
    for rows in category_rows.values():
        for row in rows:
            merged[row["arxiv_id"]] = row

    candidates = []
    for row in merged.values():
        row["relevance_score"] = relevance(row["title"], row["abstract"], row["primary_category"])
        if row["relevance_score"] >= 3:
            candidates.append(row)
    candidates.sort(
        key=lambda x: (x["relevance_score"], x.get("updated", "")),
        reverse=True,
    )

    hf_signals, hf_status = fetch_hf_signals(14)
    for row in candidates:
        row["huggingface_signal"] = hf_signals.get(row["arxiv_id"])

    github_status = "not attempted"
    for row in candidates[:15]:
        row["github_repositories"] = fetch_github_signals(row["arxiv_id"])
        time.sleep(0.5)
    github_status = "searched for top 15 candidates (or fewer)" if candidates else "no relevant arXiv candidates"

    fulltext_ids = []
    llm_statuses = []
    llm_model = os.getenv("LLM_MODEL") or None
    llm_preflight_response, llm_preflight_status = probe_llm()
    llm_failure = None if llm_preflight_response else llm_preflight_status
    llm_analysis_count = 0
    for row in candidates[:10]:
        full_text, source_url = fetch_full_text(row["arxiv_id"])
        row["full_text_source_url"] = source_url or None
        if full_text:
            fulltext_ids.append(row["arxiv_id"])
            if llm_failure:
                row["technical_analysis"] = None
                row["technical_analysis_status"] = f"skipped after previous API failure: {llm_failure}"
                row["reading_scope"] = "HTML full text fetched; model analysis skipped after API failure"
                llm_statuses.append(row["technical_analysis_status"])
                continue
            if llm_analysis_count >= 5:
                row["technical_analysis"] = None
                row["technical_analysis_status"] = "skipped: daily analysis cap reached (5)"
                row["reading_scope"] = "HTML full text fetched; model analysis cap reached"
                llm_statuses.append(row["technical_analysis_status"])
                continue
            summary, summary_status = summarize_with_llm(row, full_text)
            if not summary:
                llm_failure = summary_status
            else:
                llm_analysis_count += 1
            row["technical_analysis"] = summary
            row["technical_analysis_status"] = summary_status
            row["reading_scope"] = "HTML full text fetched; concise model analysis stored" if summary else "HTML full text fetched but no analysis stored"
            llm_statuses.append(summary_status)
        else:
            row["technical_analysis"] = None
            row["technical_analysis_status"] = "no HTML full text available"
            row["reading_scope"] = "abstract and metadata only"
        time.sleep(1)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    recent_72h = []
    for row in candidates:
        stamp = row.get("updated") or row.get("published")
        if stamp:
            try:
                if datetime.fromisoformat(stamp.replace("Z", "+00:00")) >= cutoff:
                    recent_72h.append(row["arxiv_id"])
            except ValueError:
                pass

    payload = {
        "schema_version": 1,
        "report_date_local": today.isoformat(),
        "generated_at_local": now.isoformat(),
        "timezone": "Asia/Taipei",
        "search_window_days": 14,
        "preferred_window_hours": 72,
        "source_status": {
            "arxiv_by_category": category_status,
            "huggingface_daily_papers": hf_status,
            "github_repository_search": github_status,
            "html_full_text_ids": fulltext_ids,
            "llm_analysis_model": llm_model,
            "llm_analysis_endpoint": resolve_llm_chat_completions_url(os.getenv("LLM_BASE_URL", "")) if os.getenv("LLM_BASE_URL") else None,
            "llm_analysis_configured": bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL")),
            "llm_preflight_status": llm_preflight_status,
            "llm_analysis_success_count": llm_analysis_count,
            "llm_analysis_statuses": llm_statuses,
        },
        "counts": {
            "arxiv_records_after_window_filter": len(merged),
            "relevant_candidates": len(candidates),
            "candidates_updated_in_last_72h": len(recent_72h),
        },
        "selection_note": (
            "This is an evidence bundle, not a quality ranking. Select 1-5 papers only after "
            "checking scientific contribution, evidence, author affiliations, and community signals. "
            "Do not treat popularity or institutional prestige as proof of quality."
        ),
        "candidates": candidates[:20],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (OUT / f"{today.isoformat()}.json").write_text(text, encoding="utf-8")
    (OUT / "latest.json").write_text(text, encoding="utf-8")
    print(json.dumps(payload["source_status"], ensure_ascii=False, indent=2))
    print(f"Saved {min(len(candidates), 20)} candidates to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
