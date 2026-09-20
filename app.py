"""
Next-Generation 3D WebGL Streamlit Workbench
Primary entrypoint: app.py

Designed for deployment on Streamlit / Hugging Face Spaces.

Optional packages:
  streamlit
  pyyaml
  pypdf
  google-genai
  openai
  anthropic

The application is intentionally resilient: optional integrations degrade gracefully,
while the deterministic workspace, editors, artifact lifecycle, and 2D fallbacks
remain usable without an AI provider.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import html
import io
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components


# =============================================================================
# App configuration
# =============================================================================

APP_TITLE = "3D WebGL Workbench"
APP_VERSION = "1.0.0"

DEFAULT_MODEL = "gemini-3.1-flash-lite"

MODELS = {
    "gemini-3.1-flash-lite": {
        "provider": "Gemini",
        "label": "Gemini 3.1 Flash Lite",
        "speed": "Fast",
        "purpose": "General workbench default",
    },
    "gemini-3.5-flash-lite": {
        "provider": "Gemini",
        "label": "Gemini 3.5 Flash Lite",
        "speed": "Fast",
        "purpose": "Longer reasoning / synthesis",
    },
    "gemma-4-31b-it": {
        "provider": "Gemini",
        "label": "Gemma 4 31B IT",
        "speed": "Balanced",
        "purpose": "Instruction-oriented local/provider deployment",
    },
    "gemma-4-26b-14b-it": {
        "provider": "Gemini",
        "label": "Gemma 4 26B/14B IT",
        "speed": "Balanced",
        "purpose": "Efficient structured tasks",
    },
}

PROVIDERS = {
    "Gemini": {
        "env": "GEMINI_API_KEY",
        "session_key": "gemini_api_key",
    },
    "OpenAI": {
        "env": "OPENAI_API_KEY",
        "session_key": "openai_api_key",
    },
    "Anthropic": {
        "env": "ANTHROPIC_API_KEY",
        "session_key": "anthropic_api_key",
    },
}

LANGUAGES = {
    "繁體中文": "zh-TW",
    "English": "en",
    "日本語": "ja",
}

THEMES = {
    "Light": {
        "bg": "#F7F8FA",
        "panel": "#FFFFFF",
        "text": "#15202B",
        "muted": "#687386",
        "accent": "#6C5CE7",
        "accent2": "#00A6A6",
        "border": "#DDE2EA",
        "success": "#178B61",
        "warning": "#C98200",
        "danger": "#C24141",
        "coral": "#FF6F61",
        "canvas": "#EEF1F7",
    },
    "Dark": {
        "bg": "#0C1017",
        "panel": "#131A24",
        "text": "#EEF3F8",
        "muted": "#9BA9B9",
        "accent": "#9A8CFF",
        "accent2": "#25D0C4",
        "border": "#273241",
        "success": "#49C58D",
        "warning": "#F3B34D",
        "danger": "#FF7474",
        "coral": "#FF7B70",
        "canvas": "#101722",
    },
    "System": {
        "bg": "#F7F8FA",
        "panel": "#FFFFFF",
        "text": "#15202B",
        "muted": "#687386",
        "accent": "#6C5CE7",
        "accent2": "#00A6A6",
        "border": "#DDE2EA",
        "success": "#178B61",
        "warning": "#C98200",
        "danger": "#C24141",
        "coral": "#FF6F61",
        "canvas": "#EEF1F7",
    },
    "Jackpot — Aurora": {
        "bg": "#07131A", "panel": "#0D202A", "text": "#F2FBFF",
        "muted": "#9FC0C8", "accent": "#4CE1D2", "accent2": "#65B6FF",
        "border": "#1E3C47", "success": "#5EE6A8", "warning": "#FFD166",
        "danger": "#FF6B6B", "coral": "#FF7A70", "canvas": "#0B1C24",
    },
    "Jackpot — Coral": {
        "bg": "#1A0B0B", "panel": "#291313", "text": "#FFF7F5",
        "muted": "#D3A9A4", "accent": "#FF6F61", "accent2": "#FFC2BA",
        "border": "#4B2321", "success": "#75D69F", "warning": "#F9C74F",
        "danger": "#FF5252", "coral": "#FF8C7D", "canvas": "#211010",
    },
    "Jackpot — Orchid": {
        "bg": "#120B1B", "panel": "#20132E", "text": "#FCF7FF",
        "muted": "#C4A8D2", "accent": "#C084FC", "accent2": "#F0ABFC",
        "border": "#3B2451", "success": "#6EE7B7", "warning": "#FDE68A",
        "danger": "#FB7185", "coral": "#FB7185", "canvas": "#180F24",
    },
    "Jackpot — Ocean": {
        "bg": "#06131E", "panel": "#0A2231", "text": "#F2FBFF",
        "muted": "#9DBBC9", "accent": "#38BDF8", "accent2": "#22D3EE",
        "border": "#18445B", "success": "#4ADE80", "warning": "#FBBF24",
        "danger": "#FB7185", "coral": "#FB7185", "canvas": "#081B29",
    },
    "Jackpot — Mint": {
        "bg": "#071512", "panel": "#0D231D", "text": "#F2FFF9",
        "muted": "#9FC8BA", "accent": "#34D399", "accent2": "#5EEAD4",
        "border": "#1D4639", "success": "#6EE7B7", "warning": "#FACC15",
        "danger": "#FB7185", "coral": "#FB7185", "canvas": "#091C17",
    },
    "Jackpot — Sunset": {
        "bg": "#1A0E08", "panel": "#2B180F", "text": "#FFF8F0",
        "muted": "#D2B29B", "accent": "#FB923C", "accent2": "#FACC15",
        "border": "#51301D", "success": "#86EFAC", "warning": "#FDE047",
        "danger": "#FB7185", "coral": "#FF8066", "canvas": "#211109",
    },
    "Jackpot — Sapphire": {
        "bg": "#070B1D", "panel": "#10183A", "text": "#F5F7FF",
        "muted": "#A7B1D6", "accent": "#818CF8", "accent2": "#60A5FA",
        "border": "#252F62", "success": "#34D399", "warning": "#FBBF24",
        "danger": "#FB7185", "coral": "#FF7A70", "canvas": "#0B1028",
    },
    "Jackpot — Citrus": {
        "bg": "#111407", "panel": "#1E240B", "text": "#FCFFE9",
        "muted": "#BFC994", "accent": "#A3E635", "accent2": "#FDE047",
        "border": "#394619", "success": "#4ADE80", "warning": "#FACC15",
        "danger": "#FB7185", "coral": "#FF8066", "canvas": "#151A08",
    },
    "Jackpot — Rose": {
        "bg": "#180A12", "panel": "#29111E", "text": "#FFF6FB",
        "muted": "#D0A7BA", "accent": "#F472B6", "accent2": "#FB7185",
        "border": "#4A2136", "success": "#6EE7B7", "warning": "#FDE68A",
        "danger": "#FB7185", "coral": "#FF8066", "canvas": "#210D18",
    },
    "Jackpot — Platinum": {
        "bg": "#111316", "panel": "#1C2025", "text": "#F7F8FA",
        "muted": "#A8AFB8", "accent": "#D1D5DB", "accent2": "#94A3B8",
        "border": "#343A43", "success": "#86EFAC", "warning": "#FDE68A",
        "danger": "#FDA4AF", "coral": "#FF8066", "canvas": "#15181C",
    },
}

TEXT = {
    "zh-TW": {
        "home": "工作台",
        "notes": "AI 筆記管家",
        "review": "法規審查台",
        "skills": "Skill Studio",
        "pipeline": "Pipeline Studio",
        "agents": "Agent Studio",
        "results": "成果庫",
        "visuals": "3D 視覺中心",
        "settings": "設定與安全",
        "new": "新增",
        "save": "儲存",
        "run": "執行",
        "export": "匯出",
        "upload": "上傳",
        "download": "下載",
        "ready": "就緒",
        "running": "執行中",
        "error": "錯誤",
        "success": "完成",
        "default": "預設",
    },
    "en": {
        "home": "Workbench",
        "notes": "AI Note Keeper",
        "review": "Review Bench",
        "skills": "Skill Studio",
        "pipeline": "Pipeline Studio",
        "agents": "Agent Studio",
        "results": "Results Library",
        "visuals": "3D Visualization",
        "settings": "Settings & Security",
        "new": "New",
        "save": "Save",
        "run": "Run",
        "export": "Export",
        "upload": "Upload",
        "download": "Download",
        "ready": "Ready",
        "running": "Running",
        "error": "Error",
        "success": "Complete",
        "default": "Default",
    },
    "ja": {
        "home": "ワークベンチ",
        "notes": "AI ノートキーパー",
        "review": "レビュー・ベンチ",
        "skills": "Skill Studio",
        "pipeline": "Pipeline Studio",
        "agents": "Agent Studio",
        "results": "成果物ライブラリ",
        "visuals": "3D ビジュアル",
        "settings": "設定とセキュリティ",
        "new": "新規",
        "save": "保存",
        "run": "実行",
        "export": "エクスポート",
        "upload": "アップロード",
        "download": "ダウンロード",
        "ready": "準備完了",
        "running": "実行中",
        "error": "エラー",
        "success": "完了",
        "default": "デフォルト",
    },
}


# =============================================================================
# Utility helpers
# =============================================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def uid(prefix: str = "asset") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def short_id(value: str) -> str:
    return value[:12] if value else ""


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def safe_text(value: Any) -> str:
    return "" if value is None else str(value)


def t(key: str) -> str:
    lang = st.session_state.get("language", "zh-TW")
    return TEXT.get(lang, TEXT["zh-TW"]).get(key, key)


def theme_tokens() -> Dict[str, str]:
    name = st.session_state.get("theme", "System")
    return THEMES.get(name, THEMES["System"])


def add_log(message: str, level: str = "INFO", source: str = "system") -> None:
    event = {
        "id": uid("evt"),
        "time": now_iso(),
        "level": level.upper(),
        "source": source,
        "message": message,
    }
    st.session_state.setdefault("logs", []).append(event)
    st.session_state["logs"] = st.session_state["logs"][-250:]


def set_flash(message: str, level: str = "success") -> None:
    st.session_state["flash"] = {"message": message, "level": level}


def clear_flash() -> None:
    st.session_state.pop("flash", None)


def provider_key_status(provider: str) -> Dict[str, Any]:
    cfg = PROVIDERS[provider]
    env_present = bool(os.getenv(cfg["env"], "").strip())
    session_present = bool(st.session_state.get(cfg["session_key"], "").strip())
    return {
        "environment": env_present,
        "session": session_present,
        "configured": env_present or session_present,
        "source": "environment" if env_present else ("session" if session_present else None),
    }


def get_provider_key(provider: str) -> Optional[str]:
    cfg = PROVIDERS[provider]
    env_key = os.getenv(cfg["env"], "").strip()
    if env_key:
        return env_key
    session_key = st.session_state.get(cfg["session_key"], "").strip()
    return session_key or None


def model_provider(model: str) -> str:
    return MODELS.get(model, {}).get("provider", "Gemini")


def artifact_count(kind: Optional[str] = None) -> int:
    results = st.session_state.get("artifacts", [])
    if kind is None:
        return len(results)
    return sum(1 for item in results if item.get("kind") == kind)


# =============================================================================
# Session state
# =============================================================================

def default_skill(name: str = "Regulatory Evidence Review") -> Dict[str, Any]:
    return {
        "id": uid("skill"),
        "name": name,
        "description": "Evidence-first review and structured regulatory analysis.",
        "version": "1.0.0",
        "system": (
            "You are an evidence-first professional reviewer. "
            "Separate source facts, inferred observations, and unresolved questions. "
            "Never invent evidence."
        ),
        "instructions": (
            "1. Identify claims.\n"
            "2. Link each claim to available evidence.\n"
            "3. Flag contradictions.\n"
            "4. Produce concise, traceable findings."
        ),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }


def default_pipeline() -> Dict[str, Any]:
    return {
        "id": uid("pipe"),
        "name": "Evidence Review Pipeline",
        "description": "Parse → extract → compare → review → export",
        "version": "1.0.0",
        "nodes": [
            {"id": "n1", "label": "Input", "type": "input", "status": "idle"},
            {"id": "n2", "label": "Parse", "type": "parse", "status": "idle"},
            {"id": "n3", "label": "Extract", "type": "extract", "status": "idle"},
            {"id": "n4", "label": "Compare", "type": "compare", "status": "idle"},
            {"id": "n5", "label": "Review", "type": "review", "status": "idle"},
            {"id": "n6", "label": "Export", "type": "export", "status": "idle"},
        ],
        "edges": [
            ["n1", "n2"],
            ["n2", "n3"],
            ["n3", "n4"],
            ["n4", "n5"],
            ["n5", "n6"],
        ],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }


def init_state() -> None:
    defaults = {
        "initialized": True,
        "language": "zh-TW",
        "theme": "Dark",
        "page": "home",
        "reduced_motion": False,
        "dashboard_open": True,
        "logs": [],
        "flash": None,
        "global_model": DEFAULT_MODEL,
        "module_models": {},
        "active_provider": "Gemini",
        "gemini_api_key": "",
        "openai_api_key": "",
        "anthropic_api_key": "",
        "notes": [],
        "current_note_id": None,
        "note_highlights": [],
        "review": {
            "case_name": "",
            "files": [],
            "claims": [],
            "conflicts": [],
            "draft": "",
            "final": "",
            "questions": [],
        },
        "skills": [default_skill()],
        "current_skill_id": None,
        "comparison": {
            "input": "",
            "skill_a": None,
            "skill_b": None,
            "skill_c": None,
            "model_a": DEFAULT_MODEL,
            "model_b": DEFAULT_MODEL,
            "model_c": DEFAULT_MODEL,
            "output_a": "",
            "output_b": "",
            "review_c": "",
            "criteria": "evidence fidelity, completeness, clarity, traceability",
        },
        "pipelines": [default_pipeline()],
        "current_pipeline_id": None,
        "pipeline_run": {},
        "agent_yaml": "",
        "agent_skill_md": "",
        "agent_validation": [],
        "artifacts": [],
        "token_estimate": 0,
        "run_count": 0,
        "startup_logged": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)

    if not st.session_state["startup_logged"]:
        add_log("Workbench initialized.", "INFO", "boot")
        add_log(f"Default model: {DEFAULT_MODEL}", "INFO", "model")
        st.session_state["startup_logged"] = True


# =============================================================================
# Styling
# =============================================================================

def inject_css() -> None:
    c = theme_tokens()
    st.markdown(
        f"""
        <style>
        :root {{
            --wb-bg: {c["bg"]};
            --wb-panel: {c["panel"]};
            --wb-text: {c["text"]};
            --wb-muted: {c["muted"]};
            --wb-accent: {c["accent"]};
            --wb-accent2: {c["accent2"]};
            --wb-border: {c["border"]};
            --wb-success: {c["success"]};
            --wb-warning: {c["warning"]};
            --wb-danger: {c["danger"]};
            --wb-coral: {c["coral"]};
            --wb-canvas: {c["canvas"]};
        }}

        .stApp {{
            background: var(--wb-bg);
            color: var(--wb-text);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        .wb-hero {{
            border: 1px solid var(--wb-border);
            background:
                radial-gradient(circle at 10% 0%, color-mix(in srgb, var(--wb-accent) 18%, transparent), transparent 32%),
                radial-gradient(circle at 90% 20%, color-mix(in srgb, var(--wb-accent2) 15%, transparent), transparent 28%),
                var(--wb-panel);
            border-radius: 24px;
            padding: 28px;
            margin-bottom: 18px;
            box-shadow: 0 18px 60px rgba(0,0,0,.12);
        }}

        .wb-title {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin: 0;
        }}

        .wb-subtitle {{
            color: var(--wb-muted);
            margin-top: 6px;
        }}

        .wb-chip {{
            display: inline-block;
            border: 1px solid var(--wb-border);
            border-radius: 999px;
            padding: 5px 10px;
            margin: 3px;
            color: var(--wb-muted);
            background: color-mix(in srgb, var(--wb-panel) 88%, transparent);
            font-size: .78rem;
        }}

        .wb-card {{
            border: 1px solid var(--wb-border);
            border-radius: 18px;
            padding: 18px;
            background: var(--wb-panel);
            min-height: 120px;
        }}

        .wb-kpi {{
            font-size: 1.65rem;
            font-weight: 800;
        }}

        .wb-muted {{
            color: var(--wb-muted);
        }}

        .wb-status {{
            padding: 8px 12px;
            border-radius: 999px;
            display: inline-block;
            font-size: .8rem;
            border: 1px solid var(--wb-border);
        }}

        .wb-floating {{
            position: fixed;
            right: 18px;
            bottom: 18px;
            width: 360px;
            max-height: 46vh;
            overflow: auto;
            z-index: 9999;
            padding: 14px;
            border: 1px solid var(--wb-border);
            border-radius: 18px;
            background: color-mix(in srgb, var(--wb-panel) 80%, transparent);
            backdrop-filter: blur(16px);
            opacity: .20;
            transition: opacity .18s ease, transform .18s ease;
            box-shadow: 0 18px 60px rgba(0,0,0,.22);
        }}

        .wb-floating:hover {{
            opacity: .96;
            transform: translateY(-2px);
        }}

        .wb-log {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: .72rem;
            line-height: 1.5;
            white-space: pre-wrap;
        }}

        .wb-coral {{
            color: var(--wb-coral);
            font-weight: 700;
        }}

        .wb-section {{
            margin-top: 18px;
            margin-bottom: 10px;
            font-size: 1.25rem;
            font-weight: 750;
        }}

        .stButton > button {{
            border-radius: 12px;
        }}

        .stDownloadButton > button {{
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Artifact helpers
# =============================================================================

def save_artifact(kind: str, name: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
    artifact = {
        "id": uid(kind),
        "kind": kind,
        "name": name,
        "created_at": now_iso(),
        "content": content,
        "metadata": metadata or {},
    }
    st.session_state["artifacts"].insert(0, artifact)
    st.session_state["artifacts"] = st.session_state["artifacts"][:300]
    add_log(f"Artifact saved: {name}", "INFO", "artifact")
    return artifact["id"]


def artifact_bytes(artifact: Dict[str, Any]) -> bytes:
    content = artifact.get("content")
    if isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")
    return safe_text(content).encode("utf-8")


def artifact_download(label: str, artifact: Dict[str, Any], filename: str, mime: str = "text/plain") -> None:
    st.download_button(
        label,
        data=artifact_bytes(artifact),
        file_name=filename,
        mime=mime,
        key=f"download_{artifact['id']}",
    )


# =============================================================================
# AI providers
# =============================================================================

def heuristic_ai(prompt: str, model: str) -> str:
    """
    Deterministic fallback used when no provider is configured.
    It deliberately labels itself as a local/demo synthesis so the UI never
    represents fallback output as a live external-model result.
    """
    text = prompt.strip()
    words = re.findall(r"\S+", text)
    excerpt = " ".join(words[:120])
    return (
        f"【本地備援 / Local fallback — {model}】\n\n"
        "以下結果由工作台的 deterministic fallback 產生，未呼叫外部模型。\n\n"
        "### 摘要\n"
        f"{excerpt[:900]}\n\n"
        "### 可追蹤觀察\n"
        "- 已保留輸入語意的主要片段。\n"
        "- 未加入未出現在輸入中的外部事實。\n"
        "- 建議在設定頁配置模型提供者後重新執行，以取得 AI 生成結果。"
    )


def call_gemini(prompt: str, model: str, api_key: str) -> str:
    try:
        from google import genai  # type: ignore
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        text = getattr(response, "text", None)
        if text:
            return text
        return safe_text(response)
    except Exception as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc


def call_openai(prompt: str, model: str, api_key: str) -> str:
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=model, input=prompt)
        text = getattr(response, "output_text", None)
        if text:
            return text
        return safe_text(response)
    except Exception as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc


def call_anthropic(prompt: str, model: str, api_key: str) -> str:
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = getattr(response, "content", [])
        return "\n".join(
            getattr(part, "text", safe_text(part)) for part in parts
        )
    except Exception as exc:
        raise RuntimeError(f"Anthropic request failed: {exc}") from exc


def execute_ai(
    prompt: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    purpose: str = "general",
) -> str:
    model = model or st.session_state.get("global_model", DEFAULT_MODEL)
    provider = provider or model_provider(model)
    key = get_provider_key(provider)

    st.session_state["run_count"] += 1
    st.session_state["token_estimate"] += max(1, len(prompt) // 4)

    add_log(
        f"AI run started: {purpose} / {provider} / {model}",
        "INFO",
        "ai",
    )

    if not key:
        add_log(
            f"No key configured for {provider}; deterministic fallback used.",
            "WARNING",
            "ai",
        )
        return heuristic_ai(prompt, model)

    try:
        started = time.perf_counter()
        if provider == "Gemini":
            result = call_gemini(prompt, model, key)
        elif provider == "OpenAI":
            result = call_openai(prompt, model, key)
        elif provider == "Anthropic":
            result = call_anthropic(prompt, model, key)
        else:
            result = heuristic_ai(prompt, model)

        elapsed = time.perf_counter() - started
        st.session_state["token_estimate"] += max(1, len(result) // 4)
        add_log(
            f"AI run completed in {elapsed:.2f}s: {purpose}",
            "INFO",
            "ai",
        )
        return result
    except Exception as exc:
        add_log(str(exc), "ERROR", "ai")
        raise


# =============================================================================
# File extraction
# =============================================================================

def extract_uploaded_file(uploaded) -> Tuple[str, Dict[str, Any]]:
    name = uploaded.name
    raw = uploaded.getvalue()
    metadata = {
        "filename": name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mime": getattr(uploaded, "type", None),
    }

    lower = name.lower()
    if lower.endswith((".txt", ".md", ".markdown", ".csv", ".json", ".yaml", ".yml")):
        try:
            return raw.decode("utf-8"), metadata
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace"), metadata

    if lower.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(io.BytesIO(raw))
            pages = []
            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append(f"## Page {idx}\n\n{page_text}")
            metadata["pages"] = len(pages)
            return "\n\n".join(pages), metadata
        except Exception as exc:
            metadata["extraction_error"] = str(exc)
            return (
                f"# PDF import\n\nUnable to extract text automatically.\n\n"
                f"File: {name}\nBytes: {len(raw)}"
            ), metadata

    return (
        f"# Imported file\n\nFilename: {name}\n\n"
        "Binary or unsupported file type. The asset is preserved for downstream handling."
    ), metadata


# =============================================================================
# WebGL visualizations
# =============================================================================

def webgl_scene(
    title: str,
    nodes: List[Dict[str, Any]],
    edges: List[Tuple[str, str]],
    height: int = 470,
    scene_type: str = "graph",
) -> None:
    c = theme_tokens()
    payload = json.dumps(
        {
            "title": title,
            "nodes": nodes,
            "edges": edges,
            "scene_type": scene_type,
            "accent": c["accent"],
            "accent2": c["accent2"],
            "coral": c["coral"],
            "bg": c["canvas"],
        },
        ensure_ascii=False,
    )

    html_doc = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <style>
        html, body {{
          margin: 0;
          width: 100%;
          height: 100%;
          overflow: hidden;
          background: {c["canvas"]};
          font-family: Inter, system-ui, sans-serif;
        }}
        #hud {{
          position: absolute;
          left: 14px;
          top: 12px;
          color: {c["text"]};
          z-index: 10;
          pointer-events: none;
        }}
        #title {{
          font-size: 16px;
          font-weight: 800;
        }}
        #hint {{
          font-size: 11px;
          color: {c["muted"]};
          margin-top: 4px;
        }}
        canvas {{ display:block; }}
        #fallback {{
          padding: 20px;
          color: {c["text"]};
          font-size: 13px;
        }}
      </style>
    </head>
    <body>
      <div id="hud">
        <div id="title">{html.escape(title)}</div>
        <div id="hint">Drag to orbit · Scroll to zoom · Click a node</div>
      </div>
      <div id="fallback"></div>
      <script>
        const payload = {payload};

        function fallback() {{
          const f = document.getElementById("fallback");
          f.innerHTML =
            "<strong>2D fallback</strong><br><br>" +
            payload.nodes.map(n => "• " + (n.label || n.id)).join("<br>");
        }}

        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.min.js";
        script.onload = () => {{
          try {{
            init3D();
          }} catch (e) {{
            console.error(e);
            fallback();
          }}
        }};
        script.onerror = fallback;
        document.head.appendChild(script);

        function init3D() {{
          const THREE = window.THREE;
          document.getElementById("fallback").remove();

          const scene = new THREE.Scene();
          scene.background = new THREE.Color(payload.bg);

          const camera = new THREE.PerspectiveCamera(
            55, window.innerWidth / window.innerHeight, 0.1, 1000
          );
          camera.position.set(0, 0, 18);

          const renderer = new THREE.WebGLRenderer({{ antialias: true }});
          renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
          renderer.setSize(window.innerWidth, window.innerHeight);
          document.body.appendChild(renderer.domElement);

          const ambient = new THREE.AmbientLight(0xffffff, 1.2);
          scene.add(ambient);

          const light = new THREE.PointLight(0xffffff, 2.4, 100);
          light.position.set(6, 8, 12);
          scene.add(light);

          const group = new THREE.Group();
          scene.add(group);

          const positions = {{}};
          const n = Math.max(payload.nodes.length, 1);

          payload.nodes.forEach((node, i) => {{
            const a = (i / n) * Math.PI * 2;
            const radius = 5.5 + (i % 3) * 1.15;
            const x = Math.cos(a) * radius;
            const y = Math.sin(a * 1.7) * 3.0;
            const z = Math.sin(a) * radius * .55;
            positions[node.id] = new THREE.Vector3(x, y, z);

            const geometry = new THREE.SphereGeometry(
              node.size ? Math.max(.25, node.size) : .48, 20, 20
            );
            const color = node.color || (i % 2 ? payload.accent2 : payload.accent);
            const material = new THREE.MeshStandardMaterial({{
              color: color,
              roughness: .28,
              metalness: .35,
              emissive: color,
              emissiveIntensity: node.active ? .35 : .08
            }});
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.copy(positions[node.id]);
            mesh.userData = node;
            group.add(mesh);

            const labelCanvas = document.createElement("canvas");
            labelCanvas.width = 512;
            labelCanvas.height = 96;
            const ctx = labelCanvas.getContext("2d");
            ctx.fillStyle = "rgba(0,0,0,0)";
            ctx.fillRect(0,0,512,96);
            ctx.fillStyle = "{c["text"]}";
            ctx.font = "bold 28px system-ui";
            ctx.textAlign = "center";
            ctx.fillText(String(node.label || node.id).slice(0, 30), 256, 55);
            const texture = new THREE.CanvasTexture(labelCanvas);
            const spriteMaterial = new THREE.SpriteMaterial({{
              map: texture, transparent: true, depthWrite: false
            }});
            const sprite = new THREE.Sprite(spriteMaterial);
            sprite.scale.set(3.2, .6, 1);
            sprite.position.copy(mesh.position);
            sprite.position.y += .75;
            group.add(sprite);
          }});

          payload.edges.forEach(pair => {{
            const a = positions[pair[0]];
            const b = positions[pair[1]];
            if (!a || !b) return;
            const geometry = new THREE.BufferGeometry().setFromPoints([a,b]);
            const material = new THREE.LineBasicMaterial({{
              color: payload.accent2,
              transparent: true,
              opacity: .34
            }});
            group.add(new THREE.Line(geometry, material));
          }});

          const raycaster = new THREE.Raycaster();
          const mouse = new THREE.Vector2();

          function pointer(ev) {{
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(mouse, camera);
            const hits = raycaster.intersectObjects(group.children, true);
            const hit = hits.find(h => h.object && h.object.userData && h.object.userData.label);
            if (hit) {{
              const n = hit.object.userData;
              window.parent.postMessage({{
                type: "wb-node-selected",
                id: n.id,
                label: n.label
              }}, "*");
            }}
          }}
          renderer.domElement.addEventListener("click", pointer);

          let dragging = false, px = 0, py = 0, rx = 0, ry = 0;
          renderer.domElement.addEventListener("pointerdown", e => {{
            dragging = true; px = e.clientX; py = e.clientY;
          }});
          renderer.domElement.addEventListener("pointerup", () => dragging = false);
          renderer.domElement.addEventListener("pointermove", e => {{
            if (!dragging) return;
            ry += (e.clientX - px) * .006;
            rx += (e.clientY - py) * .006;
            px = e.clientX; py = e.clientY;
          }});
          renderer.domElement.addEventListener("wheel", e => {{
            camera.position.z = Math.max(7, Math.min(30, camera.position.z + e.deltaY * .012));
          }}, {{passive:true}});

          function animate(t) {{
            requestAnimationFrame(animate);
            if (!{str(st.session_state.get("reduced_motion", False)).lower()}) {{
              group.rotation.y += .0018;
              group.rotation.y += ry * .0005;
              group.rotation.x = Math.max(-.8, Math.min(.8, rx));
            }}
            ry *= .96;
            rx *= .96;
            renderer.render(scene, camera);
          }}
          animate();

          window.addEventListener("resize", () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
          }});
        }}
      </script>
    </body>
    </html>
    """

    components.html(html_doc, height=height, scrolling=False)


# =============================================================================
# Shell
# =============================================================================

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ◈ 3D Workbench")
        st.caption(f"v{APP_VERSION}")

        pages = {
            "home": t("home"),
            "notes": t("notes"),
            "review": t("review"),
            "skills": t("skills"),
            "pipeline": t("pipeline"),
            "agents": t("agents"),
            "results": t("results"),
            "visuals": t("visuals"),
            "settings": t("settings"),
        }

        current = st.session_state["page"]
        for key, label in pages.items():
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state["page"] = key
                add_log(f"Navigation: {label}", "INFO", "ui")
                st.rerun()

        st.divider()
        st.caption("Runtime")
        provider = st.session_state.get("active_provider", "Gemini")
        status = provider_key_status(provider)
        state_label = "● configured" if status["configured"] else "○ fallback"
        st.write(f"**{provider}** · {state_label}")
        st.write(f"**Model:** `{st.session_state['global_model']}`")
        st.write(f"**Runs:** {st.session_state['run_count']}")
        st.write(f"**Tokens≈:** {st.session_state['token_estimate']:,}")

        st.divider()
        if st.button("↻ Reset session UI", use_container_width=True):
            for key in ["page", "dashboard_open", "flash"]:
                st.session_state.pop(key, None)
            st.session_state["page"] = "home"
            add_log("Session UI reset.", "INFO", "ui")
            st.rerun()


def render_topbar() -> None:
    left, mid, right = st.columns([2.5, 3.5, 2])
    with left:
        st.markdown(
            '<div class="wb-chip">TRACEABLE</div>'
            '<div class="wb-chip">AI-AUGMENTED</div>'
            '<div class="wb-chip">WEBGL</div>',
            unsafe_allow_html=True,
        )
    with mid:
        st.caption(
            f"Provider: {st.session_state['active_provider']} · "
            f"Model: {st.session_state['global_model']}"
        )
    with right:
        if st.button("⚙", help="Settings", key="top_settings"):
            st.session_state["page"] = "settings"
            st.rerun()


def render_flash() -> None:
    flash = st.session_state.get("flash")
    if not flash:
        return
    if flash["level"] == "error":
        st.error(flash["message"])
    elif flash["level"] == "warning":
        st.warning(flash["message"])
    else:
        st.success(flash["message"])
    clear_flash()


def render_dashboard() -> None:
    if not st.session_state.get("dashboard_open", True):
        return

    logs = st.session_state.get("logs", [])[-14:]
    log_html = "<br>".join(
        f"[{html.escape(item['level'])}] {html.escape(item['message'])}"
        for item in reversed(logs)
    )

    c = theme_tokens()
    st.markdown(
        f"""
        <div class="wb-floating">
          <div style="font-weight:800;margin-bottom:7px;">◉ Live Observatory</div>
          <div style="font-size:.72rem;color:{c["muted"]};margin-bottom:8px;">
            {html.escape(st.session_state["page"])} ·
            {html.escape(st.session_state["active_provider"])} ·
            {html.escape(st.session_state["global_model"])}
          </div>
          <div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px;">
            <span class="wb-chip">{st.session_state["run_count"]} runs</span>
            <span class="wb-chip">≈ {st.session_state["token_estimate"]:,} tokens</span>
            <span class="wb-chip">{artifact_count()} artifacts</span>
          </div>
          <div class="wb-log">{log_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Home
# =============================================================================

def page_home() -> None:
    st.markdown(
        """
        <div class="wb-hero">
          <div class="wb-title">Next-Generation 3D WebGL Workbench</div>
          <div class="wb-subtitle">
            Evidence-first AI workflows · multilingual workspace · governed artifacts · live observability
          </div>
          <div style="margin-top:14px;">
            <span class="wb-chip">Traditional Chinese</span>
            <span class="wb-chip">Gemini default</span>
            <span class="wb-chip">A/B/C evaluation</span>
            <span class="wb-chip">Pipeline Galaxy</span>
            <span class="wb-chip">Secure provider fallback</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    kpis = [
        ("Notes", len(st.session_state["notes"])),
        ("Skills", len(st.session_state["skills"])),
        ("Pipelines", len(st.session_state["pipelines"])),
        ("Artifacts", artifact_count()),
    ]
    for col, (label, value) in zip(cols, kpis):
        with col:
            st.markdown(
                f'<div class="wb-card"><div class="wb-muted">{label}</div>'
                f'<div class="wb-kpi">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="wb-section">Workbench Launchpad</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        if st.button("✦ Open AI Note Keeper", use_container_width=True):
            st.session_state["page"] = "notes"
            st.rerun()
        if st.button("◈ Open Review Bench", use_container_width=True):
            st.session_state["page"] = "review"
            st.rerun()
    with b:
        if st.button("◇ Open Skill Studio", use_container_width=True):
            st.session_state["page"] = "skills"
            st.rerun()
        if st.button("⌁ Open Pipeline Studio", use_container_width=True):
            st.session_state["page"] = "pipeline"
            st.rerun()
    with c:
        if st.button("◎ Open 3D Visualization", use_container_width=True):
            st.session_state["page"] = "visuals"
            st.rerun()
        if st.button("▣ Open Results Library", use_container_width=True):
            st.session_state["page"] = "results"
            st.rerun()

    st.markdown('<div class="wb-section">Workspace topology</div>', unsafe_allow_html=True)

    nodes = [
        {"id": "notes", "label": "AI Notes", "active": True, "size": .62},
        {"id": "review", "label": "Review Bench", "size": .55},
        {"id": "skills", "label": "Skill Studio", "size": .60},
        {"id": "pipeline", "label": "Pipeline", "size": .66},
        {"id": "agents", "label": "Agents", "size": .50},
        {"id": "results", "label": "Results", "size": .56},
    ]
    edges = [
        ("notes", "review"),
        ("notes", "skills"),
        ("skills", "pipeline"),
        ("agents", "skills"),
        ("pipeline", "results"),
        ("review", "results"),
    ]
    webgl_scene("Workspace Constellation", nodes, edges, height=500)


# =============================================================================
# Note Keeper
# =============================================================================

def note_by_id(note_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not note_id:
        return None
    return next((n for n in st.session_state["notes"] if n["id"] == note_id), None)


def page_notes() -> None:
    st.title(t("notes"))

    left, right = st.columns([1, 2.1])
    with left:
        st.subheader("Intake")
        uploaded = st.file_uploader(
            "Upload text / Markdown / PDF",
            type=["txt", "md", "markdown", "pdf", "json", "yaml", "yml", "csv"],
            key="note_upload",
        )
        if uploaded and st.button("Import file", use_container_width=True):
            text, metadata = extract_uploaded_file(uploaded)
            note = {
                "id": uid("note"),
                "title": uploaded.name,
                "raw": text,
                "markdown": text,
                "metadata": metadata,
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
            st.session_state["notes"].insert(0, note)
            st.session_state["current_note_id"] = note["id"]
            add_log(f"Note imported: {uploaded.name}", "INFO", "notes")
            set_flash("Note imported successfully.")
            st.rerun()

        if st.button("＋ New note", use_container_width=True):
            note = {
                "id": uid("note"),
                "title": "Untitled Note",
                "raw": "",
                "markdown": "# Untitled Note\n\n",
                "metadata": {"source": "manual"},
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
            st.session_state["notes"].insert(0, note)
            st.session_state["current_note_id"] = note["id"]
            add_log("New note created.", "INFO", "notes")
            st.rerun()

        if st.session_state["notes"]:
            options = {
                f"{n['title']} · {short_id(n['id'])}": n["id"]
                for n in st.session_state["notes"]
            }
            labels = list(options.keys())
            current_id = st.session_state.get("current_note_id")
            default_idx = 0
            for i, label in enumerate(labels):
                if options[label] == current_id:
                    default_idx = i
                    break
            selected_label = st.selectbox("Open note", labels, index=default_idx)
            st.session_state["current_note_id"] = options[selected_label]

        st.divider()
        st.subheader("AI Magics")
        magic = st.selectbox(
            "Transformation",
            [
                "Structure Notes",
                "Extract Entities",
                "Draft Summary",
                "Find Gaps & Contradictions",
                "Translate & Harmonize",
                "AI Keyword Colorizer",
            ],
        )
        if st.button("✦ Run AI Magic", use_container_width=True):
            note = note_by_id(st.session_state.get("current_note_id"))
            if not note:
                st.warning("Create or import a note first.")
            else:
                prompt = f"""
You are working inside an evidence-first note workspace.
Magic: {magic}
Do not invent source facts. Clearly separate source-derived statements
from suggestions.

SOURCE:
{note["raw"]}
"""
                try:
                    result = execute_ai(
                        prompt,
                        model=st.session_state["global_model"],
                        purpose=f"Note Magic: {magic}",
                    )
                    note["markdown"] = result
                    note["updated_at"] = now_iso()
                    save_artifact("note_transform", f"{note['title']} — {magic}", result)
                    set_flash(f"{magic} completed.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with right:
        note = note_by_id(st.session_state.get("current_note_id"))
        if not note:
            st.info("Select a note or create a new one.")
            return

        title = st.text_input("Title", value=note["title"], key=f"title_{note['id']}")
        edited = st.text_area(
            "Structured Markdown",
            value=note["markdown"],
            height=500,
            key=f"editor_{note['id']}",
        )

        if st.button("Save note", type="primary"):
            note["title"] = title
            note["markdown"] = edited
            note["updated_at"] = now_iso()
            save_artifact("note", title, edited, {"source_note_id": note["id"]})
            add_log(f"Note saved: {title}", "INFO", "notes")
            set_flash("Note saved.")
            st.rerun()

        st.markdown("#### Keyword Colorizer")
        keywords = st.text_input(
            "Comma-separated keywords",
            value=", ".join(st.session_state.get("note_highlights", [])),
        )
        if st.button("Apply coral highlights"):
            st.session_state["note_highlights"] = [
                x.strip() for x in keywords.split(",") if x.strip()
            ]
            add_log("Keyword highlight set updated.", "INFO", "notes")

        highlighted = edited
        for kw in st.session_state.get("note_highlights", []):
            highlighted = re.sub(
                re.escape(kw),
                lambda m: f'<span class="wb-coral">{html.escape(m.group(0))}</span>',
                highlighted,
                flags=re.IGNORECASE,
            )

        st.markdown("#### Preview")
        st.markdown(highlighted, unsafe_allow_html=True)


# =============================================================================
# Review Bench
# =============================================================================

def page_review() -> None:
    st.title(t("review"))
    st.caption("Evidence-first intake, normalization, contradiction mapping, and report generation.")

    st.session_state["review"]["case_name"] = st.text_input(
        "Case / project name",
        value=st.session_state["review"].get("case_name", ""),
    )

    uploads = st.file_uploader(
        "Upload review materials",
        type=["txt", "md", "pdf", "json", "yaml", "yml", "csv"],
        accept_multiple_files=True,
        key="review_uploads",
    )

    if uploads:
        st.session_state["review"]["files"] = []
        for item in uploads:
            text, meta = extract_uploaded_file(item)
            st.session_state["review"]["files"].append(
                {"name": item.name, "text": text, "metadata": meta}
            )

    c1, c2, c3 = st.columns(3)
    with c1:
        parse = st.button("1 · Parse evidence", use_container_width=True)
    with c2:
        draft = st.button("2 · Draft review", use_container_width=True)
    with c3:
        final = st.button("3 · Build final report", use_container_width=True)

    if parse:
        all_text = "\n\n".join(
            f"# {x['name']}\n{x['text']}"
            for x in st.session_state["review"]["files"]
        )
        if not all_text:
            st.warning("Upload at least one review file.")
        else:
            sentences = re.split(r"(?<=[.!?。！？])\s+", all_text)
            claims = [
                {
                    "id": uid("claim"),
                    "text": s.strip(),
                    "source": "uploaded evidence",
                    "support": "pending",
                }
                for s in sentences if len(s.strip()) > 15
            ][:80]
            conflicts = []
            for i, claim in enumerate(claims):
                if "not " in claim["text"].lower() or "不" in claim["text"]:
                    conflicts.append(
                        {
                            "id": uid("conflict"),
                            "claim_id": claim["id"],
                            "type": "potential contradiction",
                            "text": claim["text"],
                        }
                    )
            st.session_state["review"]["claims"] = claims
            st.session_state["review"]["conflicts"] = conflicts
            add_log(f"Review parsed: {len(claims)} claims, {len(conflicts)} flags.", "INFO", "review")
            set_flash("Evidence parsing completed.")
            st.rerun()

    if draft:
        source = "\n".join(x["text"] for x in st.session_state["review"]["files"])
        prompt = f"""
Create a professional evidence-first review draft for:
{st.session_state["review"]["case_name"]}

Rules:
- Do not invent evidence.
- Separate source facts, observations, and open questions.
- Include a claim/evidence matrix.
- Include contradictions and missing evidence.
- Be explicit about uncertainty.

SOURCE:
{source}
"""
        try:
            st.session_state["review"]["draft"] = execute_ai(
                prompt, purpose="Review Bench draft"
            )
            add_log("Review draft generated.", "INFO", "review")
            set_flash("Draft generated.")
        except Exception as exc:
            st.error(str(exc))

    if final:
        draft_text = st.session_state["review"].get("draft", "")
        if not draft_text:
            st.warning("Generate the draft first.")
        else:
            prompt = f"""
Convert the following review draft into a final professional report.
Preserve traceability. Do not add unsupported claims.

DRAFT:
{draft_text}
"""
            try:
                st.session_state["review"]["final"] = execute_ai(
                    prompt, purpose="Review Bench final report"
                )
                save_artifact(
                    "review_report",
                    st.session_state["review"]["case_name"] or "Review Report",
                    st.session_state["review"]["final"],
                )
                add_log("Final review report generated.", "INFO", "review")
                set_flash("Final report generated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.divider()
    tabs = st.tabs(["Claims", "Conflicts", "Draft", "Final"])
    with tabs[0]:
        st.dataframe(
            st.session_state["review"]["claims"],
            use_container_width=True,
            hide_index=True,
        )
    with tabs[1]:
        st.dataframe(
            st.session_state["review"]["conflicts"],
            use_container_width=True,
            hide_index=True,
        )
    with tabs[2]:
        st.text_area(
            "Draft",
            value=st.session_state["review"].get("draft", ""),
            height=400,
            key="review_draft_view",
        )
    with tabs[3]:
        final_text = st.session_state["review"].get("final", "")
        st.markdown(final_text if final_text else "_No final report yet._")


# =============================================================================
# Skill Studio
# =============================================================================

def current_skill() -> Dict[str, Any]:
    skill_id = st.session_state.get("current_skill_id")
    if skill_id:
        for skill in st.session_state["skills"]:
            if skill["id"] == skill_id:
                return skill
    if st.session_state["skills"]:
        st.session_state["current_skill_id"] = st.session_state["skills"][0]["id"]
        return st.session_state["skills"][0]
    skill = default_skill()
    st.session_state["skills"].append(skill)
    st.session_state["current_skill_id"] = skill["id"]
    return skill


def skill_prompt(skill: Dict[str, Any], input_text: str) -> str:
    return (
        f"{skill.get('system','')}\n\n"
        f"Instructions:\n{skill.get('instructions','')}\n\n"
        f"Input:\n{input_text}"
    )


def page_skills() -> None:
    st.title(t("skills"))
    st.caption("Create, edit, run, compare, and review governed skills.")

    left, right = st.columns([1, 2.2])
    with left:
        st.subheader("Skill Library")
        if st.button("＋ Create skill", use_container_width=True):
            skill = default_skill(f"New Skill {len(st.session_state['skills']) + 1}")
            st.session_state["skills"].insert(0, skill)
            st.session_state["current_skill_id"] = skill["id"]
            add_log("Skill created.", "INFO", "skills")
            st.rerun()

        options = {
            f"{s['name']} · v{s['version']}": s["id"]
            for s in st.session_state["skills"]
        }
        selected = st.selectbox("Open skill", list(options.keys()))
        st.session_state["current_skill_id"] = options[selected]

        if st.button("Download selected skill", use_container_width=True):
            skill = current_skill()
            payload = (
                f"# {skill['name']}\n\n"
                f"Version: {skill['version']}\n\n"
                f"## System\n{skill['system']}\n\n"
                f"## Instructions\n{skill['instructions']}\n"
            )
            st.download_button(
                "Download SKILL.md",
                data=payload,
                file_name=f"{skill['name'].replace(' ','_')}.md",
                mime="text/markdown",
                key="skill_dl",
            )

    skill = current_skill()
    with right:
        skill["name"] = st.text_input("Name", skill["name"])
        skill["description"] = st.text_area("Description", skill["description"], height=80)
        skill["version"] = st.text_input("Version", skill["version"])
        skill["system"] = st.text_area("System", skill["system"], height=140)
        skill["instructions"] = st.text_area("Instructions", skill["instructions"], height=220)

        if st.button("Save skill", type="primary"):
            skill["updated_at"] = now_iso()
            save_artifact(
                "skill",
                skill["name"],
                skill,
                {"skill_id": skill["id"], "version": skill["version"]},
            )
            add_log(f"Skill saved: {skill['name']}", "INFO", "skills")
            set_flash("Skill saved.")
            st.rerun()

    st.divider()
    st.subheader("A / B / C Skill Arena")

    cmp = st.session_state["comparison"]
    skill_ids = [s["id"] for s in st.session_state["skills"]]
    labels = {s["id"]: s["name"] for s in st.session_state["skills"]}

    if skill_ids:
        c1, c2, c3 = st.columns(3)
        with c1:
            cmp["skill_a"] = st.selectbox(
                "Skill A", skill_ids,
                index=skill_ids.index(cmp["skill_a"]) if cmp["skill_a"] in skill_ids else 0,
                format_func=lambda x: labels[x],
            )
            cmp["model_a"] = st.selectbox(
                "Model A", list(MODELS.keys()),
                index=list(MODELS.keys()).index(cmp["model_a"])
                if cmp["model_a"] in MODELS else 0,
            )
        with c2:
            cmp["skill_b"] = st.selectbox(
                "Skill B", skill_ids,
                index=skill_ids.index(cmp["skill_b"]) if cmp["skill_b"] in skill_ids else min(1, len(skill_ids)-1),
                format_func=lambda x: labels[x],
            )
            cmp["model_b"] = st.selectbox(
                "Model B", list(MODELS.keys()),
                index=list(MODELS.keys()).index(cmp["model_b"])
                if cmp["model_b"] in MODELS else 0,
            )
        with c3:
            cmp["skill_c"] = st.selectbox(
                "Review skill C", skill_ids,
                index=skill_ids.index(cmp["skill_c"]) if cmp["skill_c"] in skill_ids else 0,
                format_func=lambda x: labels[x],
            )
            cmp["model_c"] = st.selectbox(
                "Review model C", list(MODELS.keys()),
                index=list(MODELS.keys()).index(cmp["model_c"])
                if cmp["model_c"] in MODELS else 0,
            )

    cmp["input"] = st.text_area(
        "Comparison input",
        value=cmp.get("input", ""),
        height=180,
        placeholder="Paste the same evidence/task into A and B.",
    )
    cmp["criteria"] = st.text_input(
        "C review criteria",
        value=cmp.get("criteria", ""),
    )

    a, b, c = st.columns(3)
    with a:
        run_a = st.button("▶ Run A", use_container_width=True)
    with b:
        run_b = st.button("▶ Run B", use_container_width=True)
    with c:
        run_c = st.button("◎ Run C review", use_container_width=True)

    if run_a:
        selected_skill = next(s for s in st.session_state["skills"] if s["id"] == cmp["skill_a"])
        try:
            cmp["output_a"] = execute_ai(
                skill_prompt(selected_skill, cmp["input"]),
                model=cmp["model_a"],
                purpose="Skill Arena A",
            )
            add_log("Skill Arena A completed.", "INFO", "skills")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if run_b:
        selected_skill = next(s for s in st.session_state["skills"] if s["id"] == cmp["skill_b"])
        try:
            cmp["output_b"] = execute_ai(
                skill_prompt(selected_skill, cmp["input"]),
                model=cmp["model_b"],
                purpose="Skill Arena B",
            )
            add_log("Skill Arena B completed.", "INFO", "skills")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if run_c:
        selected_skill = next(s for s in st.session_state["skills"] if s["id"] == cmp["skill_c"])
        review_prompt = f"""
{skill_prompt(selected_skill, "")}

You are the C reviewer in an A/B/C comparison.
Compare the two outputs below using these criteria:
{cmp["criteria"]}

OUTPUT A:
{cmp["output_a"]}

OUTPUT B:
{cmp["output_b"]}

Return:
1. Shared strengths
2. Material differences
3. Evidence fidelity
4. Completeness
5. Traceability
6. Concrete revision suggestions
7. Comprehensive reviewer comments

Do not invent facts that are not present in A, B, or the input.
"""
        try:
            cmp["review_c"] = execute_ai(
                review_prompt,
                model=cmp["model_c"],
                purpose="Skill Arena C review",
            )
            save_artifact(
                "abc_comparison",
                "A-B-C Skill Comparison",
                copy.deepcopy(cmp),
            )
            add_log("Skill Arena C review completed.", "INFO", "skills")
            set_flash("A/B/C comparison completed.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    o1, o2, o3 = st.columns(3)
    with o1:
        st.markdown("### A")
        st.markdown(cmp.get("output_a") or "_Not run._")
    with o2:
        st.markdown("### B")
        st.markdown(cmp.get("output_b") or "_Not run._")
    with o3:
        st.markdown("### C Review")
        st.markdown(cmp.get("review_c") or "_Not run._")

    nodes = [
        {"id": "A", "label": "Skill A", "active": bool(cmp.get("output_a")), "size": .65},
        {"id": "B", "label": "Skill B", "active": bool(cmp.get("output_b")), "size": .65},
        {"id": "C", "label": "C Review", "active": bool(cmp.get("review_c")), "size": .72},
        {"id": "input", "label": "Shared Input", "size": .55},
    ]
    edges = [("input", "A"), ("input", "B"), ("A", "C"), ("B", "C")]
    webgl_scene("Skill Arena", nodes, edges, height=420)


# =============================================================================
# Pipeline Studio
# =============================================================================

def current_pipeline() -> Dict[str, Any]:
    pipeline_id = st.session_state.get("current_pipeline_id")
    if pipeline_id:
        for p in st.session_state["pipelines"]:
            if p["id"] == pipeline_id:
                return p
    if st.session_state["pipelines"]:
        st.session_state["current_pipeline_id"] = st.session_state["pipelines"][0]["id"]
        return st.session_state["pipelines"][0]
    pipeline = default_pipeline()
    st.session_state["pipelines"].append(pipeline)
    st.session_state["current_pipeline_id"] = pipeline["id"]
    return pipeline


def validate_pipeline(pipeline: Dict[str, Any]) -> List[str]:
    issues = []
    ids = [n["id"] for n in pipeline.get("nodes", [])]
    if len(ids) != len(set(ids)):
        issues.append("Duplicate node IDs.")
    node_set = set(ids)
    for a, b in pipeline.get("edges", []):
        if a not in node_set or b not in node_set:
            issues.append(f"Edge references missing node: {a} → {b}")
    if not pipeline.get("nodes"):
        issues.append("Pipeline contains no nodes.")
    return issues


def run_pipeline(pipeline: Dict[str, Any], input_text: str) -> None:
    run = {
        "id": uid("run"),
        "pipeline_id": pipeline["id"],
        "started_at": now_iso(),
        "input": input_text,
        "nodes": {},
    }
    st.session_state["pipeline_run"] = run

    for node in pipeline["nodes"]:
        node["status"] = "running"
        add_log(f"Pipeline node started: {node['label']}", "INFO", "pipeline")
        time.sleep(0.03)

        if node["type"] == "input":
            output = input_text
        elif node["type"] == "parse":
            output = "\n".join(
                f"- {s.strip()}" for s in re.split(r"\n+|(?<=[.!?。！？])\s+", input_text)
                if s.strip()
            )
        elif node["type"] == "extract":
            terms = sorted(set(re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b", input_text)))
            output = json.dumps({"entities": terms[:80]}, ensure_ascii=False, indent=2)
        elif node["type"] == "compare":
            output = "Comparison checkpoint created from normalized pipeline input."
        elif node["type"] == "review":
            output = heuristic_ai(input_text, st.session_state["global_model"])
        elif node["type"] == "export":
            output = json.dumps(
                {
                    "pipeline": pipeline["name"],
                    "run_id": run["id"],
                    "input_hash": hash_text(input_text),
                },
                ensure_ascii=False,
                indent=2,
            )
        else:
            output = input_text

        node["status"] = "complete"
        run["nodes"][node["id"]] = output
        add_log(f"Pipeline node completed: {node['label']}", "INFO", "pipeline")

    run["finished_at"] = now_iso()
    save_artifact("pipeline_run", f"{pipeline['name']} Run", run)
    set_flash("Pipeline run completed.")


def page_pipeline() -> None:
    st.title(t("pipeline"))
    st.caption("Graph-native workflow builder with deterministic checkpoints and 3D execution visualization.")

    left, right = st.columns([1, 2.2])
    with left:
        if st.button("＋ New pipeline", use_container_width=True):
            p = default_pipeline()
            p["name"] = f"Pipeline {len(st.session_state['pipelines']) + 1}"
            st.session_state["pipelines"].insert(0, p)
            st.session_state["current_pipeline_id"] = p["id"]
            add_log("Pipeline created.", "INFO", "pipeline")
            st.rerun()

        options = {
            f"{p['name']} · v{p['version']}": p["id"]
            for p in st.session_state["pipelines"]
        }
        selected = st.selectbox("Open pipeline", list(options.keys()))
        st.session_state["current_pipeline_id"] = options[selected]

    pipeline = current_pipeline()
    with right:
        pipeline["name"] = st.text_input("Pipeline name", pipeline["name"])
        pipeline["description"] = st.text_area(
            "Description", pipeline["description"], height=70
        )

        st.markdown("#### Nodes")
        for idx, node in enumerate(pipeline["nodes"]):
            a, b, c, d = st.columns([.7, 2, 1.2, .8])
            with a:
                st.write(node["id"])
            with b:
                node["label"] = st.text_input(
                    "Label",
                    node["label"],
                    key=f"node_label_{pipeline['id']}_{idx}",
                    label_visibility="collapsed",
                )
            with c:
                node["type"] = st.selectbox(
                    "Type",
                    ["input", "parse", "extract", "transform", "compare", "review", "merge", "export"],
                    index=["input", "parse", "extract", "transform", "compare", "review", "merge", "export"].index(node["type"])
                    if node["type"] in ["input", "parse", "extract", "transform", "compare", "review", "merge", "export"] else 0,
                    key=f"node_type_{pipeline['id']}_{idx}",
                    label_visibility="collapsed",
                )
            with d:
                st.write(node.get("status", "idle"))

        add_col, validate_col, save_col = st.columns(3)
        with add_col:
            if st.button("＋ Add node", use_container_width=True):
                pipeline["nodes"].append(
                    {
                        "id": f"n{len(pipeline['nodes'])+1}",
                        "label": "New node",
                        "type": "transform",
                        "status": "idle",
                    }
                )
                pipeline["updated_at"] = now_iso()
                st.rerun()
        with validate_col:
            if st.button("Validate", use_container_width=True):
                issues = validate_pipeline(pipeline)
                if issues:
                    for issue in issues:
                        st.error(issue)
                    add_log(f"Pipeline validation failed: {len(issues)} issue(s).", "ERROR", "pipeline")
                else:
                    st.success("Pipeline valid.")
                    add_log("Pipeline validation passed.", "INFO", "pipeline")
        with save_col:
            if st.button("Save pipeline", type="primary", use_container_width=True):
                pipeline["updated_at"] = now_iso()
                save_artifact("pipeline", pipeline["name"], pipeline)
                add_log(f"Pipeline saved: {pipeline['name']}", "INFO", "pipeline")
                set_flash("Pipeline saved.")
                st.rerun()

    st.divider()
    st.subheader("Pipeline Galaxy")

    positions_nodes = [
        {
            "id": n["id"],
            "label": n["label"],
            "active": n.get("status") == "running",
            "size": .48 + (0.12 if n.get("status") == "complete" else 0),
        }
        for n in pipeline["nodes"]
    ]
    webgl_scene(
        "Pipeline Galaxy",
        positions_nodes,
        [tuple(e) for e in pipeline["edges"]],
        height=450,
        scene_type="pipeline",
    )

    input_text = st.text_area(
        "Pipeline input",
        value="",
        height=140,
        placeholder="Enter or paste evidence to run through the pipeline.",
    )

    if st.button("▶ Run pipeline", type="primary"):
        issues = validate_pipeline(pipeline)
        if issues:
            for issue in issues:
                st.error(issue)
        elif not input_text.strip():
            st.warning("Provide pipeline input first.")
        else:
            run_pipeline(pipeline, input_text)
            st.rerun()

    run = st.session_state.get("pipeline_run", {})
    if run:
        st.subheader("Run outputs")
        st.json(run)


# =============================================================================
# Agent Studio
# =============================================================================

def parse_yaml(text: str) -> Tuple[Any, Optional[str]]:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text), None
    except ImportError:
        return None, "PyYAML is not installed."
    except Exception as exc:
        return None, str(exc)


def normalize_yaml(text: str) -> str:
    data, error = parse_yaml(text)
    if error:
        raise ValueError(error)
    try:
        import yaml  # type: ignore
        return yaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    except Exception as exc:
        raise ValueError(str(exc)) from exc


def page_agents() -> None:
    st.title(t("agents"))
    st.caption("Normalize, validate, diff, and export agent YAML and SKILL.md assets.")

    yaml_upload = st.file_uploader("Upload agents.yaml", type=["yaml", "yml"])
    skill_upload = st.file_uploader("Upload SKILL.md", type=["md"])

    if yaml_upload:
        st.session_state["agent_yaml"] = yaml_upload.getvalue().decode("utf-8", errors="replace")
    if skill_upload:
        st.session_state["agent_skill_md"] = skill_upload.getvalue().decode("utf-8", errors="replace")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state["agent_yaml"] = st.text_area(
            "agents.yaml",
            value=st.session_state.get("agent_yaml", ""),
            height=420,
        )
    with c2:
        st.session_state["agent_skill_md"] = st.text_area(
            "SKILL.md",
            value=st.session_state.get("agent_skill_md", ""),
            height=420,
        )

    a, b, c = st.columns(3)
    with a:
        if st.button("Validate YAML", use_container_width=True):
            data, error = parse_yaml(st.session_state["agent_yaml"])
            if error:
                st.session_state["agent_validation"] = [error]
                add_log("Agent YAML validation failed.", "ERROR", "agents")
            else:
                issues = []
                if not isinstance(data, (dict, list)):
                    issues.append("Root YAML structure should be a mapping or list.")
                st.session_state["agent_validation"] = issues
                add_log("Agent YAML validation passed.", "INFO", "agents")
    with b:
        if st.button("Standardize YAML", use_container_width=True):
            try:
                st.session_state["agent_yaml"] = normalize_yaml(st.session_state["agent_yaml"])
                add_log("Agent YAML standardized.", "INFO", "agents")
                set_flash("YAML standardized.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with c:
        if st.button("Export agent bundle", use_container_width=True):
            bundle = {
                "agents.yaml": st.session_state["agent_yaml"],
                "SKILL.md": st.session_state["agent_skill_md"],
                "exported_at": now_iso(),
            }
            save_artifact("agent_bundle", "Agent Bundle", bundle)
            st.download_button(
                "Download bundle JSON",
                data=json.dumps(bundle, ensure_ascii=False, indent=2),
                file_name="agent_bundle.json",
                mime="application/json",
                key="agent_bundle_download",
            )

    if st.session_state["agent_validation"]:
        for issue in st.session_state["agent_validation"]:
            st.error(issue)
    else:
        if st.session_state["agent_yaml"].strip():
            st.success("No recorded validation errors.")


# =============================================================================
# Results Library
# =============================================================================

def page_results() -> None:
    st.title(t("results"))
    st.caption("Portable, traceable workspace artifacts.")

    if not st.session_state["artifacts"]:
        st.info("No artifacts yet. Save a note, skill, pipeline, review, or comparison.")
        return

    kinds = sorted(set(a["kind"] for a in st.session_state["artifacts"]))
    selected_kind = st.selectbox("Filter", ["All"] + kinds)

    items = st.session_state["artifacts"]
    if selected_kind != "All":
        items = [a for a in items if a["kind"] == selected_kind]

    for artifact in items:
        with st.expander(
            f"{artifact['name']} · {artifact['kind']} · {artifact['created_at']}"
        ):
            st.caption(f"ID: {artifact['id']}")
            content = artifact["content"]
            if isinstance(content, (dict, list)):
                st.json(content)
            else:
                st.markdown(safe_text(content)[:12000])

            st.download_button(
                "Download artifact",
                data=artifact_bytes(artifact),
                file_name=f"{artifact['name'].replace(' ','_')}.{ 'json' if isinstance(content,(dict,list)) else 'md' }",
                mime="application/json" if isinstance(content, (dict,list)) else "text/markdown",
                key=f"artifact_dl_{artifact['id']}",
            )


# =============================================================================
# Visualization hub
# =============================================================================

def page_visuals() -> None:
    st.title(t("visuals"))
    st.caption("Interactive WebGL scenes backed by the current workspace state.")

    scene = st.selectbox(
        "Scene",
        [
            "Evidence Constellation",
            "Skill Arena",
            "Pipeline Galaxy",
            "Conflict Prism",
        ],
    )

    if scene == "Evidence Constellation":
        nodes = [
            {"id": "case", "label": "Case", "size": .75, "active": True},
            {"id": "doc1", "label": "Document A", "size": .52},
            {"id": "doc2", "label": "Document B", "size": .52},
            {"id": "claim", "label": "Claim", "size": .60},
            {"id": "test", "label": "Test", "size": .55},
            {"id": "output", "label": "Report", "size": .65},
        ]
        edges = [
            ("case", "doc1"), ("case", "doc2"), ("doc1", "claim"),
            ("doc2", "claim"), ("claim", "test"), ("test", "output"),
        ]
        webgl_scene(scene, nodes, edges, height=570)

    elif scene == "Skill Arena":
        cmp = st.session_state["comparison"]
        nodes = [
            {"id": "A", "label": "A", "active": bool(cmp.get("output_a")), "size": .7},
            {"id": "B", "label": "B", "active": bool(cmp.get("output_b")), "size": .7},
            {"id": "C", "label": "C Review", "active": bool(cmp.get("review_c")), "size": .8},
        ]
        webgl_scene(scene, nodes, [("A", "C"), ("B", "C")], height=570)

    elif scene == "Pipeline Galaxy":
        p = current_pipeline()
        nodes = [
            {
                "id": n["id"],
                "label": n["label"],
                "active": n.get("status") == "running",
                "size": .5,
            }
            for n in p["nodes"]
        ]
        webgl_scene(scene, nodes, [tuple(e) for e in p["edges"]], height=570)

    else:
        nodes = [
            {"id": "spec", "label": "Specification", "size": .68},
            {"id": "label", "label": "Label", "size": .55},
            {"id": "ifus", "label": "IFU", "size": .55},
            {"id": "test", "label": "Test Evidence", "size": .60},
            {"id": "conflict", "label": "Conflict", "size": .78, "active": True},
        ]
        webgl_scene(
            scene,
            nodes,
            [("spec", "conflict"), ("label", "conflict"), ("ifus", "conflict"), ("test", "conflict")],
            height=570,
        )


# =============================================================================
# Settings & security
# =============================================================================

def page_settings() -> None:
    st.title(t("settings"))

    st.subheader("Language")
    language_label = st.selectbox(
        "UI language",
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.values()).index(st.session_state["language"]),
    )
    st.session_state["language"] = LANGUAGES[language_label]

    st.subheader("Theme")
    theme = st.selectbox(
        "Theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state["theme"])
        if st.session_state["theme"] in THEMES else 0,
    )
    st.session_state["theme"] = theme
    st.session_state["reduced_motion"] = st.checkbox(
        "Reduced motion",
        value=st.session_state.get("reduced_motion", False),
    )

    st.subheader("Model")
    st.session_state["global_model"] = st.selectbox(
        "Global default model",
        list(MODELS.keys()),
        index=list(MODELS.keys()).index(st.session_state["global_model"])
        if st.session_state["global_model"] in MODELS else 0,
    )

    st.subheader("Providers & secure session keys")
    st.caption("Environment variables take precedence over session-entered keys. Keys are never written to artifacts or logs.")

    for provider, cfg in PROVIDERS.items():
        status = provider_key_status(provider)
        cols = st.columns([1.2, 2.4, 1.2])
        with cols[0]:
            st.write(f"**{provider}**")
        with cols[1]:
            st.caption(
                "Environment configured"
                if status["environment"]
                else ("Session configured" if status["session"] else "Not configured")
            )
        with cols[2]:
            if status["configured"]:
                st.success("Ready", icon="●")
            else:
                st.warning("Fallback", icon="○")

        if not status["environment"]:
            st.session_state[cfg["session_key"]] = st.text_input(
                f"{provider} API key",
                value=st.session_state.get(cfg["session_key"], ""),
                type="password",
                key=f"key_input_{provider}",
            )

    st.session_state["active_provider"] = st.selectbox(
        "Active provider",
        list(PROVIDERS.keys()),
        index=list(PROVIDERS.keys()).index(st.session_state["active_provider"]),
    )

    st.divider()
    st.subheader("Workspace export / import")

    workspace = {
        "version": 1,
        "exported_at": now_iso(),
        "language": st.session_state["language"],
        "theme": st.session_state["theme"],
        "global_model": st.session_state["global_model"],
        "notes": st.session_state["notes"],
        "review": st.session_state["review"],
        "skills": st.session_state["skills"],
        "comparison": st.session_state["comparison"],
        "pipelines": st.session_state["pipelines"],
        "agent_yaml": st.session_state["agent_yaml"],
        "agent_skill_md": st.session_state["agent_skill_md"],
        "artifacts": st.session_state["artifacts"],
    }

    st.download_button(
        "Download workspace snapshot",
        data=json.dumps(workspace, ensure_ascii=False, indent=2),
        file_name="workbench_workspace.json",
        mime="application/json",
        use_container_width=True,
    )

    uploaded = st.file_uploader(
        "Import workspace snapshot",
        type=["json"],
        key="workspace_import",
    )
    if uploaded and st.button("Validate & import workspace", use_container_width=True):
        try:
            incoming = json.loads(uploaded.getvalue().decode("utf-8"))
            required = ["version", "notes", "skills", "pipelines", "artifacts"]
            missing = [k for k in required if k not in incoming]
            if missing:
                raise ValueError(f"Missing required workspace fields: {missing}")

            # Apply only known safe workspace fields.
            for key in [
                "language", "theme", "global_model", "notes", "review",
                "skills", "comparison", "pipelines", "agent_yaml",
                "agent_skill_md", "artifacts",
            ]:
                if key in incoming:
                    st.session_state[key] = incoming[key]

            add_log("Workspace snapshot imported.", "INFO", "workspace")
            set_flash("Workspace imported.")
            st.rerun()
        except Exception as exc:
            add_log(f"Workspace import rejected: {exc}", "ERROR", "workspace")
            st.error(f"Import rejected: {exc}")


# =============================================================================
# Router
# =============================================================================

def render_page() -> None:
    page = st.session_state.get("page", "home")
    if page == "home":
        page_home()
    elif page == "notes":
        page_notes()
    elif page == "review":
        page_review()
    elif page == "skills":
        page_skills()
    elif page == "pipeline":
        page_pipeline()
    elif page == "agents":
        page_agents()
    elif page == "results":
        page_results()
    elif page == "visuals":
        page_visuals()
    elif page == "settings":
        page_settings()
    else:
        st.session_state["page"] = "home"
        page_home()


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_state()
    inject_css()
    render_sidebar()
    render_topbar()
    render_flash()
    render_page()
    render_dashboard()


if __name__ == "__main__":
    main()
