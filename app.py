import os
import io
import json
import re
import time
import random
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

# Optional dependencies. The app remains runnable without them; AI features show
# a clear configuration message instead of crashing.
try:
    import yaml
except Exception:
    yaml = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


# ============================================================
# 0. PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Staged Medical Device Regulatory Review Bench",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 1. CONSTANTS / LOCALIZATION / THEMES
# ============================================================
APP_TITLE = "Staged Medical Device Regulatory Review Bench"
APP_VERSION = "2.0.0"

LOCALIZATIONS = {
    "繁體中文": {
        "title": "3D WebGL 醫療器材法規智慧審查工作臺",
        "subtitle": "五階段醫療器材法規審查、FDA 情報、IFU 規格擷取、送件文件對照與最終審查報告",
        "nav_constellation": "🪐 3D 證據星座",
        "nav_notes": "📝 AI 筆記本",
        "nav_bench": "⚖️ 審查工作臺",
        "nav_skill_studio": "🧪 技能工作室",
        "nav_pipeline": "🧬 流程工作室",
        "nav_agents": "🤖 Agent 檔案庫",
        "nav_wow_ai": "🚀 AI 工具集",
        "nav_results": "📁 結果檔案庫",
        "nav_settings": "⚙️ 系統設定",
    },
    "English": {
        "title": "3D WebGL Medical Device Regulatory Review Workbench",
        "subtitle": "Five-stage FDA intelligence, IFU extraction, submission mapping and review-report workflow",
        "nav_constellation": "🪐 3D Evidence Hub",
        "nav_notes": "📝 AI Note Keeper",
        "nav_bench": "⚖️ Review Bench",
        "nav_skill_studio": "🧪 Skill Studio",
        "nav_pipeline": "🧬 Pipeline Studio",
        "nav_agents": "🤖 Agent Studio",
        "nav_wow_ai": "🚀 AI Utilities",
        "nav_results": "📁 Results Library",
        "nav_settings": "⚙️ Settings",
    },
    "日本語": {
        "title": "3D WebGL 医療機器規制審査ワークベンチ",
        "subtitle": "FDA 情報、IFU 仕様抽出、提出資料対応表、審査質問・最終報告を統合",
        "nav_constellation": "🪐 3D 証拠ハブ",
        "nav_notes": "📝 AI ノート",
        "nav_bench": "⚖️ 審査ワークベンチ",
        "nav_skill_studio": "🧪 スキルスタジオ",
        "nav_pipeline": "🧬 パイプライン",
        "nav_agents": "🤖 エージェント",
        "nav_wow_ai": "🚀 AI ツール",
        "nav_results": "📁 結果ライブラリ",
        "nav_settings": "⚙️ 設定",
    },
}

PANTONE_THEMES = {
    "Coral Pulse": {"primary": "#FF6F61", "bg": "#171820", "card": "#232633", "text": "#F5F7FA"},
    "Jade Logic": {"primary": "#00A86B", "bg": "#101A16", "card": "#1B2923", "text": "#EFFAF4"},
    "Midnight Indigo": {"primary": "#7C5CFC", "bg": "#11101B", "card": "#211E32", "text": "#F2F0FF"},
    "Warm Sand": {"primary": "#D2B48C", "bg": "#1D1A17", "card": "#2A2520", "text": "#FAF7F1"},
    "Arctic Glass": {"primary": "#00A6A6", "bg": "#0D1A22", "card": "#182833", "text": "#EFFBFF"},
    "Ocean Signal": {"primary": "#1885D8", "bg": "#0A1624", "card": "#12263B", "text": "#EEF7FF"},
}


# ============================================================
# 2. SESSION STATE
# ============================================================
def init_state() -> None:
    defaults = {
        "initialized": True,
        "language": "繁體中文",
        "theme_name": "Coral Pulse",
        "theme_mode": "Dark",
        "active_model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "token_count": 0,
        "logs": [],
        "results": [],
        "notes": [],
        "skills": [],
        "pipelines": [],
        "agents": [],
        "bench": {
            "stage1_description": "",
            "stage1_result": "",
            "stage1_sources": [],
            "stage2_ifu_name": "",
            "stage2_ifu_text": "",
            "stage2_result": "",
            "stage2_specs": [],
            "stage2_accessories": [],
            "stage2_software": [],
            "stage3_doc_list": "",
            "stage3_result": "",
            "stage3_docs": [],
            "stage4_result": "",
            "stage5_questions": [],
            "stage5_feedback": "",
            "stage5_report": "",
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.logs:
        log_event("System initialized.")
        log_event(f"Model: {st.session_state.active_model}")
        log_event("Five-stage review bench ready.")

    if not st.session_state.skills:
        st.session_state.skills = [
            {
                "id": "SKILL-001",
                "name": "FDA Regulatory Intelligence",
                "model": st.session_state.active_model,
                "description": "Search and synthesize FDA public regulatory evidence.",
            },
            {
                "id": "SKILL-002",
                "name": "IFU Specification Extractor",
                "model": st.session_state.active_model,
                "description": "Extract device, accessory and software specifications from IFU.",
            },
            {
                "id": "SKILL-003",
                "name": "Submission Document Mapper",
                "model": st.session_state.active_model,
                "description": "Normalize a raw submission-document list into a review table.",
            },
        ]

    if not st.session_state.pipelines:
        st.session_state.pipelines = [
            {
                "id": "PIPE-001",
                "name": "Staged Medical Device Regulatory Review",
                "nodes": [
                    {"step": 1, "name": "FDA intelligence", "status": "Stage 1"},
                    {"step": 2, "name": "IFU extraction", "status": "Stage 2"},
                    {"step": 3, "name": "Document mapping", "status": "Stage 3"},
                    {"step": 4, "name": "Review guidance", "status": "Stage 4"},
                    {"step": 5, "name": "Questions and final report", "status": "Stage 5"},
                ],
            }
        ]

    if not st.session_state.agents:
        st.session_state.agents = [
            {
                "name": "Regulatory Audit Agent",
                "role": "Lead Reviewer",
                "model": st.session_state.active_model,
                "scope": "Stages 1-5",
            }
        ]


def log_event(message: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{stamp}] {message}")
    st.session_state.logs = st.session_state.logs[-30:]


init_state()

L10N = LOCALIZATIONS[st.session_state.language]
THEME = PANTONE_THEMES[st.session_state.theme_name]


# ============================================================
# 3. GENERAL HELPERS
# ============================================================
def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def add_result(title: str, body: str) -> None:
    st.session_state.results.insert(
        0,
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "body": body,
        },
    )
    st.session_state.results = st.session_state.results[:30]


def extract_json_object(text: str) -> Optional[Any]:
    """Best-effort extraction of JSON from a Gemini response."""
    if not text:
        return None
    candidates = [text.strip()]
    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.I | re.S)
    candidates.extend(fenced)
    for candidate in candidates:
        candidate = candidate.strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass
        start_obj = candidate.find("{")
        end_obj = candidate.rfind("}")
        if start_obj >= 0 and end_obj > start_obj:
            try:
                return json.loads(candidate[start_obj : end_obj + 1])
            except Exception:
                pass
        start_arr = candidate.find("[")
        end_arr = candidate.rfind("]")
        if start_arr >= 0 and end_arr > start_arr:
            try:
                return json.loads(candidate[start_arr : end_arr + 1])
            except Exception:
                pass
    return None


def extract_urls(text: str) -> List[str]:
    urls = re.findall(r"https?://[^\s\]\)<>\"']+", text or "")
    return list(dict.fromkeys(urls))


def get_gemini_client():
    key = clean_text(st.session_state.api_key)
    if not key:
        return None
    if genai is None:
        raise RuntimeError(
            "未安裝 google-genai。請在 requirements.txt 加入 google-genai。"
        )
    return genai.Client(api_key=key)


def call_gemini(
    prompt: str,
    *,
    system_instruction: str = "",
    use_web: bool = False,
    temperature: float = 0.2,
    max_output_tokens: int = 12000,
) -> Tuple[str, List[str]]:
    """
    Gemini call wrapper.
    When use_web=True, Gemini is instructed to use Google Search grounding.
    The exact SDK surface is isolated here so future SDK changes are easy to fix.
    """
    client = get_gemini_client()
    if client is None:
        raise RuntimeError("尚未設定 GEMINI_API_KEY。請到左側設定 API Key。")
    if types is None:
        raise RuntimeError("google-genai 套件版本不完整，請重新安裝 google-genai。")

    tools = []
    if use_web:
        try:
            tools = [types.Tool(google_search=types.GoogleSearch())]
        except Exception as exc:
            raise RuntimeError(
                f"目前 google-genai 版本不支援 Google Search grounding：{exc}"
            )

    config_kwargs = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if tools:
        config_kwargs["tools"] = tools

    response = client.models.generate_content(
        model=st.session_state.active_model,
        contents=prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    )

    text = getattr(response, "text", "") or ""
    if not text:
        raise RuntimeError("模型沒有回傳可讀取的文字結果。")

    # SDK versions differ in how grounding metadata is exposed. URLs in the
    # generated response are still preserved as a useful fallback.
    urls = extract_urls(text)
    try:
        st.session_state.token_count += int(
            getattr(getattr(response, "usage_metadata", None), "total_token_count", 0) or 0
        )
    except Exception:
        pass

    return text, urls


def require_input(value: str, label: str) -> bool:
    if not clean_text(value):
        st.warning(f"請先提供：{label}")
        return False
    return True


def render_markdown_table(rows: List[Dict[str, Any]], columns: List[str]) -> None:
    if not rows:
        st.info("目前沒有可顯示的資料。")
        return
    safe_rows = []
    for row in rows:
        safe_rows.append({c: row.get(c, "") for c in columns})
    st.dataframe(safe_rows, use_container_width=True, hide_index=True)


def parse_ifu_file(uploaded_file) -> Tuple[str, str]:
    """
    Supports PDF/TXT/MD/DOCX when the corresponding lightweight parser exists.
    DOCX parsing is done without requiring python-docx at import time.
    """
    name = uploaded_file.name
    data = uploaded_file.getvalue()
    suffix = name.lower().rsplit(".", 1)[-1] if "." in name else ""

    if suffix == "pdf":
        if PdfReader is None:
            raise RuntimeError("PDF 解析需要 pypdf，請在 requirements.txt 加入 pypdf。")
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return name, "\n\n".join(pages)

    if suffix in {"txt", "md", "csv"}:
        return name, data.decode("utf-8", errors="ignore")

    if suffix == "docx":
        try:
            from docx import Document
        except Exception:
            raise RuntimeError("DOCX 解析需要 python-docx，請在 requirements.txt 加入 python-docx。")
        doc = Document(io.BytesIO(data))
        return name, "\n".join(p.text for p in doc.paragraphs)

    raise RuntimeError("目前支援 PDF、TXT、MD、CSV、DOCX。")


def stage_badge(stage_num: int, label: str, done: bool = False) -> str:
    state = "完成" if done else "待執行"
    return (
        f"<div style='padding:10px 12px;border-radius:10px;"
        f"border:1px solid {THEME['primary']};margin-bottom:8px;'>"
        f"<b>Stage {stage_num}</b> · {label}<br>"
        f"<span style='opacity:.8'>{state}</span></div>"
    )


# ============================================================
# 4. PROMPTS — CENTRALIZED AND VERSIONED
# ============================================================
SYSTEM_REVIEW = """
你是醫療器材法規文件審查 AI 助理。你的工作是協助專業審查人員整理、比對與研究公開法規資料。
你不是主管機關，也不能取代正式法規判定。不得捏造法規、FDA 文件編號、產品代碼、510(k) 編號、
標準版本、核准狀態或試驗結果。若證據不足，明確寫「資料不足／需人工確認」。
所有時間敏感或法規相關結論應以可追溯來源支持。對於使用者提供的文件，必須區分「文件明載」
與「AI 推論／待確認事項」。輸出使用繁體中文。
"""

STAGE1_PROMPT = """
任務：建立「Stage 1 — FDA Regulatory Intelligence Memo」，目標約 4,500 個中文字。
使用者提供的是醫療器材描述。請使用 Google Search grounding 搜尋 FDA 官方及其他高可信公開來源。

研究優先順序：
1. FDA 510(k) database / 510(k) Summary；
2. FDA product classification、Product Classification、regulation number、product code；
3. FDA guidance、special controls、recognized consensus standards（僅在與裝置直接相關時）；
4. FDA recall / safety communication / labeling / public device information；
5. 必要時引用其他權威公開來源，但清楚標示來源性質。

請產生以下章節：
# FDA Regulatory Intelligence Memo
## 1. Executive Summary
## 2. Device identity and intended use signals
## 3. FDA classification / regulation / product code evidence
## 4. 510(k) landscape and potentially relevant predicates
## 5. Relevant FDA guidance and standards
## 6. Safety / labeling / software / cybersecurity considerations
## 7. Key regulatory risks and information gaps
## 8. Recommended evidence to verify
## 9. Source register

對 predicate 的描述只能是「可能相關候選」，不得在沒有足夠證據時宣稱 substantial equivalence。
每一個重要外部事實盡量提供來源名稱、頁面標題、URL 或 FDA database 查詢線索。
若搜尋結果互相衝突，列出衝突並要求人工核對。
"""

STAGE2_PROMPT = """
任務：從使用者上傳的 IFU（Instructions for Use）中建立結構化裝置規格摘要。
只能根據 IFU 內容；如果 IFU 沒有資料，填「IFU 未載明」，不要自行補值。

輸出 JSON，格式必須是：
{
  "device_summary": "繁體中文摘要",
  "specs": [
    {"title":"", "spec":"", "comments":""}
  ],
  "accessories": [
    {"title":"", "spec":"", "comments":""}
  ],
  "software": [
    {"title":"", "brief_spec":"", "ai_related":"是/否/不明", "comments":""}
  ],
  "safety_and_labeling_notes": [],
  "source_notes": []
}

specs 應涵蓋 IFU 中的重要主機、硬體、尺寸、電源、操作範圍、性能、適用部位、
環境條件、滅菌/清潔、使用限制等。
accessories 應包含探頭、探針、線材、套件、腳踏、支架等 IFU 明載附件。
software 應列出主要軟體功能；若有 AI、machine learning、deep learning、segmentation、
registration、classification、detection 等字樣，ai_related 應依 IFU 證據判定；沒有明確證據則「不明」。
"""

STAGE3_PROMPT = """
任務：把使用者貼上的「送件文件清單」重新整理成適合醫療器材審查的對照總表。
不得創造原始清單中不存在的文件名稱；若可合理判斷分類，分類應以文件本身與一般審查結構為依據，
但任何推論分類請在 comments 標示「AI 分類，待確認」。

輸出 JSON：
{
  "documents": [
    {
      "title": "文件角色/主題",
      "category": "文件類別",
      "doc_name": "原始文件名稱",
      "comments": "審查備註"
    }
  ],
  "gaps": [],
  "normalization_notes": []
}

分類可使用：行政/申請、裝置描述、原理與規格、風險管理、性能/bench testing、
電氣安全/EMC、生物相容性、軟體/AI、臨床、標示/IFU、滅菌/清潔、製造/品質、
上市後/其他；若不適用可建立更合適分類。
"""

STAGE4_PROMPT = """
任務：根據 Stage 1 FDA Regulatory Intelligence Memo、Stage 2 IFU specification summary、
Stage 3 submission-document mapping，建立「Stage 4 — Comprehensive Review Guidance」。

同時研究並納入台灣公開法規資料，尤其是「醫療器材許可證核發與登錄及年度申報準則」。
請優先搜尋台灣衛生福利部食品藥物管理署（TFDA）及全國法規資料庫等官方來源。
若法規名稱、條文或現行版本無法確認，必須標示「需人工確認」，不得猜測。

輸出繁體中文 Markdown，至少包含：
# 綜合審查指引
## A. Review scope and evidence boundary
## B. Stage 1–3 integrated findings
## C. Required document review matrix
表格欄位至少：Required Document / 對應 Stage 證據 / 10 Key Review Points / Review Evidence / Gap / Action
其中「10 Key Review Points」要有恰好 10 個明確審查點，涵蓋：
1 intended use
2 indications / contraindications
3 classification and regulatory pathway
4 device specifications
5 accessories
6 software / AI
7 performance and safety
8 labeling / IFU consistency
9 risk management / post-market considerations
10 Taiwan submission and annual-reporting obligations
## D. Cross-document consistency checks
## E. High-priority gaps
## F. Reviewer workflow
## G. Taiwan regulatory references
## H. Source register

不要把 AI 產生的「建議」寫成主管機關正式要求。
"""

STAGE5_PROMPT = """
任務：根據 Stage 1–4 的結果建立「30 題綜合醫療器材法規審查問題與答案」。
所有問題都必須能追溯到 Stage 1–4 的證據或明確的法規查詢事項。
答案使用繁體中文，若資料不足要明確回答「資料不足／需補件或人工確認」，不要猜。

輸出 JSON：
{
  "questions": [
    {
      "id": 1,
      "category": "",
      "question": "",
      "answer": "",
      "evidence": "",
      "reviewer_focus": ""
    }
  ]
}
必須恰好 30 題，涵蓋 FDA intelligence、device specs、accessories、software/AI、
submission documents、Taiwan requirements、labeling、risk/performance、cross-document consistency。
"""

FINAL_REPORT_PROMPT = """
任務：撰寫「醫療器材法規綜合審查報告」，約 5,000–6,000 個中文字。
根據 Stage 1–5 所有材料及使用者對 30 題問題的回饋。
不要把 AI 意見寫成主管機關正式決定。所有重大缺口要標示證據來源或「待確認」。

請使用繁體中文 Markdown，至少包含：
# 醫療器材法規綜合審查報告
## 1. 審查目的與範圍
## 2. 裝置識別與用途
## 3. FDA Regulatory Intelligence
## 4. IFU 與裝置規格審查
## 5. 附件與耗材審查
## 6. 軟體與 AI 功能審查
## 7. 送件文件完整性與一致性
## 8. 台灣法規與「醫療器材許可證核發與登錄及年度申報準則」相關檢核
## 9. 風險、性能、安全與標示審查
## 10. 30 題問答與 reviewer feedback 影響
## 11. 主要缺口與待補資料
## 12. 建議的後續審查工作
## 13. Evidence / source register
## 14. Limitations and human-review points

不得自行創造測試結果、法規條文、FDA 核准狀態、產品代碼或申請號碼。
"""


# ============================================================
# 5. STAGE FUNCTIONS
# ============================================================
def run_stage1() -> None:
    description = st.session_state.bench["stage1_description"]
    if not require_input(description, "裝置描述"):
        return

    prompt = STAGE1_PROMPT + "\n\nUSER DEVICE DESCRIPTION:\n" + description
    with st.spinner("正在進行 FDA 公開資料搜尋與法規情報整理…"):
        result, urls = call_gemini(
            prompt,
            system_instruction=SYSTEM_REVIEW,
            use_web=True,
            temperature=0.15,
            max_output_tokens=16000,
        )

    st.session_state.bench["stage1_result"] = result
    st.session_state.bench["stage1_sources"] = urls
    add_result("Stage 1 — FDA Regulatory Intelligence Memo", result)
    log_event("Stage 1 completed with web-grounded research.")
    st.success("Stage 1 完成。")


def run_stage2() -> None:
    text = st.session_state.bench["stage2_ifu_text"]
    if not require_input(text, "IFU 內容"):
        return

    # Avoid accidental context explosions. Keep enough text for long IFUs while
    # clearly warning the reviewer when truncation occurs.
    max_chars = 120_000
    truncated = len(text) > max_chars
    source_text = text[:max_chars]
    if truncated:
        source_text += "\n\n[注意：IFU 超過模型輸入保護上限，後段文字未送入模型。]"

    prompt = STAGE2_PROMPT + f"\n\nIFU FILE: {st.session_state.bench['stage2_ifu_name']}\n\nIFU TEXT:\n{source_text}"
    with st.spinner("正在解析 IFU 並建立裝置、附件與軟體規格表…"):
        raw, _ = call_gemini(
            prompt,
            system_instruction=SYSTEM_REVIEW,
            use_web=False,
            temperature=0.1,
            max_output_tokens=12000,
        )

    parsed = extract_json_object(raw)
    if not isinstance(parsed, dict):
        # Preserve raw output so the reviewer can inspect it rather than losing it.
        parsed = {
            "device_summary": raw,
            "specs": [],
            "accessories": [],
            "software": [],
            "safety_and_labeling_notes": [],
            "source_notes": ["模型沒有回傳可解析 JSON；以上為原始模型輸出。"],
        }

    b = st.session_state.bench
    b["stage2_result"] = safe_json(parsed)
    b["stage2_specs"] = parsed.get("specs", []) or []
    b["stage2_accessories"] = parsed.get("accessories", []) or []
    b["stage2_software"] = parsed.get("software", []) or []

    add_result("Stage 2 — IFU Specification Summary", b["stage2_result"])
    log_event(f"Stage 2 completed: {st.session_state.bench['stage2_ifu_name']}")
    if truncated:
        st.warning("IFU 太長，已套用輸入長度保護；請考慮分段處理或提高模型輸入上限。")
    st.success("Stage 2 完成。")


def run_stage3() -> None:
    doc_list = st.session_state.bench["stage3_doc_list"]
    if not require_input(doc_list, "送件文件清單"):
        return

    prompt = STAGE3_PROMPT + "\n\nRAW SUBMISSION DOCUMENT LIST:\n" + doc_list
    with st.spinner("正在整理送件文件並建立對照總表…"):
        raw, _ = call_gemini(
            prompt,
            system_instruction=SYSTEM_REVIEW,
            use_web=False,
            temperature=0.1,
            max_output_tokens=10000,
        )

    parsed = extract_json_object(raw)
    if not isinstance(parsed, dict):
        parsed = {
            "documents": [],
            "gaps": [],
            "normalization_notes": ["模型沒有回傳可解析 JSON。原始輸出已保留。"],
            "raw_output": raw,
        }

    st.session_state.bench["stage3_result"] = safe_json(parsed)
    st.session_state.bench["stage3_docs"] = parsed.get("documents", []) or []
    add_result("Stage 3 — Submission Document Mapping", st.session_state.bench["stage3_result"])
    log_event("Stage 3 completed.")
    st.success("Stage 3 完成。")


def build_stage_context() -> str:
    b = st.session_state.bench
    return f"""
=== STAGE 1 ===
{b['stage1_result']}

=== STAGE 2 ===
{b['stage2_result']}

=== STAGE 3 ===
{b['stage3_result']}
"""


def run_stage4() -> None:
    if not require_input(st.session_state.bench["stage1_result"], "Stage 1 結果"):
        return
    if not require_input(st.session_state.bench["stage2_result"], "Stage 2 結果"):
        return
    if not require_input(st.session_state.bench["stage3_result"], "Stage 3 結果"):
        return

    prompt = STAGE4_PROMPT + "\n\n" + build_stage_context()
    with st.spinner("正在研究 FDA / TFDA 公開法規資料並建立綜合審查指引…"):
        result, urls = call_gemini(
            prompt,
            system_instruction=SYSTEM_REVIEW,
            use_web=True,
            temperature=0.15,
            max_output_tokens=18000,
        )

    if urls:
        result += "\n\n## Web sources detected by model\n" + "\n".join(f"- {u}" for u in urls)

    st.session_state.bench["stage4_result"] = result
    add_result("Stage 4 — Comprehensive Review Guidance", result)
    log_event("Stage 4 completed with FDA/TFDA web research.")
    st.success("Stage 4 完成。")


def run_stage5_questions() -> None:
    b = st.session_state.bench
    for label, key in [
        ("Stage 1", "stage1_result"),
        ("Stage 2", "stage2_result"),
        ("Stage 3", "stage3_result"),
        ("Stage 4", "stage4_result"),
    ]:
        if not require_input(b[key], label):
            return

    prompt = STAGE5_PROMPT + "\n\n=== STAGE 1–4 CONTEXT ===\n" + (
        f"\nSTAGE 1:\n{b['stage1_result']}\n"
        f"\nSTAGE 2:\n{b['stage2_result']}\n"
        f"\nSTAGE 3:\n{b['stage3_result']}\n"
        f"\nSTAGE 4:\n{b['stage4_result']}\n"
    )

    with st.spinner("正在建立 30 題綜合審查問題與答案…"):
        raw, _ = call_gemini(
            prompt,
            system_instruction=SYSTEM_REVIEW,
            use_web=False,
            temperature=0.1,
            max_output_tokens=18000,
        )

    parsed = extract_json_object(raw)
    questions = parsed.get("questions", []) if isinstance(parsed, dict) else []
    if len(questions) != 30:
        st.warning(f"模型目前回傳 {len(questions)} 題；系統會保留原始結果，請檢查後再產生報告。")
    b["stage5_questions"] = questions if questions else [{"id": 0, "category": "Raw", "question": "模型原始輸出", "answer": raw, "evidence": "", "reviewer_focus": ""}]
    log_event(f"Stage 5 generated {len(b['stage5_questions'])} questions.")
    st.success("30 題審查問答產生完成。")


def run_final_report() -> None:
    b = st.session_state.bench
    if not b["stage5_questions"]:
        st.warning("請先產生 Stage 5 的 30 題問題與答案。")
        return

    feedback = b["stage5_feedback"].strip() or "Reviewer 未提供額外 feedback。"
    prompt = (
        FINAL_REPORT_PROMPT
        + "\n\n=== STAGE 1 ===\n" + b["stage1_result"]
        + "\n\n=== STAGE 2 ===\n" + b["stage2_result"]
        + "\n\n=== STAGE 3 ===\n" + b["stage3_result"]
        + "\n\n=== STAGE 4 ===\n" + b["stage4_result"]
        + "\n\n=== STAGE 5 QUESTIONS ===\n" + safe_json(b["stage5_questions"])
        + "\n\n=== REVIEWER FEEDBACK ===\n" + feedback
    )

    with st.spinner("正在撰寫 5,000–6,000 字繁體中文綜合審查報告…"):
        result, _ = call_gemini(
            prompt,
            system_instruction=SYSTEM_REVIEW,
            use_web=False,
            temperature=0.15,
            max_output_tokens=24000,
        )

    b["stage5_report"] = result
    add_result("Stage 5 — Comprehensive Review Report", result)
    log_event("Final review report completed.")
    st.success("最終審查報告完成。")


# ============================================================
# 6. CSS / SIDEBAR
# ============================================================
mode_bg = THEME["bg"] if st.session_state.theme_mode == "Dark" else "#F7F8FA"
mode_text = THEME["text"] if st.session_state.theme_mode == "Dark" else "#1B1F24"
card_bg = THEME["card"] if st.session_state.theme_mode == "Dark" else "#FFFFFF"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {mode_bg};
        color: {mode_text};
    }}
    [data-testid="stSidebar"] {{
        background: {card_bg};
    }}
    .review-card {{
        border: 1px solid {THEME['primary']};
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
        background: rgba(255,255,255,.03);
    }}
    .stage-title {{
        color: {THEME['primary']};
        font-weight: 800;
        font-size: 1.1rem;
    }}
    .small-muted {{
        opacity: .72;
        font-size: .85rem;
    }}
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid {THEME['primary']};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("🎛️ Control Panel")

    st.session_state.language = st.selectbox(
        "🌐 Language / 語言",
        ["繁體中文", "English", "日本語"],
        index=["繁體中文", "English", "日本語"].index(st.session_state.language),
    )
    # Refresh localization after language change.
    L10N = LOCALIZATIONS[st.session_state.language]

    model_options = [
        "gemini-3.5-flash-lite",
        "gemma-4-31b-it",
        "gemma-4-26b-14b-it",
    ]
    current_model = st.session_state.active_model
    if current_model not in model_options:
        model_options.insert(0, current_model)

    selected_model = st.selectbox(
        "🤖 Gemini Model",
        model_options,
        index=model_options.index(current_model),
        help="請使用你有權限存取的 Gemini model ID。",
    )
    st.session_state.active_model = selected_model

    user_key = st.text_input(
        "🔑 Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="建議在 Hugging Face Spaces Secrets 設定 GEMINI_API_KEY，而不是硬編碼。",
    )
    if user_key != st.session_state.api_key:
        st.session_state.api_key = user_key
        log_event("API key updated.")

    st.divider()
    st.subheader("🎨 Theme")
    st.session_state.theme_name = st.selectbox(
        "Pantone Palette",
        list(PANTONE_THEMES.keys()),
        index=list(PANTONE_THEMES.keys()).index(st.session_state.theme_name),
    )
    st.session_state.theme_mode = st.radio(
        "Mode", ["Dark", "Light"], index=["Dark", "Light"].index(st.session_state.theme_mode), horizontal=True
    )

    st.divider()
    nav_items = [
        L10N["nav_constellation"],
        L10N["nav_notes"],
        L10N["nav_bench"],
        L10N["nav_skill_studio"],
        L10N["nav_pipeline"],
        L10N["nav_agents"],
        L10N["nav_wow_ai"],
        L10N["nav_results"],
        L10N["nav_settings"],
    ]
    nav_choice = st.radio("Navigation", nav_items, index=2)

    st.divider()
    st.caption(f"Version {APP_VERSION}")
    st.caption(f"Token count: {st.session_state.token_count:,}")


# ============================================================
# 7. HEADER
# ============================================================
st.title(L10N["title"])
st.caption(L10N["subtitle"])

b = st.session_state.bench
completion = {
    "Stage 1": bool(b["stage1_result"]),
    "Stage 2": bool(b["stage2_result"]),
    "Stage 3": bool(b["stage3_result"]),
    "Stage 4": bool(b["stage4_result"]),
    "Stage 5": bool(b["stage5_report"]),
}
completed_count = sum(completion.values())
st.progress(completed_count / 5, text=f"審查流程進度：{completed_count}/5")


# ============================================================
# 8. MODULE: 3D CONSTELLATION
# ============================================================
if nav_choice == L10N["nav_constellation"]:
    st.subheader("🪐 3D WebGL Evidence Constellation")
    st.write("以 Stage 1–5 審查證據建立互動式視覺化。此區只做 dossier 導覽，不取代文字證據。")

    webgl_code = f"""
    <!doctype html>
    <html>
    <head>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
      <style>
        body {{ margin:0; overflow:hidden; background:{THEME['bg']}; }}
        canvas {{ display:block; width:100%; height:430px; }}
      </style>
    </head>
    <body>
    <script>
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(70, window.innerWidth/430, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({{antialias:true, alpha:true}});
      renderer.setSize(window.innerWidth,430);
      document.body.appendChild(renderer.domElement);

      const nodes = [];
      const colors = [0xFF6F61, 0x00A86B, 0x1885D8, 0x7C5CFC, 0xD2B48C];
      const labels = ["Stage 1","Stage 2","Stage 3","Stage 4","Stage 5"];

      for (let i=0;i<5;i++) {{
        const geometry = new THREE.SphereGeometry(0.55, 28, 28);
        const material = new THREE.MeshBasicMaterial({{color:colors[i], wireframe:i===0}});
        const node = new THREE.Mesh(geometry, material);
        const a = (i/5)*Math.PI*2;
        node.position.set(Math.cos(a)*3, Math.sin(a)*1.8, Math.sin(a)*2);
        scene.add(node);
        nodes.push(node);
      }}

      const points = nodes.map(n => n.position);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points.concat([points[0]]));
      const lineMat = new THREE.LineBasicMaterial({{color:0xFFFFFF,opacity:.35,transparent:true}});
      scene.add(new THREE.Line(lineGeo,lineMat));

      camera.position.z=8;
      function animate() {{
        requestAnimationFrame(animate);
        nodes.forEach((n,i)=>{{n.rotation.x+=.008+i*.001;n.rotation.y+=.01;}});
        scene.rotation.y+=.0025;
        renderer.render(scene,camera);
      }}
      animate();
      window.addEventListener("resize",()=>{{
        camera.aspect=window.innerWidth/430;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth,430);
      }});
    </script>
    </body>
    </html>
    """
    components.html(webgl_code, height=450)

    st.dataframe(
        [
            {"Stage": "1", "Evidence": "FDA regulatory intelligence", "Status": "完成" if completion["Stage 1"] else "待執行"},
            {"Stage": "2", "Evidence": "IFU device / accessories / software", "Status": "完成" if completion["Stage 2"] else "待執行"},
            {"Stage": "3", "Evidence": "Submission document mapping", "Status": "完成" if completion["Stage 3"] else "待執行"},
            {"Stage": "4", "Evidence": "Comprehensive review guidance", "Status": "完成" if completion["Stage 4"] else "待執行"},
            {"Stage": "5", "Evidence": "30 questions + final report", "Status": "完成" if completion["Stage 5"] else "待執行"},
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 9. MODULE: NOTE KEEPER
# ============================================================
elif nav_choice == L10N["nav_notes"]:
    st.subheader("📝 AI Note Keeper")
    left, right = st.columns([1, 2])

    with left:
        uploaded = st.file_uploader("Upload notes", type=["txt", "md", "csv"])
        if uploaded:
            text = uploaded.getvalue().decode("utf-8", errors="ignore")
            if st.button("➕ Add Note", key="add_note"):
                st.session_state.notes.append(
                    {"id": f"NOTE-{len(st.session_state.notes)+1:03d}", "title": uploaded.name, "content": text}
                )
                st.success("Note added.")

        st.write("### Saved notes")
        if st.session_state.notes:
            idx = st.selectbox(
                "Select",
                range(len(st.session_state.notes)),
                format_func=lambda i: st.session_state.notes[i]["title"],
            )
        else:
            idx = None
            st.info("尚無筆記。")

    with right:
        if idx is not None:
            note = st.session_state.notes[idx]
            title = st.text_input("Title", note["title"])
            content = st.text_area("Content", note["content"], height=360)
            if st.button("💾 Save Note", key="save_note"):
                note["title"] = title
                note["content"] = content
                st.success("Saved.")
        else:
            st.info("上傳 TXT/MD 後可建立筆記。")


# ============================================================
# 10. MODULE: FIVE-STAGE REVIEW BENCH
# ============================================================
elif nav_choice == L10N["nav_bench"]:
    st.subheader("⚖️ Staged Medical Device Regulatory Review Bench")
    st.caption("建議工作順序：Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5。每一階段結果會留在 session state。")

    tabs = st.tabs([
        "1️⃣ FDA Intelligence",
        "2️⃣ IFU Specs",
        "3️⃣ Submission Docs",
        "4️⃣ Review Guidance",
        "5️⃣ Q&A + Final Report",
    ])

    # ---------------- Stage 1 ----------------
    with tabs[0]:
        st.markdown(stage_badge(1, "FDA Regulatory Intelligence Memo", completion["Stage 1"]), unsafe_allow_html=True)
        st.markdown("### 裝置描述")
        st.session_state.bench["stage1_description"] = st.text_area(
            "請貼上 device description / intended use / indication / technology description",
            value=b["stage1_description"],
            height=220,
            placeholder="例如：裝置名稱、預期用途、使用者、病患族群、主要硬體、軟體、AI 功能、附件、工作原理……",
            key="stage1_description_widget",
        )

        c1, c2 = st.columns([1, 3])
        with c1:
            run1 = st.button("🔎 執行 Stage 1 Web Search", type="primary", key="run_stage1")
        with c2:
            st.info("搜尋重點：FDA 510(k) Summary、classification、product code、guidance、standards、labeling、recall 等。")

        if run1:
            try:
                run_stage1()
            except Exception as exc:
                st.error(f"Stage 1 失敗：{exc}")
                log_event(f"Stage 1 error: {exc}")

        if b["stage1_result"]:
            st.markdown("### 📄 FDA Regulatory Intelligence Memo")
            st.markdown(b["stage1_result"])
            if b["stage1_sources"]:
                st.markdown("### 🔗 Detected source URLs")
                for url in b["stage1_sources"]:
                    st.markdown(f"- {url}")
            st.download_button(
                "📥 Download Stage 1 Markdown",
                data=b["stage1_result"],
                file_name="stage1_fda_regulatory_intelligence.md",
                mime="text/markdown",
                key="dl_stage1",
            )

    # ---------------- Stage 2 ----------------
    with tabs[1]:
        st.markdown(stage_badge(2, "IFU Device Specification Summary", completion["Stage 2"]), unsafe_allow_html=True)
        st.write("上傳 IFU 後，AI 會整理：①主要裝置規格 ②附件/探頭 ③主要軟體功能與 AI 判定。")

        uploaded_ifu = st.file_uploader(
            "📤 Upload IFU",
            type=["pdf", "txt", "md", "csv", "docx"],
            key="ifu_uploader",
        )
        if uploaded_ifu:
            try:
                name, text = parse_ifu_file(uploaded_ifu)
                st.session_state.bench["stage2_ifu_name"] = name
                st.session_state.bench["stage2_ifu_text"] = text
                st.success(f"已讀取 {name}，約 {len(text):,} 字元。")
                with st.expander("Preview extracted IFU text"):
                    st.text(text[:8000])
            except Exception as exc:
                st.error(f"IFU 讀取失敗：{exc}")

        if b["stage2_ifu_text"]:
            if st.button("🧩 建立 IFU 規格摘要", type="primary", key="run_stage2"):
                try:
                    run_stage2()
                except Exception as exc:
                    st.error(f"Stage 2 失敗：{exc}")
                    log_event(f"Stage 2 error: {exc}")

        if b["stage2_result"]:
            try:
                parsed2 = json.loads(b["stage2_result"])
            except Exception:
                parsed2 = {}

            st.markdown("### 裝置規格摘要")
            st.write(parsed2.get("device_summary", ""))

            st.markdown("### 📐 主要裝置規格")
            render_markdown_table(
                b["stage2_specs"],
                ["title", "spec", "comments"],
            )

            st.markdown("### 🔌 Accessories / Probes")
            render_markdown_table(
                b["stage2_accessories"],
                ["title", "spec", "comments"],
            )

            st.markdown("### 💻 主要軟體功能")
            render_markdown_table(
                b["stage2_software"],
                ["title", "brief_spec", "ai_related", "comments"],
            )

            st.download_button(
                "📥 Download Stage 2 JSON",
                data=b["stage2_result"],
                file_name="stage2_ifu_specification_summary.json",
                mime="application/json",
                key="dl_stage2",
            )

    # ---------------- Stage 3 ----------------
    with tabs[2]:
        st.markdown(stage_badge(3, "送件文件對照總表", completion["Stage 3"]), unsafe_allow_html=True)
        b["stage3_doc_list"] = st.text_area(
            "請貼上送件文件清單",
            value=b["stage3_doc_list"],
            height=300,
            placeholder="一行一份文件，例如：\n申請書\n產品技術規格\n風險管理報告\n軟體驗證報告\n臨床評估報告\nIFU\n標籤……",
            key="stage3_doc_list_widget",
        )

        if st.button("🗂️ 重新整理送件文件", type="primary", key="run_stage3"):
            try:
                run_stage3()
            except Exception as exc:
                st.error(f"Stage 3 失敗：{exc}")
                log_event(f"Stage 3 error: {exc}")

        if b["stage3_result"]:
            try:
                parsed3 = json.loads(b["stage3_result"])
            except Exception:
                parsed3 = {}

            st.markdown("### 📋 送件文件對照總表")
            render_markdown_table(
                b["stage3_docs"],
                ["title", "category", "doc_name", "comments"],
            )

            gaps = parsed3.get("gaps", [])
            if gaps:
                st.markdown("### ⚠️ AI identified gaps")
                for item in gaps:
                    st.warning(str(item))

            st.download_button(
                "📥 Download Stage 3 JSON",
                data=b["stage3_result"],
                file_name="stage3_submission_document_mapping.json",
                mime="application/json",
                key="dl_stage3",
            )

    # ---------------- Stage 4 ----------------
    with tabs[3]:
        st.markdown(stage_badge(4, "Comprehensive Review Guidance", completion["Stage 4"]), unsafe_allow_html=True)
        st.info("Stage 4 會綜合 Stage 1–3，並搜尋 FDA / TFDA 公開資料，特別檢查「醫療器材許可證核發與登錄及年度申報準則」。")

        ready4 = all(
            [
                bool(b["stage1_result"]),
                bool(b["stage2_result"]),
                bool(b["stage3_result"]),
            ]
        )
        if not ready4:
            st.warning("請先完成 Stage 1、Stage 2、Stage 3。")

        if st.button("📚 建立綜合審查指引", type="primary", disabled=not ready4, key="run_stage4"):
            try:
                run_stage4()
            except Exception as exc:
                st.error(f"Stage 4 失敗：{exc}")
                log_event(f"Stage 4 error: {exc}")

        if b["stage4_result"]:
            st.markdown(b["stage4_result"])
            st.download_button(
                "📥 Download Stage 4 Markdown",
                data=b["stage4_result"],
                file_name="stage4_comprehensive_review_guidance.md",
                mime="text/markdown",
                key="dl_stage4",
            )

    # ---------------- Stage 5 ----------------
    with tabs[4]:
        st.markdown(stage_badge(5, "30 Questions + Reviewer Feedback + Final Report", completion["Stage 5"]), unsafe_allow_html=True)

        ready5 = bool(b["stage4_result"])
        if st.button("❓ 產生 30 題綜合審查問題與答案", type="primary", disabled=not ready5, key="run_questions"):
            try:
                run_stage5_questions()
            except Exception as exc:
                st.error(f"Stage 5 問題產生失敗：{exc}")
                log_event(f"Stage 5 question error: {exc}")

        if b["stage5_questions"]:
            st.markdown("### 30 題綜合審查問題")
            for i, q in enumerate(b["stage5_questions"], 1):
                qid = q.get("id", i)
                st.markdown(f"#### Q{qid}. {q.get('question', '')}")
                st.write(f"**分類：** {q.get('category', '')}")
                st.write(f"**答案：** {q.get('answer', '')}")
                if q.get("evidence"):
                    st.caption(f"Evidence: {q.get('evidence')}")
                if q.get("reviewer_focus"):
                    st.caption(f"Reviewer focus: {q.get('reviewer_focus')}")

            st.markdown("### 📝 Reviewer Feedback（可選）")
            b["stage5_feedback"] = st.text_area(
                "請針對答案提供修正、補充、不同意見或要求重新核對的項目",
                value=b["stage5_feedback"],
                height=220,
                placeholder="例如：Q7 的附件名稱應以 IFU Rev. C 為準；Q18 請重新確認 FDA product code；……",
                key="stage5_feedback_widget",
            )

            if st.button("📑 產生 5,000–6,000 字綜合審查報告", type="primary", key="run_final"):
                try:
                    run_final_report()
                except Exception as exc:
                    st.error(f"最終報告產生失敗：{exc}")
                    log_event(f"Final report error: {exc}")

        if b["stage5_report"]:
            st.markdown("---")
            st.markdown("## 📘 綜合審查報告")
            st.markdown(b["stage5_report"])
            st.download_button(
                "📥 Download Final Review Report",
                data=b["stage5_report"],
                file_name="stage5_comprehensive_review_report.md",
                mime="text/markdown",
                key="dl_final",
            )


# ============================================================
# 11. MODULE: SKILL STUDIO
# ============================================================
elif nav_choice == L10N["nav_skill_studio"]:
    st.subheader("🧪 Skill Studio")
    st.write("管理 Stage 1–5 使用的技能提示與未來可擴充的 reviewer skills。")

    tab1, tab2 = st.tabs(["Skills", "Create Skill"])
    with tab1:
        st.dataframe(st.session_state.skills, use_container_width=True, hide_index=True)

    with tab2:
        name = st.text_input("Skill name")
        description = st.text_area("Description")
        if st.button("Create Skill"):
            if require_input(name, "Skill name"):
                st.session_state.skills.append(
                    {
                        "id": f"SKILL-{len(st.session_state.skills)+1:03d}",
                        "name": name,
                        "model": st.session_state.active_model,
                        "description": description,
                    }
                )
                st.success("Skill created.")

    st.download_button(
        "📥 Download skills.json",
        data=safe_json(st.session_state.skills),
        file_name="skills.json",
        mime="application/json",
    )


# ============================================================
# 12. MODULE: PIPELINE STUDIO
# ============================================================
elif nav_choice == L10N["nav_pipeline"]:
    st.subheader("🧬 Pipeline Studio")
    for pipe in st.session_state.pipelines:
        st.markdown(f"### {pipe['name']}")
        st.dataframe(pipe["nodes"], use_container_width=True, hide_index=True)

    if st.button("➕ Add Review Node"):
        nodes = st.session_state.pipelines[0]["nodes"]
        nodes.append(
            {
                "step": len(nodes) + 1,
                "name": "Custom reviewer step",
                "status": "Custom",
            }
        )
        st.rerun()

    st.download_button(
        "📥 Download pipeline.json",
        data=safe_json(st.session_state.pipelines),
        file_name="pipeline.json",
        mime="application/json",
    )


# ============================================================
# 13. MODULE: AGENT STUDIO
# ============================================================
elif nav_choice == L10N["nav_agents"]:
    st.subheader("🤖 Agent Studio")
    if yaml is None:
        st.warning("PyYAML 未安裝。requirements.txt 請加入 PyYAML。")
    else:
        yaml_text = yaml.safe_dump(st.session_state.agents, allow_unicode=True, sort_keys=False)
        edited = st.text_area("agents.yaml", yaml_text, height=300)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 Validate YAML"):
                try:
                    parsed = yaml.safe_load(edited)
                    if not isinstance(parsed, list):
                        raise ValueError("agents.yaml 頂層必須是 list。")
                    st.session_state.agents = parsed
                    st.success("YAML valid and saved.")
                except Exception as exc:
                    st.error(f"YAML error: {exc}")
        with c2:
            st.download_button(
                "📥 Download agents.yaml",
                data=edited,
                file_name="agents.yaml",
                mime="text/yaml",
            )


# ============================================================
# 14. MODULE: AI UTILITIES
# ============================================================
elif nav_choice == L10N["nav_wow_ai"]:
    st.subheader("🚀 AI Regulatory Utilities")

    t1, t2, t3 = st.tabs(["Evidence consistency", "Gap checklist", "Prompt inspector"])

    with t1:
        st.write("快速檢查 Stage 1–3 是否都有結果，並顯示跨階段可用性。")
        checks = [
            ("Stage 1 FDA evidence", bool(b["stage1_result"])),
            ("Stage 2 IFU evidence", bool(b["stage2_result"])),
            ("Stage 3 submission evidence", bool(b["stage3_result"])),
            ("Stage 4 guidance", bool(b["stage4_result"])),
            ("Stage 5 questions", bool(b["stage5_questions"])),
            ("Final report", bool(b["stage5_report"])),
        ]
        st.dataframe(
            [{"Evidence": x, "Available": "Yes" if ok else "No"} for x, ok in checks],
            use_container_width=True,
            hide_index=True,
        )

    with t2:
        st.markdown(
            """
            **Reviewer checklist**
            - 裝置名稱、型號、版本與 IFU 是否一致？
            - Intended use / indication 是否一致？
            - FDA product code / classification 是否有來源？
            - 510(k) candidate 是否真的可由來源支持？
            - 主機與附件規格是否完整？
            - 軟體版本與 AI 功能是否在文件中明載？
            - Safety / performance evidence 是否與宣稱一致？
            - Label / IFU / submission documents 是否一致？
            - 台灣法規與年度申報要求是否以現行官方資料確認？
            - 所有 AI inference 是否與 source evidence 清楚區隔？
            """
        )

    with t3:
        st.code(
            "\n\n".join(
                [
                    "STAGE1_PROMPT",
                    "STAGE2_PROMPT",
                    "STAGE3_PROMPT",
                    "STAGE4_PROMPT",
                    "STAGE5_PROMPT",
                    "FINAL_REPORT_PROMPT",
                ]
            ),
            language="text",
        )


# ============================================================
# 15. MODULE: RESULTS LIBRARY
# ============================================================
elif nav_choice == L10N["nav_results"]:
    st.subheader("📁 Results Library")
    if not st.session_state.results:
        st.info("尚無結果。完成 Stage 1–5 後會自動保存。")
    else:
        for i, item in enumerate(st.session_state.results):
            with st.expander(f"{item['timestamp']} · {item['title']}"):
                st.markdown(item["body"])
                st.download_button(
                    "Download",
                    data=item["body"],
                    file_name=f"result_{i+1}.md",
                    mime="text/markdown",
                    key=f"download_result_{i}",
                )

    st.download_button(
        "📦 Download all results as JSON",
        data=safe_json(st.session_state.results),
        file_name="review_results.json",
        mime="application/json",
    )


# ============================================================
# 16. MODULE: SETTINGS
# ============================================================
elif nav_choice == L10N["nav_settings"]:
    st.subheader("⚙️ System Settings & Security")
    st.write(f"**UI language:** {st.session_state.language}")
    st.write(f"**Theme:** {st.session_state.theme_name} / {st.session_state.theme_mode}")
    st.write(f"**Model:** {st.session_state.active_model}")
    st.write(f"**Gemini API key:** {'Configured' if st.session_state.api_key else 'Missing'}")
    st.write("**Web search:** Gemini Google Search grounding for Stage 1 and Stage 4")
    st.write("**File support:** PDF/TXT/MD/CSV/DOCX (parser availability depends on requirements.txt)")

    st.markdown("### Environment check")
    st.dataframe(
        [
            {"Component": "streamlit", "Status": "Loaded"},
            {"Component": "google-genai", "Status": "Loaded" if genai else "Missing"},
            {"Component": "pypdf", "Status": "Loaded" if PdfReader else "Missing"},
            {"Component": "PyYAML", "Status": "Loaded" if yaml else "Missing"},
            {"Component": "GEMINI_API_KEY", "Status": "Configured" if st.session_state.api_key else "Missing"},
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Export / import session data")
    export_state = {
        "version": APP_VERSION,
        "language": st.session_state.language,
        "theme_name": st.session_state.theme_name,
        "theme_mode": st.session_state.theme_mode,
        "active_model": st.session_state.active_model,
        "bench": st.session_state.bench,
        "skills": st.session_state.skills,
        "pipelines": st.session_state.pipelines,
        "agents": st.session_state.agents,
    }
    st.download_button(
        "📤 Export Review Session JSON",
        data=safe_json(export_state),
        file_name="medical_device_review_session.json",
        mime="application/json",
    )

    uploaded_session = st.file_uploader(
        "Import Review Session JSON",
        type=["json"],
        key="session_import",
    )
    if uploaded_session and st.button("Import Session", key="import_session"):
        try:
            imported = json.loads(uploaded_session.getvalue().decode("utf-8"))
            for key in ["language", "theme_name", "theme_mode", "active_model", "bench", "skills", "pipelines", "agents"]:
                if key in imported:
                    st.session_state[key] = imported[key]
            st.success("Session imported. 請重新確認 API Key。")
            st.rerun()
        except Exception as exc:
            st.error(f"Import failed: {exc}")

    st.divider()
    if st.button("🗑️ Clear review session", type="secondary"):
        keys_to_clear = [
            "bench", "results", "notes", "token_count", "logs"
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.rerun()


# ============================================================
# 17. FOOTER / OPERATIONAL HUD
# ============================================================
with st.expander("⚡ Operational HUD", expanded=False):
    st.write(f"**Active model:** {st.session_state.active_model}")
    st.write(f"**Estimated token usage:** {st.session_state.token_count:,}")
    st.write(f"**Skills:** {len(st.session_state.skills)} · **Pipelines:** {len(st.session_state.pipelines)}")
    st.write("**Latest logs:**")
    for line in st.session_state.logs[-8:]:
        st.caption(line)

st.caption(
    "⚠️ 此工具用於法規情報整理與文件審查輔助；AI 輸出不構成 FDA、TFDA 或其他主管機關的正式核准、分類或法規決定。"
)
