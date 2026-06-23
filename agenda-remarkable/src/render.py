"""Génération du PDF lisible (mise en page adaptée à l'écran reMarkable)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .calendars import Event

JOURS = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
]
MOIS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]

# Palette de couleurs par source d'agenda.
SOURCE_COLORS = [
    colors.HexColor("#1a73e8"),  # bleu
    colors.HexColor("#d93025"),  # rouge
    colors.HexColor("#188038"),  # vert
    colors.HexColor("#8430ce"),  # violet
    colors.HexColor("#e37400"),  # orange
]


def _french_date(d: dt.date) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


def _time_label(event: Event) -> str:
    if event.all_day:
        return "Journée"
    start = event.start.strftime("%H:%M")
    if event.end is not None and event.end != event.start:
        return f"{start}–{event.end.strftime('%H:%M')}"
    return start


def _source_color_map(events: list[Event]) -> dict[str, colors.Color]:
    names = []
    for e in events:
        if e.source not in names:
            names.append(e.source)
    return {name: SOURCE_COLORS[i % len(SOURCE_COLORS)] for i, name in enumerate(names)}


def render_pdf(
    events: list[Event],
    first_day: dt.date,
    last_day: dt.date,
    output_path: str | Path,
    title: str = "Mon agenda",
    generated_at: dt.datetime | None = None,
) -> Path:
    """Construit le PDF et le retourne sous forme de chemin."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AgTitle", parent=styles["Title"], fontSize=20, spaceAfter=2, alignment=TA_LEFT
    )
    subtitle_style = ParagraphStyle(
        "AgSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=10,
    )
    day_style = ParagraphStyle(
        "AgDay",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#202124"),
        spaceBefore=10,
        spaceAfter=4,
    )
    today_style = ParagraphStyle(
        "AgToday",
        parent=day_style,
        textColor=colors.HexColor("#1a73e8"),
    )
    time_style = ParagraphStyle(
        "AgTime", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold"
    )
    summary_style = ParagraphStyle("AgSummary", parent=styles["Normal"], fontSize=10)
    meta_style = ParagraphStyle(
        "AgMeta", parent=styles["Normal"], fontSize=8, textColor=colors.grey
    )
    empty_style = ParagraphStyle(
        "AgEmpty", parent=styles["Normal"], fontSize=9, textColor=colors.grey
    )

    color_map = _source_color_map(events)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A5,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=title,
    )

    flow = []
    flow.append(Paragraph(title, title_style))
    period = f"{_french_date(first_day)} → {_french_date(last_day)}"
    if generated_at is not None:
        period += f"  ·  généré le {generated_at.strftime('%d/%m/%Y à %H:%M')}"
    flow.append(Paragraph(period, subtitle_style))

    today = dt.date.today()
    day = first_day
    while day <= last_day:
        day_events = [e for e in events if e.day == day]
        heading = _french_date(day)
        if day == today:
            heading = "Aujourd'hui — " + heading
        flow.append(Paragraph(heading, today_style if day == today else day_style))

        if not day_events:
            flow.append(Paragraph("Aucun événement", empty_style))
        else:
            rows = []
            row_styles = []
            for i, e in enumerate(day_events):
                details = f"<b>{_escape(e.summary)}</b>"
                meta_bits = [e.source]
                if e.location:
                    meta_bits.append(e.location)
                details += f'<br/><font size="8" color="#5f6368">{_escape("  ·  ".join(meta_bits))}</font>'

                rows.append(
                    [
                        Paragraph(_time_label(e), time_style),
                        Paragraph(details, summary_style),
                    ]
                )
                # Barre de couleur de la source dans la marge gauche.
                row_styles.append(
                    ("LINEBEFORE", (0, i), (0, i), 2.5, color_map.get(e.source, colors.grey))
                )

            table = Table(rows, colWidths=[22 * mm, None], hAlign="LEFT")
            base_style = [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 6),
            ]
            table.setStyle(TableStyle(base_style + row_styles))
            flow.append(table)

        day += dt.timedelta(days=1)

    if not events:
        flow.append(Spacer(1, 6 * mm))
        flow.append(
            Paragraph(
                "Aucun événement sur la période — ou aucune URL iCal configurée.",
                meta_style,
            )
        )

    doc.build(flow)
    return output_path


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
