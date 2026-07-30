"""
src/styles.py
--------------
CSS (tema oscuro SaaS) e iconografía compartidos por demo.py.
Paleta principal: #1E1E2F fondo, #6C63FF primario, #2D2F48 tarjetas.
"""

FONT_AWESOME_CDN = (
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'
)

# Icono (Font Awesome class, color hex) por categoría (clave en minúscula).
# Compatible con el formato de datos_puno.categorias_atractivos
ICONOS_CATEGORIA = {
    "isla":                 ("fa-solid fa-water",             "#38bdf8"),
    "lago":                 ("fa-solid fa-water",             "#38bdf8"),
    "sitio arqueológico":   ("fa-solid fa-landmark",          "#f59e0b"),
    "religioso":            ("fa-solid fa-place-of-worship",  "#a78bfa"),
    "mirador":              ("fa-solid fa-binoculars",        "#34d399"),
    "museo":                ("fa-solid fa-building-columns",  "#60a5fa"),
    "evento":               ("fa-solid fa-calendar-check",    "#f59e0b"),
    "senderismo":           ("fa-solid fa-person-hiking",     "#34d399"),
    "naturaleza":           ("fa-solid fa-tree",              "#38bdf8"),
    "hotel":                ("fa-solid fa-bed",               "#fb7185"),
}
ICONO_DEFECTO = ("fa-solid fa-map-pin", "#c084fc")


def icono_y_color(categoria: str):
    """Devuelve (icon_class, color_hex) para una categoría."""
    return ICONOS_CATEGORIA.get(str(categoria).strip().lower(), ICONO_DEFECTO)


def inyectar_css() -> str:
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700;800&family=Poppins:wght@400;500;600;700;800&display=swap');

:root {
  --bg-primary: #1E1E2F;
  --bg-sidebar: #24263B;
  --bg-card: #2D2F48;
  --bg-card-secondary: #36395A;
  --primary: #6C63FF;
  --primary-hover: #7C74FF;
  --primary-accent: #8A7DFF;
  --text-primary: #FFFFFF;
  --text-secondary: #B7BDD6;
  --text-muted: #8C93B0;
  --border-color: #3A3D5C;
  --divider-color: #444866;
  --success: #3DDC97;
  --warning: #FFC857;
  --error: #FF5E78;
  --info: #4D96FF;
  --radius-sm: 10px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --shadow-card: 0 4px 24px rgba(0,0,0,0.25);
  --shadow-elevated: 0 8px 40px rgba(0,0,0,0.35);
  --shadow-primary: 0 10px 30px rgba(0,0,0,0.30);
  --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

html, body, #root, .stApp {
    font-family: 'Inter', 'Poppins', 'Segoe UI', system-ui, -apple-system, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-secondary);
}

.stApp {
    background: var(--bg-primary);
}

/* ==============================
   TOP NAVBAR
   ============================== */
.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #24263B 0%, #2D2F48 100%);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 10px 24px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-card);
    position: relative;
    overflow: hidden;
}
.navbar::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary), var(--primary-accent), var(--info));
}
.navbar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
}
.navbar-logo-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, var(--primary), var(--primary-accent));
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 2px 12px rgba(108,99,255,0.35);
}
.navbar-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin: 0;
}
.navbar-subtitle {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin: 0;
    font-weight: 400;
}
.navbar-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(61, 220, 151, 0.1);
    border: 1px solid rgba(61, 220, 151, 0.25);
    border-radius: 999px;
    font-size: 0.72rem;
    color: var(--success);
    font-weight: 500;
}
.navbar-status-dot {
    width: 7px; height: 7px;
    background: var(--success);
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.85); }
}

/* ==============================
   SIDEBAR — SaaS NAV (REDESIGNED)
   ============================== */
section[data-testid="stSidebar"] {
    background-color: #24263B !important;
    border-right: 1px solid #2A2D47;
    width: 270px !important;
    min-width: 270px !important;
    max-width: 270px !important;
    padding: 0 !important;
    box-shadow: 4px 0 30px rgba(0, 0, 0, 0.25);
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}
section[data-testid="stSidebar"] > div:first-child > div:first-child {
    padding: 0 !important;
}

/* ── Header ── */
.sb-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 24px 20px 20px;
    border-bottom: 1px solid rgba(58, 61, 92, 0.35);
}
.sb-header-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #6C63FF, #8A7DFF);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.04em;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(108, 99, 255, 0.3);
}
.sb-header-text {
    flex: 1;
    min-width: 0;
}
.sb-header-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0;
    line-height: 1.3;
    letter-spacing: -0.01em;
}
.sb-header-sub {
    font-size: 0.64rem;
    color: #8C93B0;
    margin: 1px 0 0;
    line-height: 1.3;
}

/* ── Section labels ── */
.sb-section-label {
    padding: 20px 20px 6px;
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #5A5F7A;
}

/* ── Nav items ── */
.sb-nav-item {
    display: flex;
    align-items: center;
    margin: 2px 0;
    padding: 0 10px;
    border-radius: 10px;
    transition: background 0.15s ease;
    position: relative;
}
.sb-nav-item:hover {
    background: rgba(108, 99, 255, 0.07);
}
.sb-nav-item.active {
    background: rgba(108, 99, 255, 0.12);
}
.sb-nav-item.active:hover {
    background: rgba(108, 99, 255, 0.15);
}

.sb-nav-bar {
    width: 4px;
    height: 24px;
    background: transparent;
    border-radius: 0 4px 4px 0;
    margin-right: 10px;
    flex-shrink: 0;
    transition: background 0.2s ease;
}
.sb-nav-item.active .sb-nav-bar {
    background: #6C63FF;
    box-shadow: 0 0 8px rgba(108, 99, 255, 0.35);
}

.sb-nav-link {
    flex: 1;
    display: block;
    color: #B7BDD6;
    text-decoration: none;
    font-size: 0.82rem;
    font-weight: 450;
    font-family: inherit;
    padding: 8px 4px;
    border-radius: 8px;
    transition: color 0.15s ease;
    line-height: 1.3;
}
.sb-nav-link:hover {
    color: #FFFFFF;
    text-decoration: none;
}
.sb-nav-item.active .sb-nav-link {
    color: #FFFFFF;
}

/* ── Divider ── */
.sb-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(58, 61, 92, 0.5), transparent);
    margin: 10px 20px;
}

/* ── Controls area per page ── */
.sb-controls {
    padding: 8px 20px 16px;
}
.sb-controls .stSelectbox, 
.sb-controls .stButton,
.sb-controls .stInfo {
    margin-bottom: 8px;
}
.sb-controls .stButton > button {
    background: linear-gradient(90deg, #6C63FF 0%, #8A7DFF 100%);
    color: white;
    border: none;
    border-radius: 16px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 20px;
    transition: all 0.2s ease;
    box-shadow: 0 10px 30px rgba(0,0,0,0.30);
    width: 100%;
}
.sb-controls .stButton > button:hover {
    background: linear-gradient(90deg, #7C74FF 0%, #9A8DFF 100%);
    transform: translateY(-2px);
    box-shadow: 0 14px 36px rgba(0,0,0,0.35);
}
.sb-controls .stSelectbox label,
.sb-controls .stNumberInput label {
    font-size: 0.7rem;
    font-weight: 600;
    color: #8C93B0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 2px;
}
.sb-controls div[data-baseweb="select"] > div {
    background-color: #2D2F48 !important;
    border-color: #3A3D5C !important;
    border-radius: 8px !important;
}
.sb-controls div[data-baseweb="select"]:hover > div {
    border-color: #6C63FF !important;
}
.sb-controls .stInfo {
    background: rgba(108,99,255,0.06) !important;
    border: 1px solid rgba(108,99,255,0.12) !important;
    border-radius: 8px !important;
    font-size: 0.74rem !important;
    color: #B7BDD6 !important;
}
.sb-controls .stAlert {
    border-radius: 8px !important;
    font-size: 0.76rem !important;
}
.sb-controls div[data-testid="stExpander"] {
    background: #2D2F48;
    border: 1px solid #3A3D5C;
    border-radius: 8px;
    overflow: hidden;
}
.sb-controls div[data-testid="stExpander"] summary {
    font-weight: 500;
    color: #B7BDD6;
    font-size: 0.82rem;
    padding: 2px 0;
}
.sb-controls div[data-testid="stForm"] {
    background: #36395A;
    border: 1px solid #3A3D5C;
    border-radius: 8px;
    padding: 12px;
}

/* ── User panel bottom ── */
.sb-user-panel {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid rgba(58, 61, 92, 0.35);
    background: rgba(30, 30, 47, 0.25);
}
.sb-user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6C63FF, #8A7DFF);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    position: relative;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(108, 99, 255, 0.25);
}
.sb-user-status {
    width: 10px;
    height: 10px;
    background: #3DDC97;
    border: 2px solid #24263B;
    border-radius: 50%;
    position: absolute;
    bottom: -1px;
    right: -1px;
}
.sb-user-info {
    flex: 1;
    min-width: 0;
}
.sb-user-name {
    font-size: 0.78rem;
    font-weight: 600;
    color: #FFFFFF;
    margin: 0;
    line-height: 1.3;
}
.sb-user-role {
    font-size: 0.62rem;
    color: #8C93B0;
    margin: 1px 0 0;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ==============================
   HEADER / SECTION LABELS
   ============================== */
.section-label {
    font-size: 0.70rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin: 20px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::before {
    content: '';
    width: 3px;
    height: 14px;
    background: var(--primary);
    border-radius: 2px;
}

/* ==============================
   PLACE CARDS
   ============================== */
.place-card {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: linear-gradient(180deg, #2D2F48 0%, #25273D 100%);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: var(--shadow-card);
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    transition: transform var(--transition), box-shadow var(--transition);
}
.place-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-elevated);
    border-color: rgba(108,99,255,0.3);
}
.place-card::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--accent, var(--primary));
    border-radius: 3px 0 0 3px;
}
.place-card::after {
    content: '';
    position: absolute;
    top: -50%; right: -50%;
    width: 100%; height: 100%;
    background: radial-gradient(circle at 100% 0%, rgba(108,99,255,0.04), transparent 60%);
    pointer-events: none;
}

.place-icon {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    background: color-mix(in srgb, var(--accent, var(--primary)) 14%, transparent);
    font-size: 1.1rem;
    flex-shrink: 0;
    margin-top: 2px;
    border: 1px solid color-mix(in srgb, var(--accent, var(--primary)) 20%, transparent);
}

.place-info     { flex: 1; min-width: 0; }
.place-title    { font-size: 0.92rem; font-weight: 700; color: var(--text-primary); margin: 0 0 4px 0; letter-spacing: -0.01em; }
.place-meta     { font-size: 0.72rem; color: var(--text-muted); margin: 0 0 8px 0;
                  display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.place-stars    { color: var(--warning); font-size: 0.82rem; letter-spacing: 1.5px; }
.place-score    { display: block; font-size: 0.67rem; color: var(--text-muted); margin-top: 4px; }
.place-desc     { font-size: 0.72rem; color: var(--text-secondary); margin-top: 8px; line-height: 1.5; }

.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.badge-maritimo {
    background: rgba(77, 150, 255, 0.12);
    color: var(--info);
    border: 1px solid rgba(77, 150, 255, 0.25);
}
.badge-terrestre {
    background: rgba(61, 220, 151, 0.1);
    color: var(--success);
    border: 1px solid rgba(61, 220, 151, 0.2);
}

/* Visit button inside card */
.place-card .stButton > button {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 500;
    padding: 3px 12px;
    min-height: 0;
    height: auto;
    line-height: 1.8;
    transition: var(--transition);
}
.place-card .stButton > button:hover {
    background: var(--bg-card-secondary);
    border-color: var(--primary);
    color: var(--text-primary);
}

/* ==============================
   FORM ELEMENTS
   ============================== */
div[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
}
div[data-baseweb="select"]:hover > div {
    border-color: var(--primary) !important;
}
div[data-baseweb="select"] span { color: var(--text-primary) !important; }
ul[data-baseweb="menu"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
}
ul[data-baseweb="menu"] li { color: var(--text-secondary) !important; }
ul[data-baseweb="menu"] li:hover {
    background-color: var(--primary) !important;
    color: white !important;
}
ul[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: var(--bg-card-secondary) !important;
    color: var(--primary) !important;
}
div[data-baseweb="tag"] {
    background-color: var(--primary) !important;
    color: white !important;
    border-radius: 6px !important;
}
input, textarea, div[data-baseweb="input"] > div {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
}
input:focus, textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,0.15) !important;
}

/* ==============================
   EXPANDER / FORM CONTAINERS
   ============================== */
div[data-testid="stExpander"] {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-card);
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    font-weight: 600;
    color: var(--text-primary);
}
div[data-testid="stForm"] {
    background: var(--bg-card-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 16px;
}

/* ==============================
   BUTTONS (general)
   ============================== */
.stButton > button {
    background: var(--bg-card-secondary);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    font-weight: 500;
    font-size: 0.82rem;
    padding: 6px 14px;
    transition: var(--transition);
}
.stButton > button:hover {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(108,99,255,0.25);
}

/* primary buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #6C63FF 0%, #8A7DFF 100%);
    color: white;
    border: none;
    border-radius: 16px;
    font-weight: 600;
    padding: 8px 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.30);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #7C74FF 0%, #9A8DFF 100%);
    transform: translateY(-2px);
    box-shadow: 0 14px 36px rgba(0,0,0,0.35);
}

/* ==============================
   ALERTS / MESSAGES
   ============================== */
.stAlert {
    border-radius: var(--radius-sm) !important;
    font-size: 0.82rem !important;
    border: 1px solid transparent !important;
}
div[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
}
.st-bw { background-color: rgba(61, 220, 151, 0.08) !important; }
.st-bq { background-color: rgba(255, 200, 87, 0.08) !important; }
.st-br { background-color: rgba(255, 94, 120, 0.08) !important; }
.st-bi { background-color: rgba(77, 150, 255, 0.08) !important; }

/* ==============================
   DIVIDER
   ============================== */
hr {
    border-color: var(--divider-color) !important;
    margin: 24px 0 !important;
    opacity: 0.5;
}

/* ==============================
   MAP CONTAINER (st_folium iframe)
   ============================== */
iframe[srcdoc*="folium"], iframe[src*="folium"] {
    border-radius: calc(var(--radius-md) - 4px);
}
[class*="element-container"]:has(iframe[srcdoc*="folium"]),
[class*="element-container"]:has(iframe[src*="folium"]) {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 8px;
    box-shadow: var(--shadow-card);
    overflow: hidden;
    margin-bottom: 8px;
}

/* ==============================
   FOOTER
   ============================== */
.footer {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    font-size: 0.7rem;
    color: var(--text-muted);
    border-top: 1px solid var(--divider-color);
    margin-top: 24px;
}

/* ==============================
   SCROLLBAR
   ============================== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ==============================
   KEYFRAMES
   ============================== */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.place-card {
    animation: fadeIn 0.35s ease-out forwards;
}
.place-card:nth-child(2) { animation-delay: 0.05s; }
.place-card:nth-child(3) { animation-delay: 0.10s; }
.place-card:nth-child(4) { animation-delay: 0.15s; }
.place-card:nth-child(5) { animation-delay: 0.20s; }
.place-card:nth-child(6) { animation-delay: 0.25s; }
.place-card:nth-child(7) { animation-delay: 0.30s; }
.place-card:nth-child(8) { animation-delay: 0.35s; }
.place-card:nth-child(9) { animation-delay: 0.40s; }
.place-card:nth-child(10) { animation-delay: 0.45s; }

/* ==============================
   INFO BOX SIDEBAR
   ============================== */
.stInfo {
    background: rgba(77, 150, 255, 0.06) !important;
    border: 1px solid rgba(77, 150, 255, 0.15) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
}
.stSuccess {
    background: rgba(61, 220, 151, 0.06) !important;
    border: 1px solid rgba(61, 220, 151, 0.15) !important;
    border-radius: var(--radius-sm) !important;
}

/* Ruta planner success */
.st-cb {
    background: rgba(61, 220, 151, 0.06) !important;
    border: 1px solid rgba(61, 220, 151, 0.15) !important;
}

/* Spinner */
.stSpinner {
    color: var(--primary) !important;
}

/* Sidebar divider */
.sidebar-divider {
    border-color: var(--divider-color);
    margin: 16px 0;
    opacity: 0.4;
}

/* Column gap fix */
.row-widget.stHorizontal {
    gap: 20px;
}

/* Metric cards usage */
div[data-testid="stMetricValue"] {
    color: var(--text-primary);
    font-weight: 700;
}
div[data-testid="stMetricLabel"] {
    color: var(--text-muted);
    font-size: 0.72rem;
}
</style>"""


def generar_estrellas(score_0_a_1_o_5: float) -> str:
    """Acepta un score en [0,1] (motores de recomendación) o en [0,5] (rating) y
    devuelve 5 símbolos de estrella llena/vacía."""
    valor = score_0_a_1_o_5
    if valor <= 1.0:
        valor = valor * 5
    n = max(0, min(5, round(valor)))
    return "★" * n + "☆" * (5 - n)


def tarjeta_lugar_html(
    nombre: str,
    categoria: str,
    zona: str,
    score: float,
    rating: float,
    es_maritimo: bool = False,
    tipo_acceso: str = "",
    descripcion: str = "",
) -> str:
    icono_cls, color = icono_y_color(categoria)
    estrellas = generar_estrellas(score)

    acceso = tipo_acceso or ("marítimo" if es_maritimo else "terrestre")
    if "marít" in acceso.lower() or "marit" in acceso.lower():
        badge = (
            '<span class="badge badge-maritimo">'
            '<i class="fa-solid fa-ship"></i> Acceso marítimo'
            '</span>'
        )
    else:
        badge = (
            '<span class="badge badge-terrestre">'
            '<i class="fa-solid fa-bus"></i> Acceso terrestre'
            '</span>'
        )

    desc_html = f'<div class="place-desc">{descripcion}</div>' if descripcion else ""

    return f"""
    <div class="place-card" style="--accent: {color};">
        <div class="place-icon"><i class="{icono_cls}"></i></div>
        <div class="place-info">
            <p class="place-title">{nombre}</p>
            <div class="place-meta">
                <span>{categoria}</span>
                <span style="color:var(--divider-color);">&middot;</span>
                <span>{zona}</span>
                <span style="color:var(--divider-color);">&middot;</span>
                {badge}
            </div>
            <span class="place-stars">{estrellas}</span>
            <span class="place-score">Score&nbsp;{score:.3f}&ensp;&middot;&ensp;Rating&nbsp;{rating:.1f}&thinsp;/&thinsp;5</span>
            {desc_html}
        </div>
    </div>
    """
