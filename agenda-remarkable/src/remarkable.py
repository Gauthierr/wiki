"""Publication du PDF sur le cloud reMarkable via l'outil `rmapi`.

`rmapi` (https://github.com/ddvk/rmapi) doit être installé et authentifié.
En CI, l'authentification provient du secret RMAPI_CONF écrit dans
~/.config/rmapi/rmapi.conf.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class RemarkableError(RuntimeError):
    pass


def _run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    logger.debug("rmapi %s", " ".join(args))
    result = subprocess.run(
        ["rmapi", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RemarkableError(
            f"`rmapi {' '.join(args)}` a échoué (code {result.returncode}) :\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def ensure_folder(folder: str) -> None:
    """Crée le dossier cible s'il n'existe pas (ignore l'erreur s'il existe déjà)."""
    folder = folder.rstrip("/") or "/"
    if folder == "/":
        return
    result = _run(["mkdir", folder], check=False)
    if result.returncode != 0 and "exist" not in (result.stdout + result.stderr).lower():
        # On log mais on n'échoue pas : le dossier existe probablement déjà.
        logger.info("mkdir %s : %s", folder, (result.stdout + result.stderr).strip())


def upload(pdf_path: str | Path, folder: str) -> None:
    """Téléverse le PDF dans le dossier reMarkable indiqué."""
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise RemarkableError(f"Fichier introuvable : {pdf_path}")
    folder = folder.rstrip("/") or "/"
    _run(["put", str(pdf_path), folder])
    logger.info("Téléversé sur reMarkable : %s -> %s", pdf_path.name, folder)


def cleanup(folder: str, prefix: str, keep_last: int) -> None:
    """Conserve les `keep_last` documents les plus récents dont le nom commence par `prefix`.

    Best-effort : toute erreur est journalisée mais n'interrompt pas le programme.
    """
    if keep_last <= 0:
        return
    folder = folder.rstrip("/") or "/"
    try:
        result = _run(["ls", folder], check=False)
        if result.returncode != 0:
            return
        # Les lignes de fichiers (pas dossiers) commençant par le préfixe.
        names = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("[d]"):
                continue
            name = re.sub(r"^\[f\]\s*", "", line).strip()
            if name.startswith(prefix):
                names.append(name)
        # Le préfixe inclut une date ISO -> tri alphabétique == tri chronologique.
        names.sort()
        to_delete = names[:-keep_last] if len(names) > keep_last else []
        for name in to_delete:
            path = f"{folder}/{name}"
            res = _run(["rm", path], check=False)
            if res.returncode == 0:
                logger.info("Ancien document supprimé : %s", path)
    except Exception as exc:  # noqa: BLE001 - nettoyage non critique
        logger.warning("Nettoyage reMarkable ignoré : %s", exc)
