import re

import bleach
import markdown

MARKDOWN_EXTENSIONS = ["tables", "fenced_code", "nl2br"]

ALLOWED_TAGS = [
    "a", "blockquote", "cite", "div", "figure", "figcaption", "img", "span",
    "strong", "em", "b", "i", "h1", "h2", "h3", "h4", "p", "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "td", "th", "br", "code", "pre",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "class"],
    "img": ["src", "alt", "class"],
    "div": ["class"],
    "span": ["class"],
    "blockquote": ["class"],
    "figure": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "data"]

NORITALES_CLASS_RE = re.compile(r"^noritales-[a-z-]+$")
CLASS_ATTR_RE = re.compile(r'\sclass="([^"]*)"')


def _strip_disallowed_classes(html_content: str) -> str:
    """bleach only checks whether 'class' is an allowed attribute name, not its value —
    this restricts class values to our known noritales-* set so LLM-derived content can't
    smuggle in arbitrary classes for CSS-based mischief on the publishing site."""

    def repl(match):
        classes = [c for c in match.group(1).split() if NORITALES_CLASS_RE.match(c)]
        return f' class="{" ".join(classes)}"' if classes else ""

    return CLASS_ATTR_RE.sub(repl, html_content)


def sanitize_html(html_content: str) -> str:
    """Allowlist-sanitizes HTML before it is rendered or exported. Research pulls in live
    web content and the Writer can quote it — this is the defense against a prompt
    injection or adversarial source smuggling a <script>, an event handler, or a
    javascript:/data: href into what ends up as raw HTML on a real, published site."""
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return _strip_disallowed_classes(cleaned)


def convert_article_to_html(article_section: str) -> str:
    """Converts the Writer's markdown article body into real, sanitized HTML — headings,
    bold, links and (critically) pipe tables all become real HTML tags instead of literal
    markdown syntax. Any raw HTML already embedded by the Writer (CTA buttons, stat
    cards, quote/tip boxes, chart/image figures) passes through, but is run through an
    allowlist sanitizer first — this is what makes the article safe to paste into a
    Wagtail RawHTMLBlock (or any other raw-HTML sink), both because pasting the original
    markdown directly would leave table pipes/'#'/'**' as literal visible text (those
    targets don't run a markdown parser), and because the content includes live web
    research the Writer may have quoted, which is not a trusted source.
    """
    raw_html = markdown.markdown(article_section, extensions=MARKDOWN_EXTENSIONS)
    return sanitize_html(raw_html)
