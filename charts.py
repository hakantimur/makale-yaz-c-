import base64
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHART_FIELDS = ["Chart Type", "Title", "X Axis", "Y Axis", "Data", "Source", "Live URL"]
CHART_BLOCK_RE = re.compile(r"CHART RECOMMENDATION\s*\n(.*?)(?=\n\n|\Z)", flags=re.DOTALL)
DATA_PAIR_RE = re.compile(r"([^:\n,;]+):\s*([\d]+(?:[.,]\d+)?)\s*%?")

CHART_COLOR = "#e8734a"


def _extract_field(block: str, field: str, next_fields: list) -> str:
    if next_fields:
        next_pattern = "|".join(re.escape(f) for f in next_fields)
        pattern = rf"{re.escape(field)}:\s*(.*?)(?=\n(?:{next_pattern}):|\Z)"
    else:
        pattern = rf"{re.escape(field)}:\s*(.*)"
    match = re.search(pattern, block, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def find_chart_blocks(article_text: str) -> list:
    """Finds every 'CHART RECOMMENDATION' block the Writer embedded and parses its fields."""
    blocks = []
    for match in CHART_BLOCK_RE.finditer(article_text):
        block_text = match.group(1)
        spec = {}
        for i, field in enumerate(CHART_FIELDS):
            spec[field] = _extract_field(block_text, field, CHART_FIELDS[i + 1:])
        spec["_full_match"] = match.group(0)
        blocks.append(spec)
    return blocks


def parse_data_pairs(data_text: str) -> list:
    """Best-effort parse of '<label>: <number>' pairs out of the Writer's free-text Data field."""
    pairs = []
    for match in DATA_PAIR_RE.finditer(data_text):
        label = match.group(1).strip(" -*\n")
        try:
            value = float(match.group(2).replace(",", "."))
        except ValueError:
            continue
        if label:
            pairs.append((label, value))
    return pairs


def render_chart(spec: dict, pairs: list, out_path: str) -> bool:
    if not pairs:
        return False
    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]
    chart_type = (spec.get("Chart Type") or "").lower()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    if "pie" in chart_type:
        ax.pie(values, labels=labels, autopct="%1.0f%%", colors=plt.cm.Oranges(
            [0.4 + 0.5 * i / max(len(values) - 1, 1) for i in range(len(values))]
        ))
    elif "line" in chart_type:
        ax.plot(labels, values, marker="o", color=CHART_COLOR)
        ax.set_ylabel(spec.get("Y Axis") or "")
        ax.set_xlabel(spec.get("X Axis") or "")
        ax.spines[["top", "right"]].set_visible(False)
    else:
        ax.bar(labels, values, color=CHART_COLOR)
        ax.set_ylabel(spec.get("Y Axis") or "")
        ax.set_xlabel(spec.get("X Axis") or "")
        ax.spines[["top", "right"]].set_visible(False)

    ax.set_title(spec.get("Title") or "")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    return True


def render_charts_in_article(article_text: str, slug: str, output_dir: str = "outputs/images") -> tuple:
    """Replaces every CHART RECOMMENDATION text block with a real rendered chart image.
    Never raises — a chart that can't be parsed/rendered is skipped with a warning,
    the article is never blocked by a chart failure."""
    warnings = []
    new_text = article_text
    for i, spec in enumerate(find_chart_blocks(article_text), start=1):
        try:
            pairs = parse_data_pairs(spec.get("Data", ""))
            if not pairs:
                warnings.append(f"Grafik {i}: sayısal veri ayrıştırılamadı, atlandı.")
                continue

            filename = f"chart-{i}.svg"
            folder = os.path.join(output_dir, slug)
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, filename)

            if not render_chart(spec, pairs, path):
                warnings.append(f"Grafik {i}: oluşturulamadı, atlandı.")
                continue

            with open(path, "rb") as f:
                svg_bytes = f.read()
            data_uri = "data:image/svg+xml;base64," + base64.b64encode(svg_bytes).decode("ascii")
            title = spec.get("Title", "")
            source = spec.get("Source", "")
            url = spec.get("Live URL", "")
            if url:
                caption_source = f' — Kaynak: <a href="{url}">{source or url}</a>'
            elif source:
                caption_source = f" — Kaynak: {source}"
            else:
                caption_source = ""

            figure_html = (
                f'<figure class="noritales-chart">\n'
                f'  <img src="{data_uri}" alt="{title}">\n'
                f'  <figcaption>{title}{caption_source}</figcaption>\n'
                f"</figure>"
            )
            new_text = new_text.replace(spec["_full_match"], figure_html, 1)
        except Exception as exc:  # noqa: BLE001 - chart rendering must never block the article
            warnings.append(f"Grafik {i}: beklenmeyen hata ({exc}), atlandı.")
    return new_text, warnings
