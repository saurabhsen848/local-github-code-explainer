"""Streamlit frontend for the local GitHub repository explainer."""

from __future__ import annotations

import streamlit as st

from llm import OllamaError, explain_repository
from repo_processor import RepositoryError, analyze_repository


st.set_page_config(page_title="Local GitHub Repository Code Explainer", page_icon="📘", layout="wide")
st.markdown("""
<style>
:root { --ink:#e8f1fb; --muted:#9cb0c7; --panel:#111d2c; --edge:#24364b; --cyan:#59d9f5; --blue:#548cff; }
.stApp { background: radial-gradient(ellipse at 12% 0%, #152d48 0%, #0b1420 42%, #09111b 100%); color:var(--ink); font-family:Arial,sans-serif; }
.block-container { max-width:1180px; padding-top:2rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:Arial,sans-serif !important; color:#f2f7ff !important; letter-spacing:-.025em; }
.hero { border:1px solid #27435f; background:linear-gradient(120deg,rgba(27,53,80,.94),rgba(14,28,44,.92)); padding:2.1rem 2.3rem; border-radius:22px; margin-bottom:1.2rem; box-shadow:0 20px 60px #02091255; }
.hero h1 { margin:0 0 .55rem; font-size:2.5rem; }
.hero p { color:#bfd0e3; font-size:1.1rem; margin:.2rem 0 1rem; }
.techline { color:#69dff7; font-size:.88rem; font-weight:600; letter-spacing:.04em; }
.eyebrow { text-transform:uppercase; letter-spacing:.15em; color:#66d8f4; font-size:.76rem; font-weight:700; margin-bottom:.55rem; }
.panel { border:1px solid var(--edge); background:rgba(17,29,44,.86); padding:1.1rem 1.3rem; border-radius:16px; }
.workflow { display:flex; flex-direction:column; align-items:center; gap:.22rem; margin:.6rem 0 1rem; }
.step { background:#14283c; border:1px solid #294862; padding:.7rem .85rem; border-radius:12px; color:#d8e7f7; font-weight:600; font-size:.88rem; text-align:center; width:min(100%,520px); }
.arrow { color:#59d9f5; font-weight:700; line-height:1.1; }
div[data-testid="stMetric"] { background:linear-gradient(150deg,#15283b,#101a28); border:1px solid #2a4056; padding:1rem; border-radius:15px; }
div[data-testid="stMetricLabel"] { color:#a9bdd2; }
div[data-testid="stMetricValue"] { color:#62d9f4; font-family:Arial,sans-serif; }
div.stButton > button[kind="primary"] { background:linear-gradient(90deg,#1687d3,#20b5d0); border:0; border-radius:10px; font-weight:700; min-height:3rem; }
div.stButton > button[kind="primary"]:hover { background:linear-gradient(90deg,#29a5e8,#41cce3); }
[data-testid="stExpander"] { border:1px solid #263a50; border-radius:12px; background:rgba(16,28,42,.68); }
.stCaption { color:#9cb0c7 !important; }
@media(max-width:700px){.hero{padding:1.4rem}.hero h1{font-size:1.8rem}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">Local GenAI · Repository analysis</div>
  <h1>Local GitHub Repository Code Explainer</h1>
  <p>Understand any public GitHub repository using a locally running GenAI model.</p>
  <div class="techline">Python &nbsp;•&nbsp; Streamlit &nbsp;•&nbsp; GitHub &nbsp;•&nbsp; Ollama &nbsp;•&nbsp; Llama 3.2</div>
</div>
""", unsafe_allow_html=True)
st.caption("Repositories are cloned temporarily and inspected as text. Repository code and setup scripts are never executed.")

with st.form("repository_form"):
    repository_url = st.text_input("Public GitHub repository URL", placeholder="https://github.com/owner/repository")
    submitted = st.form_submit_button("✦  Explain Repository", type="primary", use_container_width=True)
st.caption("Example: `https://github.com/saurabhsen848/FoodieHub` — copy this URL into the field above.")

if submitted:
    st.session_state.pop("analysis_report", None)
    st.session_state.pop("analysis_explanation", None)
    if not repository_url.strip():
        st.error("Enter a GitHub repository URL to continue.")
    else:
        try:
            with st.spinner("Cloning and inspecting relevant source files…"):
                report = analyze_repository(repository_url.strip())
            with st.spinner("Asking your local Ollama llama3.2 model to explain the project…"):
                explanation = explain_repository(report)
            st.session_state.analysis_report = report
            st.session_state.analysis_explanation = explanation
        except RepositoryError as exc:
            st.error(str(exc))
        except OllamaError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Something went wrong while analyzing this repository. Check Git, Ollama, and the app logs, then try again.")

report = st.session_state.get("analysis_report")
explanation = st.session_state.get("analysis_explanation")
if report and explanation:
    st.success("Repository analysis is ready.")
    st.markdown("<div class='eyebrow'>Repository snapshot</div>", unsafe_allow_html=True)
    st.subheader(report["repository_name"])
    st.caption(report["url"])
    metrics = st.columns(4)
    metrics[0].metric("Source files", report["source_file_count"])
    metrics[1].metric("Included in analysis", report["included_file_count"])
    metrics[2].metric("Languages", len(report["languages"]))
    metrics[3].metric("Technologies", len(report["technologies"]))

    summary_left, summary_right = st.columns([1, 1], gap="large")
    with summary_left:
        st.markdown("#### Repository Summary")
        st.write(f"**Estimated project type:** {report['project_type']}")
        st.write("**Main languages:** " + (", ".join(report["languages"]) or "Not identified"))
        st.write("**Detected technologies:** " + (", ".join(report["technologies"]) or "No additional technologies detected"))
    with summary_right:
        st.markdown("#### Important Source Files")
        for item in report["file_explanations"]:
            with st.expander(item["name"], expanded=False):
                st.write(item["explanation"])
    if report["warnings"]:
        for warning in report["warnings"]:
            st.info(warning)

    st.divider()
    st.markdown("### How It Works")
    st.markdown("""
    <div class="workflow">
      <div class="step">GitHub URL</div><div class="arrow">↓</div>
      <div class="step">Repository Cloning</div><div class="arrow">↓</div>
      <div class="step">Source Code Extraction</div><div class="arrow">↓</div>
      <div class="step">Code Analysis</div><div class="arrow">↓</div>
      <div class="step">Local Ollama LLM</div><div class="arrow">↓</div>
      <div class="step">AI Explanation</div><div class="arrow">↓</div>
      <div class="step">Streamlit UI</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### AI Explanation")
    st.markdown(explanation)
    markdown_download = f"# Local GitHub Repository Code Explainer\n\nRepository: {report['url']}\n\n{explanation}\n"
    txt_download = f"LOCAL GITHUB REPOSITORY CODE EXPLAINER\nRepository: {report['url']}\n\n{explanation}"
    dl_col1, dl_col2, _ = st.columns([1, 1, 3])
    dl_col1.download_button("Download Markdown", markdown_download, file_name=f"{report['repository_name']}-explanation.md", mime="text/markdown", use_container_width=True)
    dl_col2.download_button("Download TXT", txt_download, file_name=f"{report['repository_name']}-explanation.txt", mime="text/plain", use_container_width=True)

    st.divider()
    st.markdown("### Analysis Notes")
    notes = {
        "Security observations": ["Repository files are treated as untrusted text and are never executed.", "`.env` files are excluded and common secret patterns are redacted before local model analysis."],
        "Performance observations": ["Analysis is bounded by the configured file and character limits.", "Local model response time depends on available hardware and repository context size."],
        "Code organization observations": [f"The selected source context includes {report['included_file_count']} file(s); use the file explanations and AI report as a guided overview."],
        "Potential improvements": ["Review suggested improvements against the complete repository and its tests before making changes."]
    }
    for heading, bullets in notes.items():
        with st.expander(heading):
            for bullet in bullets:
                st.write(f"• {bullet}")

st.divider()
st.caption("Local inference via Ollama · llama3.2 · Public repositories · No repository code execution")
