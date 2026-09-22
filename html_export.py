import markdown

MARKDOWN_EXTENSIONS = ["tables", "fenced_code", "nl2br"]


def convert_article_to_html(article_section: str) -> str:
    """Converts the Writer's markdown article body into real HTML — headings, bold,
    links and (critically) pipe tables all become real HTML tags instead of literal
    markdown syntax. Any raw HTML already embedded by the Writer (CTA buttons, stat
    cards, quote/tip boxes, chart/image figures) passes through untouched, since
    Python-Markdown preserves inline/raw HTML blocks by default.

    This is what makes the article safe to paste into a Wagtail RawHTMLBlock (or any
    other raw-HTML sink) — pasting the original markdown directly would leave table
    pipes, '#' headings and '**bold**' as literal visible text, since those targets do
    not run a markdown parser themselves.
    """
    return markdown.markdown(article_section, extensions=MARKDOWN_EXTENSIONS)
