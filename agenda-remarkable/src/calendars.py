"""Récupération et fusion des événements depuis des URLs iCal (.ics)."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import recurring_ical_events
import requests
from icalendar import Calendar

from .config import CalendarSource

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


@dataclass
class Event:
    summary: str
    start: dt.datetime  # toujours « aware » (fuseau local)
    end: dt.datetime | None
    all_day: bool
    location: str
    source: str

    @property
    def day(self) -> dt.date:
        return self.start.date()


def _fetch_ics(url: str) -> str:
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _to_local_datetime(value, tz: ZoneInfo) -> tuple[dt.datetime, bool]:
    """Normalise une valeur DTSTART/DTEND en datetime « aware » local.

    Retourne (datetime, all_day).
    """
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=tz)
        return value.astimezone(tz), False
    # `value` est une date (événement « toute la journée »)
    return dt.datetime(value.year, value.month, value.day, tzinfo=tz), True


def fetch_events(
    source: CalendarSource,
    window_start: dt.datetime,
    window_end: dt.datetime,
    tz: ZoneInfo,
) -> list[Event]:
    """Récupère et développe les événements d'une source sur la fenêtre donnée."""
    url = source.url
    if not url:
        logger.warning(
            "Calendrier « %s » ignoré : variable %s vide ou absente.",
            source.name,
            source.url_env,
        )
        return []

    try:
        raw = _fetch_ics(url)
        calendar = Calendar.from_ical(raw)
    except Exception as exc:  # noqa: BLE001 - on isole une source défaillante
        logger.error("Échec de récupération de « %s » : %s", source.name, exc)
        return []

    occurrences = recurring_ical_events.of(calendar).between(window_start, window_end)

    events: list[Event] = []
    for component in occurrences:
        dtstart = component.get("DTSTART")
        if dtstart is None:
            continue
        start, all_day = _to_local_datetime(dtstart.dt, tz)

        end = None
        dtend = component.get("DTEND")
        if dtend is not None:
            end, _ = _to_local_datetime(dtend.dt, tz)

        summary = str(component.get("SUMMARY", "(sans titre)")).strip()
        location = str(component.get("LOCATION", "")).strip()

        events.append(
            Event(
                summary=summary,
                start=start,
                end=end,
                all_day=all_day,
                location=location,
                source=source.name,
            )
        )

    logger.info("Calendrier « %s » : %d événement(s).", source.name, len(events))
    return events


def collect_all_events(
    sources: list[CalendarSource], days_ahead: int, tz: ZoneInfo
) -> tuple[list[Event], dt.date, dt.date]:
    """Collecte et trie tous les événements sur la fenêtre [aujourd'hui, +N jours[.

    Retourne (événements triés, premier jour, dernier jour inclus).
    """
    today = dt.datetime.now(tz).date()
    first_day = today
    last_day = today + dt.timedelta(days=days_ahead - 1)

    window_start = dt.datetime.combine(first_day, dt.time.min, tzinfo=tz)
    window_end = dt.datetime.combine(last_day, dt.time.max, tzinfo=tz)

    all_events: list[Event] = []
    for source in sources:
        all_events.extend(fetch_events(source, window_start, window_end, tz))

    # Tri : par jour, puis « toute la journée » d'abord, puis par heure de début.
    all_events.sort(key=lambda e: (e.start.date(), not e.all_day, e.start))
    return all_events, first_day, last_day
