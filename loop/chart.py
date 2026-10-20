"""Dependency-free SVG grouped bar chart."""

from __future__ import annotations

from typing import Sequence
from xml.sax.saxutils import escape

PALETTE = ["#8a94a6", "#2f6fdb", "#e0832b", "#2a9d6f"]


def grouped_bar_svg(
    title: str,
    subtitle: str,
    groups: Sequence[str],
    series: dict[str, Sequence[float | None]],
    y_max: float,
    value_format: str = "{:.0%}",
    y_label: str = "",
) -> str:
    width, height = 920, 460
    left, right, top, bottom = 70, 20, 80, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    names = list(series)
    group_w = plot_w / max(1, len(groups))
    bar_w = min(36.0, group_w * 0.8 / max(1, len(names)))
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{escape(title)}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="28" font-family="sans-serif" font-size="18" font-weight="bold" fill="#1b1f24">{escape(title)}</text>',
        f'<text x="{left}" y="48" font-family="sans-serif" font-size="12" fill="#57606a">{escape(subtitle)}</text>',
    ]
    for i in range(5):
        value = y_max * i / 4
        y = top + plot_h - plot_h * i / 4
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#d0d7de" stroke-width="1"/>')
        out.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#57606a">{escape(value_format.format(value))}</text>')
    if y_label:
        out.append(f'<text x="14" y="{top + plot_h / 2:.0f}" transform="rotate(-90 14 {top + plot_h / 2:.0f})" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#57606a">{escape(y_label)}</text>')
    for gi, group in enumerate(groups):
        gx = left + gi * group_w + (group_w - bar_w * len(names)) / 2
        for si, name in enumerate(names):
            value = series[name][gi]
            if value is None:
                continue
            h = plot_h * min(value, y_max) / y_max
            x, y = gx + si * bar_w, top + plot_h - h
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w - 2:.1f}" height="{h:.1f}" fill="{PALETTE[si % len(PALETTE)]}"><title>{escape(group)} / {escape(name)}: {escape(value_format.format(value))}</title></rect>')
            out.append(f'<text x="{x + (bar_w - 2) / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#1b1f24">{escape(value_format.format(value))}</text>')
        label = group.split("-", 1)[1] if group[:3].isdigit() else group
        out.append(f'<text x="{left + gi * group_w + group_w / 2:.1f}" y="{top + plot_h + 18}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#1b1f24">{escape(group[:3] if group[:3].isdigit() else group)}</text>')
        out.append(f'<text x="{left + gi * group_w + group_w / 2:.1f}" y="{top + plot_h + 32}" text-anchor="middle" font-family="sans-serif" font-size="9" fill="#57606a">{escape(label[:22] if group[:3].isdigit() else "")}</text>')
    legend_x = left
    for si, name in enumerate(names):
        out.append(f'<rect x="{legend_x}" y="{height - 22}" width="12" height="12" fill="{PALETTE[si % len(PALETTE)]}"/>')
        out.append(f'<text x="{legend_x + 18}" y="{height - 12}" font-family="sans-serif" font-size="12" fill="#1b1f24">{escape(name)}</text>')
        legend_x += 30 + 8 * len(name)
    out.append("</svg>")
    return "\n".join(out) + "\n"
