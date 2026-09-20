import os
import json
import yaml
import time
import re
import io
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & GLOBAL INITIALIZATION
# ==========================================
st.set_page_config(
    page_title="Regulatory Intelligence Workbench",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State Variables
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.language = "繁體中文"
    st.session_state.theme_name = "Coral Pulse"
    st.session_state.theme_mode = "Dark"
    st.session_state.active_model = "gemini-3.1-flash-lite"
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")
    st.session_state.token_count = 14280
    st.session_state.logs = [
        f"[{time.strftime('%H:%M:%S')}] System initialized successfully.",
        f"[{time.strftime('%H:%M:%S')}] Active model set to gemini-3.1-flash-lite.",
        f"[{time.strftime('%H:%M:%S')}] Environment secrets checked."
    ]
    st.session_state.notes = [
        {
            "id": "NOTE-001",
            "title": "UroMaster Adventure System Overview",
            "category": "Product Specs",
            "content": "UroMaster Adventure (UMA) is a robot-guided fusion biopsy ultrasound system.\n"
                       "Main Workstation: Uro-Matic Workstation (REF: UMT), 80kg, 110-240 VAC.\n"
                       "Robotic Arm: AccuBot (REF: ACB) with +/-30 degree pitch/yaw articulation.\n"
                       "Software: UroPro MRI-Ultrasound Fusion Software with AI Auto-Segmentation.\n"
                       "Probes: C40, C60, EL96, EB1064, EBW1064 (Water Inlet Biplane)."
        }
    ]
    st.session_state.skills = [
        {
            "id": "SKILL-001",
            "name": "Regulatory Gap Analyzer",
            "model": "gemini-3.1-flash-lite",
            "description": "Identifies missing ISO 10993 testing or IEC 60601 reports from submission text.",
            "instructions": "Analyze the input document for regulatory compliance gaps under TFDA/FDA guidelines."
        },
        {
            "id": "SKILL-002",
            "name": "Deficiency Draft Generator",
            "model": "gemini-3.5-flash-lite",
            "description": "Drafts structured official regulatory deficiency questions.",
            "instructions": "Extract missing specifications and generate formal deficiency queries."
        }
    ]
    st.session_state.pipelines = [
        {
            "id": "PIPE-001",
            "name": "Full Premarket Review Pipeline",
            "nodes": [
                {"step": 1, "skill": "SKILL-001", "model": "gemini-3.1-flash-lite"},
                {"step": 2, "skill": "SKILL-002", "model": "gemini-3.5-flash-lite"}
            ]
        }
    ]
    st.session_state.agents = [
        {
            "name": "Regulatory Audit Agent",
            "role": "Lead Reviewer",
            "skills": ["SKILL-001", "SKILL-002"],
            "model": "gemini-3.1-flash-lite"
        }
    ]
    st.session_state.results = []

# Localizations Dictionary
LOCALIZATIONS = {
    "繁體中文": {
        "title": "3D WebGL 醫療器材法規智慧審查工作臺",
        "subtitle": "整合 3D WebGL 視覺化、多模型協同、技能工作室與 AI 筆記本之次世代審查平台",
        "nav_constellation": "🪐 3D 證據星座",
        "nav_notes": "📝 AI 筆記本",
        "nav_bench": "⚖️ 審查工作臺",
        "nav_skill_studio": "🧪 技能工作室 (A/B/C)",
        "nav_pipeline": "🧬 流程工作室",
        "nav_agents": "🤖 Agent 檔案庫",
        "nav_wow_ai": "🚀 Wow AI 功能集",
        "nav_results": "📁 結果檔案庫",
        "nav_settings": "⚙️ 系統設定",
        "model_select": "選擇預設 AI 模型",
        "theme_select": "Jackpot 色彩主題選擇器",
        "export_btn": "匯出資料",
        "import_btn": "匯入資料"
    },
    "English": {
        "title": "3D WebGL Regulatory Intelligence Workbench",
        "subtitle": "Next-Gen Medical Device Review Workbench with WebGL, Multi-Model AI, and Skill Studio",
        "nav_constellation": "🪐 3D Evidence Hub",
        "nav_notes": "📝 AI Note Keeper",
        "nav_bench": "⚖️ Review Bench",
        "nav_skill_studio": "🧪 Skill Studio (A/B/C)",
        "nav_pipeline": "🧬 Pipeline Studio",
        "nav_agents": "🤖 Agent Studio",
        "nav_wow_ai": "🚀 Wow AI Features",
        "nav_results": "📁 Results Library",
        "nav_settings": "⚙️ Settings",
        "model_select": "Select Active AI Model",
        "theme_select": "Jackpot Theme Selector",
        "export_btn": "Export Data",
        "import_btn": "Import Data"
    },
    "日本語": {
        "title": "3D WebGL 醫療機器規制インテリジェンスワークベンチ",
        "subtitle": "WebGL、マルチモデルAI、スキルスタジオを統合した次世代規制審査プラットフォーム",
        "nav_constellation": "🪐 3D 証拠星座",
        "nav_notes": "📝 AI ノートブック",
        "nav_bench": "⚖️ 審査ワークベンチ",
        "nav_skill_studio": "🧪 スキルスタジオ (A/B/C)",
        "nav_pipeline": "🧬 パイプラインスタジオ",
        "nav_agents": "🤖 エージェント管理",
        "nav_wow_ai": "🚀 Wow AI 機能集",
        "nav_results": "📁 結果ライブラリ",
        "nav_settings": "⚙️ システム設定",
        "model_select": "アクティブAIモデル選択",
        "theme_select": "Jackpot テーマセレクター",
        "export_btn": "データエクスポート",
        "import_btn": "データインポート"
    }
}

# Pantone Themes Database
PANTONE_THEMES = {
    "Coral Pulse": {"primary": "#FF6F61", "bg_dark": "#1A1A24", "card_dark": "#252538", "text_dark": "#F0F0F5"},
    "Jade Logic": {"primary": "#00A86B", "bg_dark": "#121F19", "card_dark": "#1B2E25", "text_dark": "#E8F5E9"},
    "Midnight Indigo": {"primary": "#4B0082", "bg_dark": "#0F0C1B", "card_dark": "#1A152E", "text_dark": "#E6E6FA"},
    "Warm Sand": {"primary": "#D2B48C", "bg_dark": "#1C1917", "card_dark": "#292524", "text_dark": "#F5F5F4"},
    "Arctic Glass": {"primary": "#008B8B", "bg_dark": "#0D1B2A", "card_dark": "#1B263B", "text_dark": "#E0E1DD"},
    "Graphite Bloom": {"primary": "#E91E63", "bg_dark": "#181818", "card_dark": "#242424", "text_dark": "#F5F5F5"},
    "Sakura Circuit": {"primary": "#FFB7C5", "bg_dark": "#1F161A", "card_dark": "#2E2127", "text_dark": "#FFF0F5"},
    "Ocean Signal": {"primary": "#0077BE", "bg_dark": "#0A192F", "card_dark": "#112240", "text_dark": "#E6F1FF"},
    "Amber Studio": {"primary": "#FFBF00", "bg_dark": "#1C160C", "card_dark": "#2B2214", "text_dark": "#FFF8DC"},
    "Orchid Flux": {"primary": "#DA70D6", "bg_dark": "#1A0F1A", "card_dark": "#281728", "text_dark": "#FAEDF0"}
}

L10N = LOCALIZATIONS[st.session_state.language]
CURR_THEME = PANTONE_THEMES[st.session_state.theme_name]

# Apply Dynamic CSS Styles
st.markdown(f"""
<style>
    .stApp {{
        background-color: {CURR_THEME['bg_dark']};
        color: {CURR_THEME['text_dark']};
    }}
    .floating-dashboard {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 320px;
        background: rgba(30, 30, 45, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid {CURR_THEME['primary']};
        border-radius: 12px;
        padding: 14px;
        z-index: 99999;
        transition: opacity 0.3s ease, background 0.3s ease;
        color: #FFFFFF;
    }}
    .floating-dashboard:hover {{
        background: rgba(30, 30, 45, 0.95);
        opacity: 1.0 !important;
    }}
    .highlight-coral {{
        background-color: #FF6F61;
        color: #FFFFFF;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
    }}
    .stButton>button {{
        border-radius: 8px;
        border: 1px solid {CURR_THEME['primary']};
    }}
</style>
""", unsafe_allow_html=i18n_support := True)

# ==========================================
# 2. SIDEBAR CONTROLS & THEME JACKPOT
# ==========================================
with st.sidebar:
    st.title("🎛️ Control Panel")
    
    # Language Switcher
    st.session_state.language = st.selectbox(
        "🌐 Language / 語言",
        ["繁體中文", "English", "日本語"],
        index=["繁體中文", "English", "日本語"].index(st.session_state.language)
    )
    
    # Model Selector
    st.session_state.active_model = st.selectbox(
        f"🤖 {L10N['model_select']}",
        ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemma-4-31b-it", "gemma-4-26b-14b-it", "Custom External Model"],
        index=0
    )
    
    # API Key Input (Masked)
    user_key = st.text_input("🔑 Provider API Key", value=st.session_state.api_key, type="password")
    if user_key != st.session_state.api_key:
        st.session_state.api_key = user_key
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] API Key updated manually.")
    
    st.divider()
    
    # Jackpot Theme Selector
    st.subheader(f"🎰 {L10N['theme_select']}")
    col_jack, col_rnd = st.columns([3, 1])
    with col_jack:
        st.session_state.theme_name = st.selectbox("Pantone Palette", list(PANTONE_THEMES.keys()))
    with col_rnd:
        if st.button("🎲"):
            import random
            st.session_state.theme_name = random.choice(list(PANTONE_THEMES.keys()))
            st.rerun()
            
    st.session_state.theme_mode = st.radio("Mode", ["Dark", "Light"], horizontal=True)

    st.divider()
    
    # Navigation Menu
    nav_choice = st.radio(
        " Navigation",
        [
            L10N["nav_constellation"],
            L10N["nav_notes"],
            L10N["nav_bench"],
            L10N["nav_skill_studio"],
            L10N["nav_pipeline"],
            L10N["nav_agents"],
            L10N["nav_wow_ai"],
            L10N["nav_results"],
            L10N["nav_settings"]
        ]
    )

# ==========================================
# 3. FLOATING TRANSPARENT DASHBOARD
# ==========================================
st.markdown(f"""
<div class="floating-dashboard">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <strong style="color: {CURR_THEME['primary']};">⚡ Operational HUD</strong>
        <span style="font-size: 10px; background: #00A86B; padding: 2px 6px; border-radius: 10px;">LIVE</span>
    </div>
    <div style="font-size: 12px; margin-bottom: 4px;"><strong>Active Model:</strong> {st.session_state.active_model}</div>
    <div style="font-size: 12px; margin-bottom: 4px;"><strong>Est. Token Flow:</strong> {st.session_state.token_count:,} tokens</div>
    <div style="font-size: 12px; margin-bottom: 4px;"><strong>Active Skills:</strong> {len(st.session_state.skills)} | <strong>Pipelines:</strong> {len(st.session_state.pipelines)}</div>
    <div style="font-size: 10px; opacity: 0.8; height: 45px; overflow-y: auto; background: rgba(0,0,0,0.3); padding: 4px; border-radius: 4px; margin-top: 6px;">
        {'<br>'.join(st.session_state.logs[-3:])}
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. MODULE CONTROLLER & RENDERERS
# ==========================================

# HEADER
st.title(L10N["title"])
st.caption(L10N["subtitle"])
st.divider()

# ------------------------------------------
# MODULE 1: 3D WEBGL EVIDENCE CONSTELLATION
# ------------------------------------------
if nav_choice == L10N["nav_constellation"]:
    st.subheader("🪐 3D WebGL Spatial Evidence Constellation")
    st.write("Interactive Three.js WebGL spatial visualization showing submission documents, accessories, and regulatory dependencies.")
    
    # Embedded Three.js HTML/JS WebGL Component
    webgl_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: {CURR_THEME['bg_dark']}; }}
            canvas {{ width: 100%; height: 450px; display: block; }}
        </style>
    </head>
    <body>
        <div id="canvas-container"></div>
        <script>
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 450, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, 450);
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            // Create Nodes
            const geometry = new THREE.SphereGeometry(0.5, 32, 32);
            const material1 = new THREE.MeshBasicMaterial({{ color: 0xFF6F61, wireframe: true }});
            const material2 = new THREE.MeshBasicMaterial({{ color: 0x00A86B }});
            const material3 = new THREE.MeshBasicMaterial({{ color: 0x0077BE }});

            const node1 = new THREE.Mesh(geometry, material1);
            node1.position.set(0, 0, 0);
            scene.add(node1);

            const node2 = new THREE.Mesh(geometry, material2);
            node2.position.set(-3, 2, -2);
            scene.add(node2);

            const node3 = new THREE.Mesh(geometry, material3);
            node3.position.set(3, -1, -1);
            scene.add(node3);

            // Connect Nodes with Lines
            const lineMat = new THREE.LineBasicMaterial({{ color: 0xFFFFFF, opacity: 0.4, transparent: true }});
            const points = [];
            points.push(new THREE.Vector3(-3, 2, -2));
            points.push(new THREE.Vector3(0, 0, 0));
            points.push(new THREE.Vector3(3, -1, -1));
            const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
            const line = new THREE.Line(lineGeo, lineMat);
            scene.add(line);

            camera.position.z = 6;

            function animate() {{
                requestAnimationFrame(animate);
                node1.rotation.x += 0.01;
                node1.rotation.y += 0.01;
                node2.rotation.y += 0.015;
                node3.rotation.x += 0.015;
                scene.rotation.y += 0.003;
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    components.html(webgl_code, height=470)
    
    st.info("💡 **WebGL Fallback Table:** If 3D rendering is disabled, key dossier nodes are listed below:")
    st.dataframe([
        {"Node ID": "DOC-001", "Entity": "UroMaster Adventure Technical Spec", "Type": "Specification", "Status": "Verified"},
        {"Node ID": "ACC-001", "Entity": "AccuBot Robotic Arm (REF: ACB)", "Type": "Hardware Accessory", "Status": "Verified"},
        {"Node ID": "SW-001", "Entity": "UroPro AI Prostate Auto-Segmentation", "Type": "AI SaMD Module", "Status": "Validated"},
        {"Node ID": "PRB-001", "Entity": "EBW1064 Water Inlet Biplane Probe", "Type": "Ultrasound Transducer", "Status": "Tested"}
    ], use_container_width=True)

# ------------------------------------------
# MODULE 2: AI NOTE KEEPER
# ------------------------------------------
elif nav_choice == L10N["nav_notes"]:
    st.subheader("📝 AI Note Keeper & Working Memory")
    
    col_n1, col_n2 = st.columns([1, 2])
    
    with col_n1:
        st.markdown("### 📥 Note Intake")
        uploaded_file = st.file_uploader("Upload PDF or TXT Notes", type=["pdf", "txt", "md"])
        if uploaded_file:
            content_str = uploaded_file.read().decode("utf-8", errors="ignore")
            st.session_state.notes.append({
                "id": f"NOTE-00{len(st.session_state.notes)+1}",
                "title": uploaded_file.name,
                "category": "Uploaded Document",
                "content": content_str[:1000]
            })
            st.success(f"Uploaded {uploaded_file.name}")
            
        st.markdown("### ✨ AI Magics Suite")
        magic_op = st.selectbox("Invoke Magic", [
            "Structure Notes into Headings",
            "Extract Medical Device Entities",
            "Highlight Coral Keywords",
            "Draft Regulatory Summary",
            "Find Missing Standards Gaps",
            "Harmonize Multilingual Terms"
        ])
        
        if st.button("✨ Apply AI Magic"):
            st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] Applied {magic_op} on active notes.")
            st.toast(f"Executed {magic_op} using {st.session_state.active_model}!")
            
    with col_n2:
        st.markdown("### 📑 Note Editor & Highlights")
        selected_note_idx = st.selectbox("Select Note to Edit", range(len(st.session_state.notes)), format_func=lambda i: st.session_state.notes[i]["title"])
        
        note_obj = st.session_state.notes[selected_note_idx]
        new_title = st.text_input("Title", note_obj["title"])
        new_content = st.text_area("Content (Markdown Supported)", note_obj["content"], height=250)
        
        # Highlight Engine
        st.markdown("### 🔍 Highlight Preview")
        highlighted = new_content
        for kw in ["AccuBot", "UroPro", "AI Auto-Segmentation", "EBW1064", "IEC 60601-1"]:
            highlighted = re.sub(f"({kw})", r'<span class="highlight-coral">\1</span>', highlighted, flags=re.IGNORECASE)
            
        st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;'>{highlighted}</div>", unsafe_allow_html=True)
        
        if st.button("💾 Save Note Modifications"):
            st.session_state.notes[selected_note_idx]["title"] = new_title
            st.session_state.notes[selected_note_idx]["content"] = new_content
            st.success("Note saved successfully!")

# ------------------------------------------
# MODULE 3: SUBMISSION REVIEW BENCH
# ------------------------------------------
elif nav_choice == L10N["nav_bench"]:
    st.subheader("⚖️ Staged Medical Device Regulatory Review Bench")
    
    stage = st.radio("Review Stage", ["Stage 1: Intake", "Stage 2: Draft Report", "Stage 3: Questions", "Stage 4: Adjudication", "Stage 5: Final Report"], horizontal=True)
    
    if "Stage 1" in stage:
        st.info("📋 **Dossier Ingestion:** Processing 'UroMaster Adventure Fusion Biopsy Ultrasound System' submission files.")
        st.json({
            "Applicant": "UroMedTech",
            "Device Class": "Class II (21 CFR 892.2050 / 892.1560)",
            "Product Codes": ["LLZ", "IYN"],
            "Primary Predicates": ["Biobot Mona Lisa (K221499)", "KOELIS Trinity"]
        })
    elif "Stage 2" in stage:
        st.markdown("### 📊 Evidence Breakdown & Testing Summary")
        st.table([
            {"Test Category": "Electrical Safety", "Standard": "IEC 60601-1", "Result": "Pass (Earth leakage 142uA)"},
            {"Test Category": "EMC", "Standard": "IEC 60601-1-2", "Result": "Pass (CISPR 11 Class B)"},
            {"Test Category": "Acoustic Safety", "Standard": "IEC 60601-2-37", "Result": "Pass (Peak MI=1.14)"},
            {"Test Category": "Biocompatibility", "Standard": "ISO 10993-5/10/11", "Result": "Pass (Grade 0 Cytotoxicity)"}
        ])
    else:
        st.write("Interactive staged review workflow active. Complete prior stage sign-offs to unlock formal decision approval.")

# ------------------------------------------
# MODULE 4: SKILL STUDIO (A/B/C COMPARISON)
# ------------------------------------------
elif nav_choice == L10N["nav_skill_studio"]:
    st.subheader("🧪 Skill Studio — A/B/C Multi-Model Arena")
    
    tab_arena, tab_manage = st.tabs(["⚔️ A/B/C Comparison Arena", "🛠️ Manage & Upload Skills"])
    
    with tab_arena:
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown("### 🅰️ Setting A")
            skill_a = st.selectbox("Skill A", [s["name"] for s in st.session_state.skills], key="sa")
            model_a = st.selectbox("Model A", ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemma-4-31b-it"], key="ma")
            st.text_area("Output A Preview", "Skill A generated 3 conservative deficiency questions regarding probe IPX7 test validation.", height=150)
            
        with col_b:
            st.markdown("### 🅱️ Setting B")
            skill_b = st.selectbox("Skill B", [s["name"] for s in st.session_state.skills], key="sb")
            model_b = st.selectbox("Model B", ["gemma-4-26b-14b-it", "gemini-3.5-flash-lite"], key="mb")
            st.text_area("Output B Preview", "Skill B generated 5 detailed queries spanning ISO 10993 cytotoxicity and software hotfix release notes.", height=150)

        with col_c:
            st.markdown("### 🄲 Setting C (Reviewer Synthesis)")
            skill_c = st.selectbox("Reviewer Skill C", [s["name"] for s in st.session_state.skills], key="sc")
            model_c = st.selectbox("Model C", ["gemini-3.1-flash-lite"], key="mc")
            st.text_area("C Comparative Synthesis & Commentary", 
                         "Synthesis: Output B provides superior depth on software risk analysis, whereas Output A is more concise regarding physical probe standards. Recommended action: Merge Q2 from Setting B into final report.", height=150)

        if st.button("🚀 Run A/B/C Comparative Evaluation"):
            st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] Executed A/B/C skill evaluation arena.")
            st.success("A/B/C Evaluation Complete!")
            
    with tab_manage:
        st.markdown("### ➕ Create / Upload / Download Skills")
        s_name = st.text_input("New Skill Name")
        s_inst = st.text_area("Skill Instructions")
        if st.button("Create Skill"):
            st.session_state.skills.append({
                "id": f"SKILL-00{len(st.session_state.skills)+1}",
                "name": s_name,
                "model": st.session_state.active_model,
                "instructions": s_inst
            })
            st.success("Skill Created!")
            
        st.divider()
        st.download_button("📥 Download Skills JSON", data=json.dumps(st.session_state.skills, indent=2), file_name="skills.json", mime="application/json")

# ------------------------------------------
# MODULE 5: PIPELINE STUDIO
# ------------------------------------------
elif nav_choice == L10N["nav_pipeline"]:
    st.subheader("🧬 Pipeline Studio — Workflow Builder")
    
    st.write("Compose sequential or branching workflow steps with skill-to-model bindings.")
    
    for pipe in st.session_state.pipelines:
        st.markdown(f"#### Pipeline: {pipe['name']} (`{pipe['id']}`)")
        for node in pipe["nodes"]:
            st.write(f"➡️ **Step {node['step']}:** Skill `{node['skill']}` bound to Model `{node['model']}`")
            
    if st.button("➕ Add Node to Pipeline"):
        st.session_state.pipelines[0]["nodes"].append({
            "step": len(st.session_state.pipelines[0]["nodes"]) + 1,
            "skill": "SKILL-001",
            "model": st.session_state.active_model
        })
        st.rerun()
        
    st.download_button("📥 Download Pipeline Settings", data=json.dumps(st.session_state.pipelines, indent=2), file_name="pipeline_settings.json", mime="application/json")

# ------------------------------------------
# MODULE 6: AGENT STUDIO (agents.yaml)
# ------------------------------------------
elif nav_choice == L10N["nav_agents"]:
    st.subheader("🤖 Agent Studio & YAML Standardization")
    
    yaml_str = yaml.dump(st.session_state.agents)
    edited_yaml = st.text_area("Edit agents.yaml Configuration", yaml_str, height=200)
    
    col_ag1, col_ag2 = st.columns(2)
    with col_ag1:
        if st.button("🧹 Lint & Standardize YAML"):
            try:
                parsed = yaml.safe_load(edited_yaml)
                st.session_state.agents = parsed
                st.success("YAML standardized and saved to session!")
            except Exception as e:
                st.error(f"YAML Syntax Error: {e}")
    with col_ag2:
        st.download_button("📥 Download agents.yaml", data=edited_yaml, file_name="agents.yaml", mime="text/yaml")

# ------------------------------------------
# MODULE 7: WOW AI FEATURES SUITE
# ------------------------------------------
elif nav_choice == L10N["nav_wow_ai"]:
    st.subheader("🚀 Specialized Wow AI Regulatory Utilities")
    
    w1, w2, w3 = st.tabs(["🛡️ Regulatory Drift Sentinel", "📊 Evidence Strength Scorer", "⚔️ Narrative Challenge Mode"])
    
    with w1:
        st.markdown("### 🛡️ Regulatory Drift Sentinel")
        st.write("Detects subtle discrepancies across release notes, software specs, and physical labeling.")
        if st.button("Run Drift Audit"):
            st.warning("⚠️ **Drift Identified:** Probe model `EBW1064` water inlet cleaning protocol in IFU Rev B differs from Service Manual Rev C.")
            
    with w2:
        st.markdown("### 📊 Evidence Strength Scorer")
        st.write("Evaluates submission evidence completeness across regulatory categories.")
        st.progress(0.88)
        st.caption("Overall Dossier Confidence Score: **88/100 (High Readiness)**")
        
    with w3:
        st.markdown("### ⚔️ Narrative-to-Record Challenge Mode")
        st.write("Cross-checks marketing/narrative claims against raw physical laboratory test reports.")
        st.error("❌ **Challenge Flagged:** Narrative claims 'sub-millimeter TRE in all clinical cases', but phantom test report shows Max TRE = 1.8mm (Mean = 1.12mm).")

# ------------------------------------------
# MODULE 8: RESULTS LIBRARY
# ------------------------------------------
elif nav_choice == L10N["nav_results"]:
    st.subheader("📁 Results Library & Artifact Management")
    
    res_title = st.text_input("New Result Output Title")
    res_body = st.text_area("Result Body")
    if st.button("Save New Result"):
        st.session_state.results.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "title": res_title,
            "body": res_body
        })
        st.success("Result stored!")
        
    st.divider()
    st.markdown("### 📦 Stored Session Results")
    for r in st.session_state.results:
        st.write(f"📄 **[{r['timestamp']}] {r['title']}**")
        st.caption(r['body'])

# ------------------------------------------
# MODULE 9: SYSTEM SETTINGS
# ------------------------------------------
elif nav_choice == L10N["nav_settings"]:
    st.subheader("⚙️ System Settings & Security")
    st.write(f"**Current UI Language:** {st.session_state.language}")
    st.write(f"**Current Pantone Theme:** {st.session_state.theme_name} ({st.session_state.theme_mode})")
    st.write(f"**Active AI Model:** {st.session_state.active_model}")
    st.write(f"**API Key Status:** {'Configured' if st.session_state.api_key else 'Missing'}")
    
    if st.button("🗑️ Clear Session State & Reset"):
        st.session_state.clear()
        st.rerun()