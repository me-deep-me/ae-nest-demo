"""
ordering.py

Logiche di ordinamento lastre per la lavorazione CNC.
"""

from typing import List, Dict
from collections import defaultdict
from itertools import groupby
from geometry import LayoutRow, _safe_num


def build_run_order_cnc2(rows: List[LayoutRow], order: str = "asc") -> List[int]:
    """
    Ordinamento richiesto:
    1) LASTRE MISTE (>=2 panel_id) per prime, ordinate per min(panel_number) (asc/desc)
    2) LASTRE PURE (1 panel_id) raggruppate per panel_id; dentro ordinate per min(panel_number)
    Ritorna: lista di sheet nell'ordine di lavorazione.
    """
    by_sheet: Dict[int, List[LayoutRow]] = defaultdict(list)
    for r in rows:
        by_sheet[r.sheet].append(r)

    mixed, pure = [], []
    for s, lst in by_sheet.items():
        ids = {r.panel_id for r in lst}
        key_num = min(_safe_num(r.panel_number) for r in lst)
        if len(ids) >= 2:
            mixed.append((s, key_num))
        else:
            pid = next(iter(ids)) if ids else ""
            pure.append((s, pid, key_num))

    rev = (order == "desc")
    
    # Miste prima
    mixed.sort(key=lambda t: (t[1], t[0]), reverse=rev)
    run_mixed = [s for (s, _kn) in mixed]

    # Pure per panel_id, poi per key_num
    pure.sort(key=lambda t: (str(t[1]), t[2]), reverse=False)
    run_pure = []
    for pid, grp in groupby(pure, key=lambda t: t[1]):
        g = list(grp)
        g.sort(key=lambda t: t[2], reverse=rev)
        run_pure.extend([s for (s, _pid, _kn) in g])

    return run_mixed + run_pure


def build_run_order(rows: List[LayoutRow], order: str = "asc") -> List[int]:
    """
    Crea sequenza di lavorazione raggruppando per panel_id dominante (per area).
    Ordina per min(panel_number) nel foglio.
    """
    by_sheet: Dict[int, List[LayoutRow]] = defaultdict(list)
    for r in rows:
        by_sheet[r.sheet].append(r)

    signature = []
    for s, lst in by_sheet.items():
        area_by_id = defaultdict(float)
        nums_by_id = defaultdict(list)
        for r in lst:
            area_by_id[r.panel_id] += r.width * r.height
            nums_by_id[r.panel_id].append(_safe_num(r.panel_number))
        dom_id = max(area_by_id.items(), key=lambda kv: kv[1])[0]
        key_num = min(nums_by_id[dom_id]) if nums_by_id[dom_id] else float("inf")
        signature.append((s, dom_id, key_num))

    signature.sort(key=lambda t: (str(t[1]), t[2]))
    run_order = []
    for dom_id, grp in groupby(signature, key=lambda t: t[1]):
        g = list(grp)
        g.sort(key=lambda t: t[2], reverse=(order == "desc"))
        run_order.extend([s for (s, _did, _kn) in g])
    
    return run_order