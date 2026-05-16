"""
Æ-Nest — 2D Panel Nesting Optimizer
by Mattia Erigoni · mattiaerigoni.com
"""

import io
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe
import pandas as pd
import numpy as np

from packing import heuristic_pack
from geometry import LayoutRow
from ordering import build_run_order_cnc2

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Æ-Nest · Nesting Optimizer",
    page_icon="⬛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
  --bg:      #07101c;
  --bg2:     #0b1724;
  --bg3:     #0f1e2e;
  --ink:     #dde6f2;
  --ink2:    rgba(221,230,242,0.55);
  --ink3:    rgba(221,230,242,0.30);
  --sky:     #6aaee8;
  --sky2:    #3d85c8;
  --skydim:  rgba(106,174,232,0.10);
  --border:  rgba(106,174,232,0.10);
  --border2: rgba(106,174,232,0.22);
  --ok:      #3ecf8e;
  --warn:    #f5a623;
  --err:     #ff6b6b;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background-color: var(--bg) !important;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
  color: var(--ink) !important;
}
[data-testid="stSidebar"] {
  background-color: var(--bg2) !important;
  border-right: 1px solid var(--border2) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }

/* ── Header ── */
.ae-header {
  display: flex; align-items: center; gap: 14px;
  padding: 0 0 1.6rem 0; margin-bottom: 0.4rem;
}
.ae-dot {
  width: 12px; height: 12px; border-radius: 50%;
  background: linear-gradient(135deg, var(--sky), var(--sky2));
  box-shadow: 0 0 18px rgba(106,174,232,0.6);
  flex-shrink: 0;
}
.ae-title {
  font-size: 2.1rem; font-weight: 700; letter-spacing: -0.03em;
  color: var(--ink); line-height: 1;
}
.ae-title span { color: var(--sky); font-style: italic; }
.ae-sub {
  font-size: 0.82rem; color: var(--ink3); letter-spacing: 0.04em;
  margin-top: 0.25rem; font-weight: 400;
}
.ae-badge {
  font-size: 0.62rem; letter-spacing: 0.12em; text-transform: uppercase;
  padding: 0.22rem 0.7rem; border: 1px solid var(--border2);
  border-radius: 999px; color: var(--sky); font-weight: 600;
  white-space: nowrap; align-self: flex-start; margin-top: 0.35rem;
}

/* ── Divider ── */
.ae-divider {
  width: 100%; height: 1px;
  background: var(--border); margin: 1.4rem 0 1.8rem 0;
}

/* ── Section labels ── */
.ae-label {
  font-size: 0.68rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--sky); font-weight: 600; margin-bottom: 0.7rem;
}

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 12px; margin: 1.2rem 0 1.8rem 0; flex-wrap: wrap; }
.kpi-card {
  flex: 1; min-width: 130px;
  background: var(--bg3);
  border: 1px solid var(--border2);
  border-radius: 14px;
  padding: 1rem 1.2rem;
}
.kpi-val {
  font-size: 2rem; font-weight: 700; color: var(--sky);
  line-height: 1; letter-spacing: -0.03em;
  font-family: 'DM Mono', monospace;
}
.kpi-label {
  font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--ink3); margin-top: 0.3rem; font-weight: 500;
}
.kpi-card.ok   .kpi-val { color: var(--ok); }
.kpi-card.warn .kpi-val { color: var(--warn); }

/* ── Sheet card ── */
.sheet-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.6rem 0; margin-top: 1.2rem;
}
.sheet-title {
  font-size: 0.9rem; font-weight: 600; color: var(--ink);
  letter-spacing: 0.02em;
}
.sheet-eff {
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  padding: 0.22rem 0.7rem; border: 1px solid var(--border2);
  border-radius: 999px; color: var(--sky); font-weight: 500;
  font-family: 'DM Mono', monospace;
}

/* ── Sidebar elements ── */
.sb-section {
  font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--sky); font-weight: 600;
  margin: 1.2rem 0 0.6rem 0;
}
.sb-info {
  background: var(--skydim); border: 1px solid var(--border2);
  border-radius: 10px; padding: 0.6rem 0.9rem;
  font-size: 0.8rem; color: var(--ink2); margin-bottom: 0.6rem;
}
.sb-info strong { color: var(--sky); font-family: 'DM Mono', monospace; }

/* ── Table ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border2) !important;
  border-radius: 12px !important; overflow: hidden;
}

/* ── Buttons ── */
.stButton > button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important; letter-spacing: 0.05em !important;
  border-radius: 999px !important; transition: all 0.2s !important;
}
.stButton > button[kind="primary"] {
  background: var(--sky) !important;
  color: var(--bg) !important; border: none !important;
}
.stButton > button[kind="primary"]:hover {
  background: #8ac4ef !important; transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  border: 1px solid var(--border2) !important;
  color: var(--ink2) !important;
}

/* ── Inputs ── */
.stNumberInput input, .stTextInput input, .stSelectbox select {
  background: var(--bg3) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 10px !important;
  color: var(--ink) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ae-header">
  <div class="ae-dot"></div>
  <div>
    <div class="ae-title">Æ<span>-Nest</span></div>
    <div class="ae-sub">2D Cut-Stock Optimizer · NP-Hard · MaxRects Heuristic</div>
  </div>
  <div class="ae-badge">Panel Nesting</div>
</div>
<div class="ae-divider"></div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-section">Sheet Configuration</div>', unsafe_allow_html=True)

    PRESETS = {
        "HPL — 1300 × 3050 mm":             (1300, 3050),
        "Corian — 930 × 3000 mm":            (930,  3000),
        "Inox — 1250 × 3000 mm":             (1250, 3000),
        "Corian Grecato — 1200 × 2945 mm":   (1200, 2945),
        "Custom":                             None,
    }

    preset = st.selectbox("Material / Sheet preset", list(PRESETS.keys()), label_visibility="collapsed")

    if PRESETS[preset] is not None:
        sheet_w, sheet_h = PRESETS[preset]
        st.markdown(f'<div class="sb-info">Sheet: <strong>{sheet_w} × {sheet_h} mm</strong></div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2)
        sheet_w = col1.number_input("W (mm)", min_value=100, max_value=5000, value=1300, step=10, label_visibility="visible")
        sheet_h = col2.number_input("H (mm)", min_value=100, max_value=6000, value=3050, step=10, label_visibility="visible")

    st.markdown('<div class="sb-section">Cutting Parameters</div>', unsafe_allow_html=True)
    kerf = st.slider("Kerf / blade (mm)", min_value=0.0, max_value=15.0, value=4.0, step=0.5)
    allow_rotation = st.toggle("Allow 90° rotation", value=True)

    st.markdown('<div class="sb-section">CNC Order</div>', unsafe_allow_html=True)
    id_order = st.radio("Panel number order", ["asc", "desc"],
                        format_func=lambda x: "Ascending ↑" if x == "asc" else "Descending ↓",
                        horizontal=True)

    st.markdown('<div class="ae-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.75rem; color:rgba(221,230,242,0.35); line-height:1.7;">
    Algorithm: MaxRects BSSF + BAF<br>
    Rotation: optional 90°<br>
    Kerf: blade width subtracted from each panel<br><br>
    Built for healthcare infrastructure — HPL, Corian, Inox panels for modular wall systems in operating rooms.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.72rem; color:rgba(106,174,232,0.5); margin-top:1rem;">
    by <a href="https://mattiaerigoni.com" style="color:#6aaee8;">Mattia Erigoni</a>
    </div>
    """, unsafe_allow_html=True)

# ── Panel input ───────────────────────────────────────────────────────────────
st.markdown('<div class="ae-label">Panel List</div>', unsafe_allow_html=True)
st.caption("Dimensions in **mm** · ID = panel code · N° = number · Qty = quantity")

DEFAULT_PANELS = pd.DataFrame([
    {"ID": "A", "N°": "1", "Width (mm)": 600,  "Height (mm)": 2400, "Qty": 4},
    {"ID": "A", "N°": "2", "Width (mm)": 450,  "Height (mm)": 2400, "Qty": 6},
    {"ID": "B", "N°": "1", "Width (mm)": 1200, "Height (mm)": 800,  "Qty": 3},
    {"ID": "B", "N°": "2", "Width (mm)": 900,  "Height (mm)": 600,  "Qty": 5},
    {"ID": "C", "N°": "1", "Width (mm)": 300,  "Height (mm)": 2400, "Qty": 8},
])

edited = st.data_editor(
    DEFAULT_PANELS,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "ID":          st.column_config.TextColumn("ID",          width="small"),
        "N°":          st.column_config.TextColumn("N°",          width="small"),
        "Width (mm)":  st.column_config.NumberColumn("W (mm)",  min_value=1, max_value=5000, step=1),
        "Height (mm)": st.column_config.NumberColumn("H (mm)", min_value=1, max_value=6000, step=1),
        "Qty":         st.column_config.NumberColumn("Qty",       min_value=1, max_value=500, step=1),
    },
    hide_index=True,
)

st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
run = st.button("▶  Run Nesting Optimizer", type="primary", use_container_width=True)

# ── Engine ────────────────────────────────────────────────────────────────────
# ── Run optimizer ─────────────────────────────────────────────────────────────
if run:
    if edited.empty:
        st.warning("Add at least one panel row."); st.stop()

    panels, panel_ids, panel_numbers = [], [], []
    for _, row in edited.iterrows():
        qty = int(row["Qty"])
        for q in range(qty):
            panels.append((float(row["Width (mm)"]), float(row["Height (mm)"])))
            panel_ids.append(str(row["ID"]))
            panel_numbers.append(f"{row['N°']}.{q+1}" if qty > 1 else str(row["N°"]))

    if not panels:
        st.error("No valid panels found."); st.stop()

    with st.spinner("Running MaxRects heuristic..."):
        try:
            results = []
            for rot in ([True, False] if allow_rotation else [False]):
                r = heuristic_pack(panels, panel_ids, panel_numbers,
                                   int(sheet_w), int(sheet_h), kerf, rot)
                results.append((len({x.sheet for x in r}), r))
            rows_result = min(results, key=lambda x: x[0])[1]
            run_order = build_run_order_cnc2(rows_result, order=id_order)
        except Exception as e:
            st.error(f"Optimizer error: {e}"); st.stop()

    # Persist results in session_state so view switches / nav don't lose them
    st.session_state["rows_result"] = rows_result
    st.session_state["run_order"]   = run_order
    st.session_state["panels"]      = panels
    st.session_state["sheet_w"]     = int(sheet_w)
    st.session_state["sheet_h"]     = int(sheet_h)
    st.session_state["kerf"]        = kerf
    st.session_state["allow_rot"]   = allow_rotation
    st.session_state["sheet_idx"]   = 0   # reset navigator on new run

# ── Show results (persistent across reruns) ───────────────────────────────────
if "rows_result" not in st.session_state:
    st.stop()

rows_result    = st.session_state["rows_result"]
run_order      = st.session_state["run_order"]
panels         = st.session_state["panels"]
sheet_w        = st.session_state["sheet_w"]
sheet_h        = st.session_state["sheet_h"]
kerf           = st.session_state["kerf"]
allow_rotation = st.session_state["allow_rot"]

n_sheets   = len({r.sheet for r in rows_result})
n_placed   = len(rows_result)
panel_area = sum(w * h for (w, h) in panels)
sheet_area = n_sheets * sheet_w * sheet_h
efficiency = panel_area / sheet_area * 100
waste      = 100 - efficiency

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="ae-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="ae-label">Optimization Results</div>', unsafe_allow_html=True)

eff_cls = "ok" if efficiency >= 75 else "warn"
st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-val">{n_sheets}</div>
    <div class="kpi-label">Sheets used</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val">{n_placed}</div>
    <div class="kpi-label">Panels placed</div>
  </div>
  <div class="kpi-card {eff_cls}">
    <div class="kpi-val">{efficiency:.1f}%</div>
    <div class="kpi-label">Material efficiency</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val">{waste:.1f}%</div>
    <div class="kpi-label">Waste</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val">{sheet_w}×{sheet_h}</div>
    <div class="kpi-label">Sheet (mm)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Color map ─────────────────────────────────────────────────────────────────
unique_ids = sorted({r.panel_id for r in rows_result})
PALETTE = [
    "#6aaee8","#3ecf8e","#f5a623","#9b8cff","#ff6b6b",
    "#36d6e7","#f7c948","#c084fc","#fb923c","#a3e635",
]
id_color = {pid: PALETTE[i % len(PALETTE)] for i, pid in enumerate(unique_ids)}

# ── Helper: draw one sheet figure ─────────────────────────────────────────────
def draw_sheet(s, sheet_rows, dpi=130, thumb=False):
    SCALE = 0.003 if thumb else 0.0042
    fig_w = max(4 if thumb else 8, sheet_w * SCALE)
    fig_h = max(2 if thumb else 3, sheet_h * SCALE)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor("#0b1724")
    ax.set_facecolor("#07101c")

    if not thumb:
        for gx in range(0, int(sheet_w) + 1, 100):
            ax.axvline(gx, color="#1a2d44", lw=0.3, zorder=0)
        for gy in range(0, int(sheet_h) + 1, 100):
            ax.axhline(gy, color="#1a2d44", lw=0.3, zorder=0)

    ax.add_patch(patches.FancyBboxPatch(
        (0, 0), sheet_w, sheet_h, boxstyle="square,pad=0",
        linewidth=1.5 if not thumb else 1.0,
        edgecolor="#6aaee8", facecolor="none", zorder=2
    ))
    ax.add_patch(patches.Rectangle(
        (0, 0), sheet_w, sheet_h,
        linewidth=0, facecolor="#0d1a28",
        hatch="///" if not thumb else "", edgecolor="#0f2035", zorder=1
    ))

    for r in sheet_rows:
        hex_col = id_color.get(r.panel_id, "#6aaee8")
        hx = hex_col.lstrip("#")
        rgb = tuple(int(hx[i:i+2], 16) / 255 for i in (0, 2, 4))
        ax.add_patch(patches.Rectangle(
            (r.x, r.y), r.width, r.height,
            linewidth=0.5 if thumb else 0.8,
            edgecolor="white", facecolor=(*rgb, 0.78), zorder=3
        ))
        if not thumb and r.width > 120 and r.height > 60:
            label_main = f"{r.panel_id}·{r.panel_number}" + (" ↻" if r.rotated else "")
            label_dims = f"{int(r.width)} × {int(r.height)}"
            fs_main = max(4.5, min(9,  min(r.width, r.height) / 200))
            fs_dims = max(3.5, min(7,  min(r.width, r.height) / 280))
            cx, cy = r.x + r.width / 2, r.y + r.height / 2
            ax.text(cx, cy + r.height * 0.08, label_main,
                    ha="center", va="center", fontsize=fs_main,
                    color="white", fontweight="bold", fontfamily="monospace", zorder=4,
                    path_effects=[pe.withStroke(linewidth=1.5, foreground="#07101c")])
            ax.text(cx, cy - r.height * 0.18, label_dims,
                    ha="center", va="center", fontsize=fs_dims,
                    color="#aac0d8", fontfamily="monospace", zorder=4,
                    path_effects=[pe.withStroke(linewidth=1.2, foreground="#07101c")])
        elif thumb and r.width > 80 and r.height > 50:
            ax.text(r.x + r.width / 2, r.y + r.height / 2,
                    f"{r.panel_id}", ha="center", va="center",
                    fontsize=max(3, min(6, min(r.width, r.height) / 300)),
                    color="white", fontweight="bold", fontfamily="monospace", zorder=4)

    ax.set_xlim(-20, sheet_w + 20)
    ax.set_ylim(-20, sheet_h + 20)
    ax.set_aspect("equal")
    if not thumb:
        ax.tick_params(colors="#3d5a7a", labelsize=6.5, length=3)
        ax.set_xlabel("Width (mm)", color="#3d5a7a", fontsize=7, labelpad=4)
        ax.set_ylabel("Height (mm)", color="#3d5a7a", fontsize=7, labelpad=4)
    else:
        ax.axis("off")
    for spine in ax.spines.values():
        spine.set_edgecolor("#1a2d44")
    fig.tight_layout(pad=0.3 if thumb else 0.5)
    return fig

# ── View mode switcher ─────────────────────────────────────────────────────────
st.markdown('<div class="ae-divider"></div>', unsafe_allow_html=True)

hdr_col, btn_col = st.columns([3, 1])
with hdr_col:
    st.markdown('<div class="ae-label">Sheet Layouts — CNC Run Order</div>', unsafe_allow_html=True)
with btn_col:
    view_mode = st.radio(
        "view", ["⊞ Overview", "⬜ Single"],
        horizontal=True, label_visibility="collapsed",
        key="view_mode"
    )

# ── OVERVIEW MODE ──────────────────────────────────────────────────────────────
if view_mode == "⊞ Overview":
    COLS = 3
    for row_start in range(0, n_sheets, COLS):
        cols = st.columns(COLS)
        for col_idx, sheet_idx in enumerate(range(row_start, min(row_start + COLS, n_sheets))):
            s = run_order[sheet_idx]
            sheet_rows = [r for r in rows_result if r.sheet == s]
            used_area  = sum(r.width * r.height for r in sheet_rows)
            sheet_eff  = used_area / (sheet_w * sheet_h) * 100
            run_pos    = sheet_idx + 1

            with cols[col_idx]:
                st.markdown(f"""
                <div style="text-align:center;margin-bottom:0.3rem;">
                  <span style="font-size:0.7rem;font-weight:700;color:#6aaee8;
                    letter-spacing:0.1em;text-transform:uppercase;">
                    RUN {run_pos:03d}
                  </span>
                  <span style="font-size:0.65rem;color:rgba(221,230,242,0.35);
                    margin-left:6px;">
                    {sheet_eff:.0f}% eff · {len(sheet_rows)} panels
                  </span>
                </div>
                """, unsafe_allow_html=True)
                fig = draw_sheet(s, sheet_rows, dpi=90, thumb=True)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

# ── SINGLE MODE ────────────────────────────────────────────────────────────────
else:
    idx = st.session_state.get("sheet_idx", 0)
    idx = max(0, min(idx, n_sheets - 1))

    s          = run_order[idx]
    sheet_rows = [r for r in rows_result if r.sheet == s]
    used_area  = sum(r.width * r.height for r in sheet_rows)
    sheet_eff  = used_area / (sheet_w * sheet_h) * 100
    run_pos    = idx + 1
    ids_on     = sorted({r.panel_id for r in sheet_rows})

    # Navigation bar
    nav_l, nav_info, nav_r, nav_dl = st.columns([1, 4, 1, 1])
    with nav_l:
        if st.button("← Prev", disabled=(idx == 0), use_container_width=True):
            st.session_state.sheet_idx = idx - 1
            st.rerun()
    with nav_info:
        st.markdown(f"""
        <div class="sheet-header" style="margin-top:0;">
          <div class="sheet-title">
            RUN {run_pos:03d} &nbsp;·&nbsp; Sheet {s}
            &nbsp;<span style="color:rgba(221,230,242,0.35);font-size:0.78rem;font-weight:400;">
              {len(sheet_rows)} panels &nbsp;·&nbsp; IDs: {', '.join(ids_on)}
            </span>
          </div>
          <div class="sheet-eff">{sheet_eff:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with nav_r:
        if st.button("Next →", disabled=(idx == n_sheets - 1), use_container_width=True):
            st.session_state.sheet_idx = idx + 1
            st.rerun()

    # Figure
    fig = draw_sheet(s, sheet_rows, dpi=130, thumb=False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    with nav_dl:
        st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
        st.download_button(
            "⬇ PNG", data=buf,
            file_name=f"aenest_run{run_pos:03d}_sheet{s:03d}.png",
            mime="image/png", key="dl_single",
            use_container_width=True,
        )

    # Sheet mini-navigator dots
    dots = ""
    for i in range(n_sheets):
        active = "background:#6aaee8;width:20px;" if i == idx else "background:rgba(106,174,232,0.25);width:8px;"
        dots += f'<div style="height:6px;border-radius:999px;{active}transition:all 0.2s;"></div>'
    st.markdown(
        f'<div style="display:flex;gap:4px;align-items:center;justify-content:center;margin-top:0.8rem;">{dots}</div>',
        unsafe_allow_html=True
    )

# ── Legend ─────────────────────────────────────────────────────────────────────
legend_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1.2rem 0 0.5rem 0;">'
for pid, col in id_color.items():
    legend_html += (
        f'<div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:rgba(221,230,242,0.65);">'
        f'<div style="width:12px;height:12px;border-radius:3px;background:{col};flex-shrink:0;"></div>'
        f'<strong style="color:{col};">{pid}</strong></div>'
    )
legend_html += '</div>'
st.markdown(legend_html, unsafe_allow_html=True)

# ── Detail table ───────────────────────────────────────────────────────────────
st.markdown('<div class="ae-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="ae-label">Placement Detail</div>', unsafe_allow_html=True)

detail = [{
    "Run":     f"{run_order.index(r.sheet)+1:03d}" if r.sheet in run_order else "—",
    "Sheet":   r.sheet,
    "Panel":   r.panel_id,
    "N°":      r.panel_number,
    "W (mm)":  int(r.width),
    "H (mm)":  int(r.height),
    "X":       int(r.x),
    "Y":       int(r.y),
    "Rotated": "↻ Yes" if r.rotated else "—",
} for r in sorted(rows_result, key=lambda r: (r.sheet, r.panel_id, r.panel_number))]

st.dataframe(
    pd.DataFrame(detail),
    use_container_width=True,
    hide_index=True,
    height=min(400, 40 + len(detail) * 35),
)

# ── Summary footer ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:1.5rem;padding:1rem 1.2rem;background:var(--bg3);
     border:1px solid var(--border2);border-radius:12px;
     font-size:0.78rem;color:var(--ink3);line-height:1.8;">
  <strong style="color:var(--sky);">Æ-Nest</strong> · MaxRects BSSF + BAF via rectpack ·
  {len(panels)} panels → {n_sheets} sheets ·
  Efficiency {efficiency:.1f}% · Kerf {kerf} mm ·
  Rotation {"enabled" if allow_rotation else "disabled"} ·
  Sheet {sheet_w}×{sheet_h} mm
</div>
""", unsafe_allow_html=True)
