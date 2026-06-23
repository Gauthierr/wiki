"""Chargement de la configuration (fichier YAML + variables d'environnement)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class CalendarSource:
    name: str
    url_env: str

    @property
    def url(self) -> str | None:
        value = os.environ.get(self.url_env, "").strip()
        return value or None


@dataclass
class Config:
    timezone: str = "Europe/Paris"
    days_ahead: int = 7
    output_dir: str = "out"
    title: str = "Mon agenda"
    remarkable_folder: str = "/Agenda"
    keep_last: int = 7
    calendars: list[CalendarSource] = field(default_factory=list)


DEFAULT_CALENDARS = [
    {"name": "Outlook", "url_env": "ICS_OUTLOOK"},
    {"name": "Gmail", "url_env": "ICS_GMAIL"},
    {"name": "Infomaniak", "url_env": "ICS_INFOMANIAK"},
]


def load_config(path: str | os.PathLike[str] = "config.yaml") -> Config:
    """Charge la config depuis `path` s'il existe, sinon utilise les défauts.

    Le fichier de config est optionnel : en CI on s'appuie sur les défauts et
    les URLs d'agenda sont fournies via les variables d'environnement (secrets).
    """
    data: dict = {}
    config_path = Path(path)
    if config_path.is_file():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    raw_calendars = data.get("calendars") or DEFAULT_CALENDARS
    calendars = [
        CalendarSource(name=c["name"], url_env=c["url_env"]) for c in raw_calendars
    ]

    return Config(
        timezone=data.get("timezone", "Europe/Paris"),
        days_ahead=int(data.get("days_ahead", 7)),
        output_dir=data.get("output_dir", "out"),
        title=data.get("title", "Mon agenda"),
        remarkable_folder=data.get("remarkable_folder", "/Agenda"),
        keep_last=int(data.get("keep_last", 7)),
        calendars=calendars,
    )
