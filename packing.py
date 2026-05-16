"""
packing.py

Algoritmi di nesting/packing dei pannelli sulle lastre.
"""

import math
from typing import List, Tuple
from collections import defaultdict
from rectpack import newPacker, PackingMode, MaxRectsBssf, MaxRectsBaf

from config import log
from geometry import LayoutRow


def _validate_panels_for_rectpack(panels, panel_ids, panel_numbers):
    """Valida che i pannelli abbiano dimensioni compatibili con rectpack."""
    bad = []
    for i, (w, h) in enumerate(panels):
        if not (isinstance(w, (int, float)) and isinstance(h, (int, float))):
            bad.append((i, panel_ids[i], panel_numbers[i], w, h, "non-numeric"))
        elif not (w > 0 and h > 0):
            bad.append((i, panel_ids[i], panel_numbers[i], w, h, "non-positive"))

    if bad:
        lines = ["❌ Pannelli con dimensioni non valide (causerebbero AssertionError in rectpack):"]
        for i, pid, pnum, w, h, why in bad[:50]:
            lines.append(f"  - idx {i:4d} | ID={pid} | N°={pnum} | {w}x{h}  [{why}]")
        if len(bad) > 50:
            lines.append(f"  … e altri {len(bad)-50} pannelli")
        lines.append("Suggerimento: apri il file '<input>__issues.xlsx'")
        raise ValueError("\n".join(lines))


def heuristic_pack(panels, panel_ids, panel_numbers, W, H, kerf, rotate):
    """
    Algoritmo euristico di packing usando rectpack.
    Prova diversi algoritmi e reinserisce pannelli non allocati.
    """
    log.info(f"🚀 Heuristic pack | rotate={rotate} | N={len(panels)}")

    _validate_panels_for_rectpack(panels, panel_ids, panel_numbers)

    if not (W > 0 and H > 0):
        raise ValueError(f"Dimensioni lastra non valide: W={W}, H={H}")
    if kerf < 0:
        raise ValueError(f"Kerf non valido: {kerf}")

    algos = [MaxRectsBssf, MaxRectsBaf]
    best_rows, best_n, best_used_ids = None, math.inf, None

    # STEP 1: Prova algoritmi
    for Algo in algos:
        packer = newPacker(mode=PackingMode.Offline, pack_algo=Algo, rotation=rotate)
        for i, (w, h) in enumerate(panels):
            packer.add_rect(w + kerf, h + kerf, rid=i)
        for _ in range(len(panels)):
            packer.add_bin(W, H)
        packer.pack()

        used_ids = set()
        rows = []
        for bin_id, x, y, w, h, rid in packer.rect_list():
            used_ids.add(rid)
            rows.append(LayoutRow(
                sheet=bin_id + 1,
                idx=rid,
                x=x, y=y,
                width=w - kerf,
                height=h - kerf,
                rotated=(panels[rid][0] != w - kerf),
                panel_id=panel_ids[rid],
                panel_number=panel_numbers[rid]
            ))

        n_sheets = max((r.sheet for r in rows), default=0)
        if n_sheets < best_n:
            best_n, best_rows, best_used_ids = n_sheets, rows, used_ids

    # STEP 2: Pannelli non inseriti
    missing = [i for i in range(len(panels)) if i not in best_used_ids]
    log.info(f"📦 Pannelli inizialmente posizionati: {len(best_used_ids)} / {len(panels)}")

    if not missing:
        log.info("✅ Nessun pannello escluso in modalità euristica.")
        return best_rows

    log.warning(f"❗ Pannelli NON allocati: {len(missing)}")
    for i in missing:
        log.warning(f"   - {panel_ids[i]} (#{panel_numbers[i]}) {panels[i][0]}x{panels[i][1]}")

    # STEP 3: Reinserimento
    existing_bins = defaultdict(list)
    for r in best_rows:
        existing_bins[r.sheet].append(r)

    current_max_sheet = max(existing_bins.keys())

    for i in missing:
        w, h = panels[i]
        placed = False

        # Prova a reinserire in layout esistenti
        for sheet_id in sorted(existing_bins):
            packer = newPacker(mode=PackingMode.Offline, pack_algo=MaxRectsBssf, rotation=rotate)
            packer.add_bin(W, H)

            for item in existing_bins[sheet_id]:
                packer.add_rect(item.width + kerf, item.height + kerf, rid=-1)

            packer.add_rect(w + kerf, h + kerf, rid=i)
            packer.pack()

            for bin_id, x, y, rw, rh, rid in packer.rect_list():
                if rid == i:
                    new_row = LayoutRow(
                        sheet=sheet_id, idx=i, x=x, y=y,
                        width=rw - kerf, height=rh - kerf,
                        rotated=(w != rw - kerf),
                        panel_id=panel_ids[i],
                        panel_number=panel_numbers[i]
                    )
                    best_rows.append(new_row)
                    existing_bins[sheet_id].append(new_row)
                    placed = True
                    break
            if placed:
                break

        # Nuova lastra se non inserito
        if not placed:
            current_max_sheet += 1
            new_row = LayoutRow(
                sheet=current_max_sheet, idx=i, x=0, y=0,
                width=w, height=h, rotated=False,
                panel_id=panel_ids[i], panel_number=panel_numbers[i]
            )
            best_rows.append(new_row)
            existing_bins[current_max_sheet] = [new_row]
            log.info(f"🆕 Pannello {panel_ids[i]} allocato in nuova lastra #{current_max_sheet}")

    log.info(f"✅ Pannelli finali allocati: {len(best_rows)} / {len(panels)}")
    return best_rows