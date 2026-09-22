import re

import httpx

from utils import extract_section, parse_metadata_field, slugify_focus_keyword

SENTENCE_SPLIT_RE = re.compile(r"[.!?]+(?:\s+|$)")
URL_RE = re.compile(r"https?://[^\s)>\]]+")


def _clean_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[#*_`>|]", " ", text)
    return text


def count_words(text: str) -> int:
    cleaned = _clean_text(text)
    return len(re.findall(r"\b[\w'-]+\b", cleaned, flags=re.UNICODE))


def count_exact_keyword(text: str, keyword: str) -> int:
    if not keyword or not keyword.strip():
        return 0
    pattern = r"\b" + re.escape(keyword.strip()) + r"\b"
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def calculate_keyword_density(text: str, keyword: str) -> float:
    total_words = count_words(text)
    if total_words == 0:
        return 0.0
    keyword_word_count = max(len(keyword.strip().split()), 1)
    occurrences = count_exact_keyword(text, keyword)
    return round((occurrences * keyword_word_count) / total_words * 100, 3)


def _contains_keyword(text: str, keyword: str) -> bool:
    return count_exact_keyword(text, keyword) > 0


def keyword_in_title(title: str, keyword: str) -> bool:
    return _contains_keyword(title, keyword)


def keyword_in_h1(article_md: str, keyword: str) -> bool:
    h1_matches = re.findall(r"^#\s+(.+)$", article_md, flags=re.MULTILINE)
    return any(_contains_keyword(h1, keyword) for h1 in h1_matches)


def keyword_in_first_100_words(text: str, keyword: str) -> bool:
    cleaned = _clean_text(text)
    words = re.findall(r"\b[\w'-]+\b", cleaned, flags=re.UNICODE)
    first_100 = " ".join(words[:100])
    return _contains_keyword(first_100, keyword)


def keyword_in_h2(article_md: str, keyword: str) -> bool:
    h2_matches = re.findall(r"^##\s+(.+)$", article_md, flags=re.MULTILINE)
    return any(_contains_keyword(h2, keyword) for h2 in h2_matches)


def keyword_in_meta(meta_description: str, keyword: str) -> bool:
    return _contains_keyword(meta_description, keyword)


def keyword_in_slug(slug: str, keyword: str) -> bool:
    return slugify_focus_keyword(keyword) in slug.lower()


def extract_urls(text: str) -> list:
    return URL_RE.findall(text)


def count_internal_links(internal_links_section: str) -> int:
    return len(re.findall(r"^\s*URL:\s*\S+", internal_links_section, flags=re.MULTILINE))


def count_external_links(external_sources_section: str) -> int:
    return len(extract_urls(external_sources_section))


def count_sources(external_sources_section: str) -> int:
    return len(re.findall(r"^-\s+\S", external_sources_section, flags=re.MULTILINE))


def count_statistics(statistics_section: str) -> int:
    return len(re.findall(r"^-\s+\S", statistics_section, flags=re.MULTILINE))


def has_table(text: str) -> bool:
    return bool(re.search(r"^\|.+\|\s*$", text, flags=re.MULTILINE))


def has_image_recommendation(image_section: str) -> bool:
    return bool(re.search(r"concept:", image_section, flags=re.IGNORECASE))


def calculate_long_sentence_ratio(text: str, threshold: int = 20) -> float:
    cleaned = _clean_text(text)
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(cleaned) if s.strip()]
    if not sentences:
        return 0.0
    long_count = sum(1 for s in sentences if len(s.split()) > threshold)
    return round(long_count / len(sentences) * 100, 2)


def find_long_paragraphs(text: str, threshold: int = 150) -> list:
    paragraphs = [
        p.strip()
        for p in text.split("\n\n")
        if p.strip() and not p.strip().startswith("#") and not p.strip().startswith("|")
    ]
    long_paragraphs = []
    for p in paragraphs:
        word_count = len(p.split())
        if word_count > threshold:
            long_paragraphs.append({"word_count": word_count, "preview": p[:80]})
    return long_paragraphs


BLOCKED_STATUS_CODES = {401, 403, 405, 406, 429, 999}


def verify_urls_reachable(urls: list, timeout: float = 8.0) -> dict:
    """Real HTTP check for every URL.

    - 404/410/DNS failure/connection error -> genuinely unreachable ("fake URL" candidate).
    - 401/403/405/406/429/999 -> many legitimate .gov/.edu/.org sites return these to
      non-browser requests via bot protection (Cloudflare, Akamai, etc). Treating them as a
      hard fail would punish exactly the high-authority sources the spec prioritizes, so
      these are reported as "blocked" (a warning), never as "unreachable".
    """
    results = {}
    unique_urls = {u for u in urls if u}
    if not unique_urls:
        return results

    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}) as client:
        for url in unique_urls:
            try:
                resp = client.head(url)
                if resp.status_code >= 400:
                    resp = client.get(url)
                status = resp.status_code
                if status < 400:
                    results[url] = {"reachable": True, "status_code": status, "blocked": False}
                elif status in BLOCKED_STATUS_CODES:
                    results[url] = {"reachable": True, "status_code": status, "blocked": True}
                else:
                    results[url] = {"reachable": False, "status_code": status, "blocked": False}
            except httpx.HTTPError as exc:
                results[url] = {"reachable": False, "status_code": None, "blocked": False, "error": str(exc)}
    return results


def run_python_seo_checks(full_markdown: str, focus_keyword: str, target_word_count: int) -> dict:
    """Deterministic checks per SPEC section 47-49. Runs on the Writer's full markdown output."""
    metadata_section = extract_section(full_markdown, "SEO Metadata")
    article_section = extract_section(full_markdown, "Article")
    internal_links_section = extract_section(full_markdown, "Internal Links")
    external_sources_section = extract_section(full_markdown, "External Sources Used")
    statistics_section = extract_section(full_markdown, "Statistics Used")
    image_section = extract_section(full_markdown, "Image Recommendations")
    table_chart_section = extract_section(full_markdown, "Table / Chart / Diagram Notes")

    seo_title = parse_metadata_field(metadata_section, "SEO Title")
    h1_field = parse_metadata_field(metadata_section, "H1")
    slug = parse_metadata_field(metadata_section, "Slug")
    meta_description = parse_metadata_field(metadata_section, "Meta Description")
    excerpt = parse_metadata_field(metadata_section, "Excerpt")

    word_count = count_words(article_section)
    tolerance = target_word_count * 0.10 if target_word_count else 0

    all_urls = (
        extract_urls(article_section)
        + extract_urls(internal_links_section)
        + extract_urls(external_sources_section)
        + extract_urls(statistics_section)
    )
    url_check = verify_urls_reachable(all_urls)
    unreachable_urls = [url for url, info in url_check.items() if not info["reachable"]]
    blocked_urls = [url for url, info in url_check.items() if info.get("blocked")]

    report = {
        "word_count": word_count,
        "target_word_count": target_word_count,
        "word_count_within_tolerance": bool(target_word_count) and abs(word_count - target_word_count) <= tolerance,
        "focus_keyword_count": count_exact_keyword(article_section, focus_keyword),
        "keyword_density_percent": calculate_keyword_density(article_section, focus_keyword),
        "keyword_in_seo_title": keyword_in_title(seo_title, focus_keyword),
        "keyword_in_h1": keyword_in_h1(article_section, focus_keyword) or keyword_in_title(h1_field, focus_keyword),
        "keyword_in_first_100_words": keyword_in_first_100_words(article_section, focus_keyword),
        "keyword_in_h2": keyword_in_h2(article_section, focus_keyword),
        "keyword_in_meta_description": keyword_in_meta(meta_description, focus_keyword),
        "keyword_in_slug": keyword_in_slug(slug, focus_keyword) if slug else False,
        "seo_title_char_count": len(seo_title),
        "meta_description_char_count": len(meta_description),
        "excerpt_word_count": len(excerpt.split()) if excerpt else 0,
        "h1_count": len(re.findall(r"^#\s+.+$", article_section, flags=re.MULTILINE)),
        "h2_count": len(re.findall(r"^##\s+.+$", article_section, flags=re.MULTILINE)),
        "internal_link_count": count_internal_links(internal_links_section),
        "external_link_count": count_external_links(external_sources_section),
        "source_count": count_sources(external_sources_section),
        "statistic_count": count_statistics(statistics_section),
        "has_table": has_table(article_section) or has_table(table_chart_section),
        "has_chart_or_diagram_recommendation": bool(table_chart_section.strip()),
        "has_image_recommendation": has_image_recommendation(image_section),
        "long_sentence_ratio_percent": calculate_long_sentence_ratio(article_section),
        "long_paragraphs": find_long_paragraphs(article_section),
        "url_check": url_check,
        "unreachable_urls": unreachable_urls,
        "blocked_urls": blocked_urls,
    }

    hard_fails = []
    warnings = []
    if unreachable_urls:
        hard_fails.append(f"Fake/unreachable URL(s): {', '.join(unreachable_urls)}")
    if blocked_urls:
        warnings.append(
            f"URL(s) returned a bot-protection status (401/403/406/429) and could not be "
            f"auto-verified, but were not treated as fake: {', '.join(blocked_urls)}"
        )
    if not report["keyword_in_h1"] or not report["keyword_in_seo_title"] or not report["keyword_in_slug"]:
        hard_fails.append("Focus keyword missing from a critical location (title/H1/slug).")
    if report["keyword_density_percent"] == 0.0:
        hard_fails.append("Focus keyword not found in article body — may have been changed or dropped.")
    if target_word_count and word_count < target_word_count * 0.7:
        hard_fails.append("Article word count is massively below the requested target.")

    report["hard_fails"] = hard_fails
    report["warnings"] = warnings
    return report
