import os
import re
import unicodedata


def slugify_focus_keyword(text: str) -> str:
    """URL-safe slug. Preserves word order, only strips characters that aren't URL-safe."""
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text


def safe_filename(name: str) -> str:
    slug = slugify_focus_keyword(name)
    return slug or "article"


def save_markdown(content: str, base_filename: str, output_dir: str = "outputs") -> str:
    """Saves content, never overwriting: appends -2, -3, ... if the file already exists."""
    os.makedirs(output_dir, exist_ok=True)
    base_filename = safe_filename(base_filename)

    filename = f"{base_filename}.md"
    path = os.path.join(output_dir, filename)
    counter = 2
    while os.path.exists(path):
        filename = f"{base_filename}-{counter}.md"
        path = os.path.join(output_dir, filename)
        counter += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def extract_section(markdown_text: str, header: str) -> str:
    """Extracts the body of a top-level '# Header' block. Writer output separates top-level
    sections with '---' horizontal rules, so we split on those instead of on '# ' lines —
    a naive '# ' split would stop at the article's own nested H1/H2 headings."""
    blocks = re.split(r"^-{3,}\s*$", markdown_text, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        first_line = lines[0].strip()
        if re.match(rf"^#\s+{re.escape(header)}\s*$", first_line, flags=re.IGNORECASE):
            return "\n".join(lines[1:]).strip()
    return ""


def enforce_assignment_fields(prompt_text: str, overrides: dict) -> str:
    """Force-overwrites deterministic ARTICLE ASSIGNMENT fields (topic, focus keyword,
    language, target market, word count) with the application's exact values. Models
    reliably hallucinate small edits to these (e.g. rounding word count) if left to their
    own devices — the same reasoning as never trusting the model with the focus keyword
    or with URLs; these facts must come from the app, not from generation."""
    for field, value in overrides.items():
        pattern = rf"^{re.escape(field)}:\s*\n.*?(?=\n\n|\Z)"
        replacement = f"{field}:\n{value}"
        if re.search(pattern, prompt_text, flags=re.MULTILINE | re.DOTALL):
            prompt_text = re.sub(pattern, replacement, prompt_text, count=1, flags=re.MULTILINE | re.DOTALL)
        else:
            prompt_text = prompt_text.replace(
                "ARTICLE ASSIGNMENT", f"ARTICLE ASSIGNMENT\n\n{field}:\n{value}", 1
            )
    return prompt_text


def parse_metadata_field(section_text: str, field_name: str) -> str:
    """Extracts a '**Field Name:** value' line's value from a markdown section."""
    pattern = rf"\*\*{re.escape(field_name)}:\*\*\s*(.+)"
    match = re.search(pattern, section_text)
    return match.group(1).strip() if match else ""
