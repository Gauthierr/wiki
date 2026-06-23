"""Point d'entrée : collecte les agendas, génère le PDF, publie sur reMarkable.

Usage :
    python -m src.main                 # génère le PDF et le publie sur reMarkable
    python -m src.main --no-upload     # génère seulement le PDF (test local)

Variables d'environnement :
    ICS_OUTLOOK, ICS_GMAIL, ICS_INFOMANIAK : URLs iCal secrètes des agendas.
    SKIP_UPLOAD=1 : équivaut à --no-upload.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from . import remarkable
from .calendars import collect_all_events
from .config import load_config
from .render import render_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agenda")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agenda quotidien -> PDF -> reMarkable")
    parser.add_argument(
        "--config", default="config.yaml", help="Chemin du fichier de config YAML."
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Ne pas publier sur reMarkable (génère seulement le PDF).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)

    try:
        tz = ZoneInfo(config.timezone)
    except Exception:  # noqa: BLE001
        logger.warning("Fuseau « %s » inconnu, repli sur UTC.", config.timezone)
        tz = ZoneInfo("UTC")

    logger.info(
        "Collecte des agendas sur %d jour(s) (fuseau %s)…",
        config.days_ahead,
        config.timezone,
    )
    events, first_day, last_day = collect_all_events(
        config.calendars, config.days_ahead, tz
    )
    logger.info("Total : %d événement(s) sur la période.", len(events))

    output_name = f"Agenda {first_day.isoformat()}.pdf"
    output_path = Path(config.output_dir) / output_name
    render_pdf(
        events,
        first_day,
        last_day,
        output_path,
        title=config.title,
        generated_at=dt.datetime.now(tz),
    )
    logger.info("PDF généré : %s", output_path)

    skip_upload = args.no_upload or os.environ.get("SKIP_UPLOAD") == "1"
    if skip_upload:
        logger.info("Publication reMarkable ignorée (--no-upload).")
        return 0

    try:
        remarkable.ensure_folder(config.remarkable_folder)
        remarkable.upload(output_path, config.remarkable_folder)
        remarkable.cleanup(config.remarkable_folder, "Agenda ", config.keep_last)
    except remarkable.RemarkableError as exc:
        logger.error("Échec de la publication sur reMarkable :\n%s", exc)
        return 1

    logger.info("Terminé ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
