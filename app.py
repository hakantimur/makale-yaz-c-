import os

import streamlit as st
from dotenv import load_dotenv

import openrouter
from openrouter import OpenRouterError
from seo_checks import run_python_seo_checks
from utils import safe_filename, save_markdown

load_dotenv()

st.set_page_config(page_title="Noritales Blog Writer", layout="wide")

LANGUAGES = ["English", "Turkish", "German", "Spanish", "French", "Portuguese", "Arabic"]
MAX_AUTO_REGENERATE = 2


def init_state():
    defaults = {
        "research": None,
        "research_usage": None,
        "article_prompt": None,
        "article_prompt_usage": None,
        "article_markdown": None,
        "article_usage": None,
        "seo_report": None,
        "evaluator_text": None,
        "evaluator_usage": None,
        "regenerate_count": 0,
        "saved_path": None,
        "models": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_model_label(model: dict) -> str:
    model_id = model.get("id", "unknown")
    pricing = model.get("pricing", {})
    context_length = model.get("context_length", "?")
    prompt_price = pricing.get("prompt", "?")
    completion_price = pricing.get("completion", "?")
    return f"{model_id}  |  ctx: {context_length}  |  in: {prompt_price}  out: {completion_price}"


def get_model_pricing(models: list, model_id: str) -> dict:
    for m in models or []:
        if m.get("id") == model_id:
            return m.get("pricing", {})
    return {}


def estimate_cost(usage: dict, pricing: dict) -> float:
    if not usage or not pricing:
        return 0.0
    try:
        prompt_cost = float(pricing.get("prompt", 0)) * usage.get("prompt_tokens", 0)
        completion_cost = float(pricing.get("completion", 0)) * usage.get("completion_tokens", 0)
        return round(prompt_cost + completion_cost, 6)
    except (TypeError, ValueError):
        return 0.0


def show_usage(label: str, usage: dict, pricing: dict):
    if not usage:
        return
    cost = estimate_cost(usage, pricing)
    st.caption(
        f"{label} — input: {usage.get('prompt_tokens', '?')} tok, "
        f"output: {usage.get('completion_tokens', '?')} tok, "
        f"est. cost: ${cost}"
    )


def parse_evaluator_output(text: str) -> dict:
    result = {"score": None, "status": None, "raw": text}
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("OVERALL SCORE"):
            digits = "".join(ch for ch in line.split(":", 1)[-1] if ch.isdigit())
            if digits:
                result["score"] = int(digits)
        elif line.upper().startswith("STATUS"):
            value = line.split(":", 1)[-1].strip().upper()
            for candidate in ("PASS", "REVISE", "REGENERATE"):
                if candidate in value:
                    result["status"] = candidate
                    break
    return result


init_state()

st.title("Noritales Local SEO + LLM Blog Writer")

with st.sidebar:
    st.header("OpenRouter")
    api_key = st.text_input(
        "API Key",
        type="password",
        value=os.getenv("OPENROUTER_API_KEY", ""),
        help="Loaded from .env by default; you can override it here for this session only.",
    )
    if st.button("Load / Refresh Model List"):
        try:
            st.session_state["models"] = openrouter.get_models(api_key)
            st.success(f"{len(st.session_state['models'])} models loaded.")
        except OpenRouterError as exc:
            st.error(str(exc))

    if not api_key:
        st.warning("OpenRouter API key is missing.")

models = st.session_state["models"] or []
model_options = [m.get("id") for m in models] if models else []
model_labels = {m.get("id"): format_model_label(m) for m in models}

st.header("1. Assignment")
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic")
    focus_keyword = st.text_input("Focus Keyword")
    language = st.selectbox("Language", LANGUAGES)
with col2:
    word_count = st.number_input("Target Word Count", min_value=300, max_value=5000, value=1500, step=100)
    target_market = st.text_input("Target Market (optional)")

st.subheader("Models (one per request — each request is independent)")
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    research_model = st.selectbox(
        "Research Model", model_options, format_func=lambda x: model_labels.get(x, x), key="research_model"
    ) if model_options else st.text_input("Research Model (id)", key="research_model_manual")
with mcol2:
    prompt_builder_model = st.selectbox(
        "Article Prompt Builder Model", model_options, format_func=lambda x: model_labels.get(x, x), key="builder_model"
    ) if model_options else st.text_input("Article Prompt Builder Model (id)", key="builder_model_manual")
with mcol3:
    writer_model = st.selectbox(
        "Writer Model", model_options, format_func=lambda x: model_labels.get(x, x), key="writer_model"
    ) if model_options else st.text_input("Writer Model (id)", key="writer_model_manual")
with mcol4:
    evaluator_model = st.selectbox(
        "Evaluator Model", model_options, format_func=lambda x: model_labels.get(x, x), key="evaluator_model"
    ) if model_options else st.text_input("Evaluator Model (id)", key="evaluator_model_manual")

can_run = bool(api_key)

if st.button("RESEARCH TOPIC", disabled=not can_run):
    if not topic or not focus_keyword:
        st.error("Topic and Focus Keyword are required.")
    else:
        try:
            with st.spinner("Researching..."):
                result = openrouter.research_topic(
                    api_key, research_model, topic, focus_keyword, language, word_count, target_market
                )
            st.session_state["research"] = result["content"]
            st.session_state["research_usage"] = result["usage"]
            st.session_state["article_prompt"] = None
            st.session_state["article_markdown"] = None
            st.session_state["seo_report"] = None
            st.session_state["evaluator_text"] = None
        except OpenRouterError as exc:
            st.error(str(exc))

if st.session_state["research"]:
    st.header("2. Research Pack")
    show_usage("Research", st.session_state["research_usage"], get_model_pricing(models, research_model))
    with st.expander("View Research Pack", expanded=True):
        st.markdown(st.session_state["research"])

    st.subheader("Your Answers")
    user_answers = st.text_area(
        "Answer the questions listed under QUESTIONS FOR USER above",
        height=200,
        key="user_answers",
    )

    if st.button("BUILD ARTICLE PROMPT", disabled=not can_run):
        if not user_answers.strip():
            st.error("Please answer the research questions first.")
        else:
            try:
                with st.spinner("Building article-specific prompt..."):
                    result = openrouter.build_article_prompt(
                        api_key, prompt_builder_model, st.session_state["research"], user_answers,
                        topic, focus_keyword, language, word_count, target_market,
                    )
                st.session_state["article_prompt"] = result["content"]
                st.session_state["article_prompt_usage"] = result["usage"]
                st.session_state["article_markdown"] = None
                st.session_state["seo_report"] = None
                st.session_state["evaluator_text"] = None
            except OpenRouterError as exc:
                st.error(str(exc))

if st.session_state["article_prompt"]:
    st.header("3. Article-Specific Prompt")
    show_usage("Prompt Builder", st.session_state["article_prompt_usage"], get_model_pricing(models, prompt_builder_model))
    with st.expander("View Writer Prompt", expanded=False):
        st.markdown(st.session_state["article_prompt"])

    if st.button("WRITE ARTICLE", disabled=not can_run):
        try:
            with st.spinner("Writing article..."):
                result = openrouter.write_article(api_key, writer_model, st.session_state["article_prompt"])
            st.session_state["article_markdown"] = result["content"]
            st.session_state["article_usage"] = result["usage"]
            st.session_state["seo_report"] = None
            st.session_state["evaluator_text"] = None
            st.session_state["regenerate_count"] = 0
        except OpenRouterError as exc:
            st.error(str(exc))

if st.session_state["article_markdown"]:
    st.header("4. Article")
    show_usage("Writer", st.session_state["article_usage"], get_model_pricing(models, writer_model))
    with st.expander("View Article", expanded=True):
        st.markdown(st.session_state["article_markdown"])

    if st.button("RUN SEO + LLM AUDIT", disabled=not can_run):
        try:
            report = run_python_seo_checks(st.session_state["article_markdown"], focus_keyword, word_count)
            st.session_state["seo_report"] = report
            with st.spinner("Running evaluator..."):
                eval_result = openrouter.evaluate_article(
                    api_key, evaluator_model, st.session_state["article_markdown"], report
                )
            st.session_state["evaluator_text"] = eval_result["content"]
            st.session_state["evaluator_usage"] = eval_result["usage"]
        except OpenRouterError as exc:
            st.error(str(exc))

if st.session_state["seo_report"]:
    st.header("5. SEO + LLM Quality Audit")
    report = st.session_state["seo_report"]
    with st.expander("View Python SEO Checks", expanded=False):
        st.json(report)
    if report["hard_fails"]:
        st.error("Hard fails detected:\n" + "\n".join(f"- {f}" for f in report["hard_fails"]))

    if st.session_state["evaluator_text"]:
        show_usage("Evaluator", st.session_state["evaluator_usage"], get_model_pricing(models, evaluator_model))
        parsed = parse_evaluator_output(st.session_state["evaluator_text"])
        status = parsed["status"]
        score = parsed["score"]

        if report["hard_fails"] and status == "PASS":
            status = "REGENERATE"

        st.subheader(f"FINAL SCORE: {score if score is not None else '?'} / 100")
        st.subheader(f"STATUS: {status or 'UNKNOWN'}")

        with st.expander("View Evaluator Report", expanded=True):
            st.markdown(st.session_state["evaluator_text"])

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if status == "REVISE" and st.button("REVISE ARTICLE"):
                try:
                    with st.spinner("Revising article..."):
                        result = openrouter.revise_article(
                            api_key, writer_model, st.session_state["article_markdown"],
                            [report["hard_fails"], parsed["raw"]],
                        )
                    st.session_state["article_markdown"] = result["content"]
                    st.session_state["seo_report"] = None
                    st.session_state["evaluator_text"] = None
                    st.rerun()
                except OpenRouterError as exc:
                    st.error(str(exc))

        with col_b:
            can_regenerate = st.session_state["regenerate_count"] < MAX_AUTO_REGENERATE
            if status == "REGENERATE" and st.button("REGENERATE ARTICLE", disabled=not can_regenerate):
                try:
                    with st.spinner("Regenerating article..."):
                        result = openrouter.regenerate_article(
                            api_key, writer_model, st.session_state["article_prompt"], parsed["raw"]
                        )
                    st.session_state["article_markdown"] = result["content"]
                    st.session_state["seo_report"] = None
                    st.session_state["evaluator_text"] = None
                    st.session_state["regenerate_count"] += 1
                    st.rerun()
                except OpenRouterError as exc:
                    st.error(str(exc))
            if not can_regenerate:
                st.caption(f"Maximum automatic regenerate ({MAX_AUTO_REGENERATE}) reached.")

        with col_c:
            if status == "PASS" or not report["hard_fails"]:
                if st.button("SAVE / DOWNLOAD MARKDOWN"):
                    base_name = safe_filename(focus_keyword or topic)
                    path = save_markdown(st.session_state["article_markdown"], base_name)
                    st.session_state["saved_path"] = path
                    st.success(f"Saved to {path}")

        st.download_button(
            "Download Markdown",
            data=st.session_state["article_markdown"],
            file_name=f"{safe_filename(focus_keyword or topic)}.md",
            mime="text/markdown",
        )
