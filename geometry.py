"""
geometry.py

Classi dati e utilità geometriche per il nesting.
"""

from dataclasses import dataclass
from typing import List
import os


@dataclass
class LayoutRow:
    """Rappresenta un pannello posizionato su una lastra."""
    sheet: int
    idx: int
    x: float
    y: float
    width: float
    height: float
    rotated: bool
    panel_id: str = ""
    panel_number: str = ""


def _safe_num(x: str) -> float:
    """Converte una stringa in numero float, gestendo formati problematici."""
    try:
        s = str(x).strip().replace(",", ".")
        return float("".join(ch for ch in s if (ch.isdigit() or ch == "."))) if any(c.isdigit() for c in s) else float("inf")
    except:
        return float("inf")


def sort_parts_within_sheet(parts: List[LayoutRow]) -> List[LayoutRow]:
    """Ordina i pannelli dentro una lastra per panel_id, poi panel_number numerico, poi y, x."""
    return sorted(parts, key=lambda p: (str(p.panel_id), _safe_num(p.panel_number), p.y, p.x))


def prepare_output_dirs(prefix: str) -> dict:
    """
    Crea cartella base ./<prefix>/ con sottocartelle dxf/ e png/.
    Ritorna dict con path utili: {"root":..., "dxf":..., "png":...}
    """
    base = os.path.abspath(prefix)
    dxf_dir = os.path.join(base, "dxf")
    png_dir = os.path.join(base, "png")
    os.makedirs(dxf_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    return {"root": base, "dxf": dxf_dir, "png": png_dir}


def _ensure_dir(p):
    """Utility: crea directory se non esiste."""
    os.makedirs(p, exist_ok=True)
    return p


def _unique_preserve(seq):
    """Rimuove duplicati preservando l'ordine."""
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out