import base64
import ipaddress
import json
import socket
from urllib.parse import urlparse

import httpx

from prompts import (
    ARTICLE_PROMPT_BUILDER_SYSTEM_PROMPT,
    EVALUATOR_SYSTEM_PROMPT,
    REGENERATION_PROMPT_TEMPLATE,
    RESEARCH_SYSTEM_PROMPT,
    REVISION_PROMPT_TEMPLATE,
    WRITER_SYSTEM_PROMPT,
)
from config import NORITALES_HOMEPAGE_URL
from utils import enforce_assignment_fields, strip_embedded_media_for_llm

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterError(Exception):
    """User-facing error. Raw stack traces must never reach the Streamlit UI."""


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://noritales.local",
        "X-Title": "Noritales Blog Writer",
    }


def get_models(api_key: str, base_url: str = DEFAULT_BASE_URL) -> list:
    if not api_key:
        raise OpenRouterError("OpenRouter API key is missing.")
    try:
        resp = httpx.get(f"{base_url}/models", headers=_headers(api_key), timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OpenRouterError("Could not fetch the model list from OpenRouter.") from exc
    return resp.json().get("data", [])


def get_image_models(api_key: str, base_url: str = DEFAULT_BASE_URL) -> list:
    """Dedicated image-generation models (e.g. GPT Image 2.5 Flare, Nano Banana) live in a
    separate catalog from the chat-completions '/models' list — many of them have no text
    output at all and 404 on /chat/completions, so they never appear there."""
    if not api_key:
        raise OpenRouterError("OpenRouter API key is missing.")
    try:
        resp = httpx.get(f"{base_url}/images/models", headers=_headers(api_key), timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OpenRouterError("Could not fetch the image model list from OpenRouter.") from exc
    return resp.json().get("data", [])


def call_model(
    api_key: str,
    model: str,
    messages: list,
    web_search: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 180.0,
) -> dict:
    if not api_key:
        raise OpenRouterError("OpenRouter API key is missing.")
    if not model:
        raise OpenRouterError("No model was selected for this step.")

    payload = {"model": model, "messages": messages}
    if web_search:
        payload["plugins"] = [{"id": "web"}]

    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers=_headers(api_key),
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise OpenRouterError(
            "The selected model could not complete this request. Please choose another model or retry."
        ) from exc
    except httpx.HTTPError as exc:
        raise OpenRouterError("OpenRouter request failed.") from exc

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise OpenRouterError("The model returned invalid content. Please retry.") from exc

    choices = data.get("choices") or []
    if not choices:
        raise OpenRouterError("The model returned invalid content. Please retry.")

    content = choices[0].get("message", {}).get("content", "")
    if not content or not content.strip():
        raise OpenRouterError("The model returned invalid content. Please retry.")

    return {"content": content, "usage": data.get("usage", {}), "model": model}


def research_topic(
    api_key: str,
    model: str,
    topic: str,
    focus_keyword: str,
    language: str,
    word_count: int,
    target_market: str = "",
    web_search: bool = True,
) -> dict:
    """REQUEST 1."""
    user_message = (
        f"Topic: {topic}\n"
        f"Immutable Focus Keyword: {focus_keyword}\n"
        f"Language: {language}\n"
        f"Target Word Count: {word_count}\n"
        f"Target Market: {target_market or 'Not specified'}\n"
    )
    messages = [
        {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return call_model(api_key, model, messages, web_search=web_search)


def build_article_prompt(
    api_key: str,
    model: str,
    research_pack: str,
    user_answers: str,
    topic: str,
    focus_keyword: str,
    language: str,
    word_count: int,
    target_market: str = "",
) -> dict:
    """REQUEST 2 — separate call, separate (possibly different) model from Research."""
    user_message = (
        f"Topic: {topic}\n"
        f"Immutable Focus Keyword: {focus_keyword}\n"
        f"Language: {language}\n"
        f"Target Word Count: {word_count}\n"
        f"Target Market: {target_market or 'Not specified'}\n"
        f"Noritales Homepage URL: {NORITALES_HOMEPAGE_URL}\n\n"
        f"RESEARCH PACK:\n{research_pack}\n\nUSER ANSWERS:\n{user_answers}\n"
    )
    messages = [
        {"role": "system", "content": ARTICLE_PROMPT_BUILDER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    result = call_model(api_key, model, messages, web_search=False)

    # Never trust the model to faithfully copy these — force the exact application values,
    # the same way the focus keyword and URLs are never taken on the model's word.
    result["content"] = enforce_assignment_fields(
        result["content"],
        {
            "Topic": topic,
            "Immutable Focus Keyword": focus_keyword,
            "Language": language,
            "Target Market": target_market or "Not specified",
            "Target Word Count": str(word_count),
            "Noritales Homepage URL": NORITALES_HOMEPAGE_URL,
        },
    )
    return result


def write_article(api_key: str, model: str, article_specific_prompt: str) -> dict:
    """REQUEST 3."""
    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": article_specific_prompt},
    ]
    return call_model(api_key, model, messages, web_search=False)


def evaluate_article(api_key: str, model: str, article_markdown: str, python_metrics: dict) -> dict:
    """REQUEST 4."""
    article_markdown = strip_embedded_media_for_llm(article_markdown)
    user_message = (
        f"ARTICLE:\n{article_markdown}\n\n"
        f"DETERMINISTIC PYTHON METRICS (treat as facts):\n{json.dumps(python_metrics, indent=2)}\n"
    )
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return call_model(api_key, model, messages, web_search=False)


def revise_article(api_key: str, model: str, article_markdown: str, issues: list) -> dict:
    article_markdown = strip_embedded_media_for_llm(article_markdown)
    issues_text = "\n".join(f"- {issue}" for issue in issues) or "- General quality improvements."
    user_message = REVISION_PROMPT_TEMPLATE.format(article=article_markdown, issues=issues_text)
    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return call_model(api_key, model, messages, web_search=False)


def generate_image(
    api_key: str,
    model: str,
    prompt: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 120.0,
) -> bytes:
    """Calls OpenRouter's dedicated images endpoint and returns raw image bytes. Many
    image models (e.g. GPT Image 2.5 Flare) have no text output and 404 on
    /chat/completions — /images/generations is the correct endpoint for all image
    models, both pure-image and hybrid ones like Nano Banana.
    Never blocks article completion — callers must catch OpenRouterError and skip."""
    if not api_key:
        raise OpenRouterError("OpenRouter API key is missing.")
    if not model:
        raise OpenRouterError("No image model was selected.")

    payload = {"model": model, "prompt": prompt}
    try:
        resp = httpx.post(
            f"{base_url}/images/generations", headers=_headers(api_key), json=payload, timeout=timeout
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OpenRouterError("Image generation request failed.") from exc

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise OpenRouterError("Image model returned invalid content.") from exc

    items = data.get("data") or []
    if not items:
        raise OpenRouterError("Image model returned no content.")

    item = items[0]
    b64data = item.get("b64_json")
    if b64data:
        return base64.b64decode(b64data)

    url = item.get("url", "")
    if url:
        return _fetch_remote_image_safely(url, timeout)

    raise OpenRouterError("Image model did not return an image.")


MAX_REMOTE_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB


def _is_public_url(url: str) -> bool:
    """Blocks SSRF: only http(s) URLs that resolve to a public IP are allowed. An
    image-generation model's response is not a trusted source — it could (via prompt
    injection or a buggy/malicious provider) return a URL pointing at localhost, a
    private network, or a cloud metadata endpoint (169.254.169.254)."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    for info in addr_infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_reserved
        ):
            return False
    return True


def _fetch_remote_image_safely(url: str, timeout: float) -> bytes:
    if not _is_public_url(url):
        raise OpenRouterError("Image URL failed safety validation (blocked internal/private address).")
    try:
        with httpx.stream("GET", url, timeout=timeout, follow_redirects=False) as resp:
            if resp.is_redirect:
                raise OpenRouterError("Image URL redirect was refused for safety.")
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                raise OpenRouterError("Image URL did not return an image content type.")
            chunks = []
            total = 0
            for chunk in resp.iter_bytes():
                total += len(chunk)
                if total > MAX_REMOTE_IMAGE_BYTES:
                    raise OpenRouterError("Generated image exceeded the maximum allowed size.")
                chunks.append(chunk)
            return b"".join(chunks)
    except httpx.HTTPError as exc:
        raise OpenRouterError("Could not download the generated image.") from exc


def regenerate_article(api_key: str, model: str, original_article_prompt: str, evaluator_report: str) -> dict:
    user_message = REGENERATION_PROMPT_TEMPLATE.format(
        original_prompt=original_article_prompt, evaluator_report=evaluator_report
    )
    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return call_model(api_key, model, messages, web_search=False)
