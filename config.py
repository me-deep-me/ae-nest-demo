"""
config.py

Configurazioni globali, logging e filtri per il sistema di nesting.
"""

import logging
import warnings

# --- Disattiva warning matplotlib su thread secondario ---
warnings.filterwarnings(
    "ignore",
    message="Starting a Matplotlib GUI outside of the main thread will likely fail.",
    category=UserWarning,
)

try:
    import matplotlib
    matplotlib.use("Agg")  # backend non-GUI
except Exception:
    pass

# --- Riduzione verbosità ezdxf ---
for name in ("ezdxf", "ezdxf.entities", "ezdxf.lldxf", "ezdxf.addons"):
    logging.getLogger(name).setLevel(logging.ERROR)


# --- LOGGING CONFIG ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# --- FILTRO LOGGING SINTETICO ---
class ConciseFilter(logging.Filter):
    """
    Se enabled=True, lascia passare solo:
      - WARNING/ERROR/CRITICAL
      - poche INFO 'chiave' (parole-chiave in keep)
    """
    def __init__(self, enabled=True):
        super().__init__()
        self.enabled = enabled
        self.keep = (
            "▶️ Avvio", "📦 Packing", "✅", "⚠️", "XLSX:", "GLB export",
            "IFC export", "PNG exploded 3D", "Workbook unico"
        )

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.enabled:
            return True
        if record.levelno >= logging.WARNING:
            return True
        msg = record.getMessage()
        return any(k in msg for k in self.keep)


# Istanza globale filtro (attivabile/disattivabile)
CONCISE_FILTER = ConciseFilter(enabled=True)
logging.getLogger().addFilter(CONCISE_FILTER)


# --- COSTANTI ---
MM2M = 1.0 / 1000.0  # conversione millimetri -> metri

# Spessori default per materiale (mm)
DEFAULT_THICKNESS = {
    "hpl": 18.0,
    "corian": 18.0,
    "inox": 18.0,
    "corian_grecato": 18.0
}

# Preset lastre
SHEET_PRESETS = {
    "inox": (1250.0, 3000.0),
    "hpl": (1300.0, 3050.0),
    "corian": (930.0, 3000.0),
    "corian_grecato": (1200.0, 2945.0)
}


# --- UTILITY FUNCTIONS ---
def _default_thickness_for(material: str) -> float:
    """Ritorna lo spessore default per un materiale."""
    defaults = {
        "hpl": 18.0, 
        "corian": 18.0, 
        "inox": 18.0,
        "corian_grecato": 18.0
    }
    return defaults.get((material or "hpl").lower(), 18.0)