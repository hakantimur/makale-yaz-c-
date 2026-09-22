import html
import os
import re

import streamlit as st
from dotenv import load_dotenv

import openrouter
from charts import render_charts_in_article
from html_export import convert_article_to_html, sanitize_html
from media import image_bytes_to_data_uri, save_image_bytes
from openrouter import OpenRouterError
from seo_checks import run_python_seo_checks
from utils import extract_section, parse_image_recommendations, safe_filename, save_markdown

load_dotenv()

st.set_page_config(page_title="Noritales Blog Writer", layout="wide")

# Preview-only defaults so the colored boxes/CTA/images/charts actually look colorful while
# testing locally. The real published site's own CSS is what controls this in production.
st.markdown(
    """
    <style>
    .noritales-cta-button {
        display: inline-block; background: #e8734a; color: white !important;
        padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none;
        margin: 12px 0;
    }
    .noritales-cta-button:hover { background: #d15f38; }
    .noritales-stat-card {
        display: flex; align-items: baseline; gap: 12px; background: #fff4ec;
        border-left: 5px solid #e8734a; border-radius: 8px; padding: 16px 20px; margin: 16px 0;
    }
    .noritales-stat-number { font-size: 2.2em; font-weight: 800; color: #e8734a; }
    .noritales-stat-label { color: #6b4a3a; font-size: 1.05em; }
    .noritales-quote-box {
        background: #fdf6f0; border-left: 5px solid #f2b675; border-radius: 8px;
        padding: 16px 20px; margin: 16px 0; font-style: italic; color: #5a4433;
    }
    .noritales-tip-box {
        background: #eef7f0; border-left: 5px solid #6fae7f; border-radius: 8px;
        padding: 16px 20px; margin: 16px 0; color: #2f5a3d;
    }
    .noritales-chart, .noritales-image { margin: 20px 0; text-align: center; }
    .noritales-chart img, .noritales-image img { max-width: 100%; border-radius: 8px; }
    .noritales-chart figcaption { font-size: 0.9em; color: #777; margin-top: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        "media_enriched": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_model_label(model: dict) -> str:
    model_id = model.get("id", "unknown")
    name = model.get("name", "")
    pricing = model.get("pricing", {})
    context_length = model.get("context_length", "?")
    prompt_price = pricing.get("prompt", "?")
    completion_price = pricing.get("completion", "?")
    # OpenRouter often carries a marketing nickname (e.g. "Nano Banana") only in `name`,
    # not in `id` — include it so searching the dropdown by that nickname actually works.
    name_part = f"  ({name})" if name and name.lower() not in model_id.lower() else ""
    return f"{model_id}{name_part}  |  ctx: {context_length}  |  in: {prompt_price}  out: {completion_price}"


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


def enrich_article_with_media(article_markdown: str, api_key: str, image_model: str, slug: str) -> tuple:
    """Generates 1-2 real images and renders any CHART RECOMMENDATION blocks into real
    charts, embedding both inline. Never blocks article completion — a failed image or
    chart is skipped with a warning, never an exception the caller has to handle."""
    warnings = []
    article_section = extract_section(article_markdown, "Article")
    image_section = extract_section(article_markdown, "Image Recommendations")
    images_info = parse_image_recommendations(image_section)

    image_requests = []
    if images_info["featured"].get("Concept"):
        image_requests.append(("featured", images_info["featured"]))
    if images_info["in_article"] and images_info["in_article"][0].get("Concept"):
        image_requests.append(("in_article", images_info["in_article"][0]))
    image_requests = image_requests[:2]

    new_article_section = article_section
    for kind, info in image_requests:
        concept = info.get("Concept", "")
        alt_text = html.escape(info.get("Alt text") or concept, quote=True)
        try:
            image_prompt = (
                f"Warm, friendly flat-illustration style image for a parenting/child-development "
                f"blog article. {concept}. No text or letters anywhere in the image."
            )
            try:
                image_bytes = openrouter.generate_image(api_key, image_model, image_prompt)
            except OpenRouterError:
                # Image generation can be transiently flaky — one retry before giving up,
                # never blocking the article either way.
                image_bytes = openrouter.generate_image(api_key, image_model, image_prompt)
            filename = f"{kind}.png"
            save_image_bytes(image_bytes, slug, filename)  # local backup copy
            data_uri = image_bytes_to_data_uri(image_bytes, "image/png")
            image_html = f'\n\n<figure class="noritales-image"><img src="{data_uri}" alt="{alt_text}"></figure>\n\n'

            if kind == "featured":
                new_article_section, count = re.subn(
                    r"^#\s+.+$",
                    lambda m: m.group(0) + image_html,
                    new_article_section,
                    count=1,
                    flags=re.MULTILINE,
                )
                if count == 0:
                    new_article_section = image_html + new_article_section
            else:
                section_name = info.get("Section", "")
                if section_name and section_name in new_article_section:
                    new_article_section = new_article_section.replace(section_name, section_name + image_html, 1)
                else:
                    new_article_section += image_html
        except OpenRouterError as exc:
            warnings.append(f"Görsel oluşturulamadı ({kind}): {exc}")
        except Exception as exc:  # noqa: BLE001 - image generation must never block the article
            warnings.append(f"Görsel oluşturulurken beklenmeyen hata ({kind}): {exc}")

    new_article_section, chart_warnings = render_charts_in_article(new_article_section, slug)
    warnings.extend(chart_warnings)

    new_full_markdown = article_markdown.replace(article_section, new_article_section, 1)
    return new_full_markdown, warnings


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


def model_select(label: str, key: str):
    if model_options:
        return st.selectbox(label, model_options, format_func=lambda x: model_labels.get(x, x), key=key)
    return st.text_input(f"{label} (id)", key=f"{key}_manual")


research_model = model_select("Research Model", "research_model")
prompt_builder_model = model_select("Article Prompt Builder Model", "builder_model")
writer_model = model_select("Writer Model", "writer_model")
evaluator_model = model_select("Evaluator Model", "evaluator_model")
image_model = model_select("Image Model", "image_model")

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
            st.session_state["media_enriched"] = False
        except OpenRouterError as exc:
            st.error(str(exc))

if st.session_state["article_markdown"]:
    st.header("4. Article")
    show_usage("Writer", st.session_state["article_usage"], get_model_pricing(models, writer_model))
    with st.expander("View Article", expanded=True):
        # Research pulls in live web content, and the Writer can quote it — sanitize any
        # embedded HTML before rendering it raw, in case adversarial page content made it
        # through as a "quote" (prompt-injection / stored-XSS defense).
        st.markdown(sanitize_html(st.session_state["article_markdown"]), unsafe_allow_html=True)

    if not st.session_state["media_enriched"]:
        st.caption(
            "Metni beğendikten sonra (revize/regenerate'den geçtikten sonra) görsel ve grafik "
            "eklemek maliyet açısından daha verimlidir — ama istediğin an ekleyebilirsin."
        )
        if st.button("🎨 GÖRSEL VE GRAFİK EKLE", disabled=not can_run):
            try:
                with st.spinner("Görseller ve grafikler oluşturuluyor..."):
                    enriched, enrich_warnings = enrich_article_with_media(
                        st.session_state["article_markdown"], api_key, image_model,
                        safe_filename(focus_keyword or topic),
                    )
                st.session_state["article_markdown"] = enriched
                st.session_state["media_enriched"] = True
                for w in enrich_warnings:
                    st.warning(w)
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - enrichment must never crash the app
                st.warning(f"Görsel/grafik ekleme sırasında hata oluştu, makale metni etkilenmedi: {exc}")
    else:
        st.caption("✅ Görsel ve grafikler eklendi.")

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
                    st.session_state["media_enriched"] = False
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
                    st.session_state["media_enriched"] = False
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

        st.subheader("Wagtail için HTML")
        st.caption(
            "Markdown'ı (tablo, başlık, kalın yazı dahil) doğrudan Wagtail'in RawHTMLBlock'una "
            "yapıştırılabilecek gerçek HTML'e çevirir — düz RichText alanına değil, RawHTMLBlock'a "
            "yapıştır, aksi halde CTA/kutu/grafik stilleri kaybolur."
        )
        article_only = extract_section(st.session_state["article_markdown"], "Article")
        article_html = convert_article_to_html(article_only)
        with st.expander("Kopyala: HTML çıktısı", expanded=False):
            st.code(article_html, language="html")
        st.download_button(
            "Download HTML",
            data=article_html,
            file_name=f"{safe_filename(focus_keyword or topic)}.html",
            mime="text/html",
        )
