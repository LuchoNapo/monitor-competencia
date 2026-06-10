import streamlit as st
import os
from datetime import datetime
from pathlib import Path
from PIL import Image

from scrapers.web_scraper import scrape_website
from scrapers.meta_ads import get_meta_ads
from analyzer import generate_report
from storage import (
    save_scan, save_report, get_last_report,
    list_reports, load_report, load_clients_config, save_clients_config
)

# ── API keys desde secrets (nunca expuestas en UI) ─────────────────────────────
GROQ_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
META_TOKEN  = st.secrets.get("META_ACCESS_TOKEN", os.getenv("META_ACCESS_TOKEN", ""))
META_COUNTRY = "AR"

# ── Ícono de la app (torre de vigilancia amarilla) ─────────────────────────────
_icon_path = Path(__file__).parent / "assets" / "atalaya_icon.png"
PAGE_ICON = Image.open(_icon_path) if _icon_path.exists() else "🗼"

# ── Config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATALAYA · Monitor",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos Bound ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

/* Reset & base */
html, body, [class*="css"], .stApp {
    background-color: #0a0a0a !important;
    color: #e8e8e8 !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right: 1px solid #1e1e1e !important;
}

/* Tipografía */
h1, h2, h3, h4, h5 {
    font-family: 'Space Mono', monospace !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #ffffff !important;
}

/* Header principal */
.bound-header {
    border-bottom: 1px solid #1e1e1e;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}
.bound-header .eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: #FFFF00;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.bound-header h1 {
    font-size: 2.2rem;
    margin: 0 0 0.3rem;
    line-height: 1.1;
}
.bound-header .sub {
    font-size: 0.8rem;
    color: #555;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.1em;
}

/* Roll counter (sidebar) */
.roll-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    color: #333;
    text-transform: uppercase;
    padding: 0.2rem 0;
    border-top: 1px solid #1e1e1e;
    margin-top: 1.5rem;
}

/* Metric cards */
.metric-grid { display: flex; gap: 1px; margin-bottom: 2rem; }
.metric-cell {
    flex: 1;
    background: #111;
    border: 1px solid #1e1e1e;
    padding: 1.2rem 1rem;
}
.metric-cell .num {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #fff;
    line-height: 1;
}
.metric-cell .lbl {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #444;
    margin-top: 0.3rem;
    font-family: 'Space Mono', monospace;
}

/* Competitor card */
.comp-card {
    border: 1px solid #1e1e1e;
    border-left: 2px solid #FFFF00;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.5rem;
    background: #0f0f0f;
}
.comp-card .roll {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #FFFF00;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.comp-card .name { font-weight: 600; font-size: 0.95rem; color: #fff; }
.comp-card .url  { font-size: 0.75rem; color: #444; font-family: 'Space Mono', monospace; }

/* Report container */
.report-wrap {
    background: #0f0f0f;
    border: 1px solid #1e1e1e;
    padding: 2.5rem;
    line-height: 1.8;
    font-size: 0.92rem;
}
.report-wrap h1, .report-wrap h2, .report-wrap h3 {
    color: #fff !important;
    border-bottom: 1px solid #1e1e1e;
    padding-bottom: 0.4rem;
    margin-top: 1.8rem;
}
.report-wrap strong { color: #fff; }
.report-wrap li { color: #bbb; }

/* Botón primario */
.stButton > button {
    background: #FFFF00 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.5rem !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #CCCC00 !important; }

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #111 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 0 !important;
    color: #e8e8e8 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar nav radio */
.stRadio > div { gap: 0 !important; }
.stRadio label {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 0 !important;
    color: #555 !important;
    border-bottom: 1px solid #1a1a1a !important;
}
.stRadio label:has(input:checked) { color: #fff !important; }

/* Progress */
.stProgress > div > div > div { background: #FFFF00 !important; }
.stProgress p { color: #aaa !important; font-family: "Space Mono", monospace !important; font-size: 0.65rem !important; letter-spacing: 0.1em !important; }

/* Expander */
.streamlit-expanderHeader {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: #111 !important;
    border: 1px solid #1e1e1e !important;
    color: #aaa !important;
}
.streamlit-expanderContent { background: #0f0f0f !important; border: 1px solid #1e1e1e !important; }

/* Divider */
hr { border-color: #1e1e1e !important; }

/* Info/success/error */
.stAlert { border-radius: 0 !important; border-left: 2px solid #FFFF00 !important; background: #111 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "clients" not in st.session_state:
    st.session_state.clients = load_clients_config()
if "selected_client_idx" not in st.session_state:
    st.session_state.selected_client_idx = 0
if "current_report" not in st.session_state:
    st.session_state.current_report = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 0.5rem 0 1.5rem'>
        <div style='font-family: Space Mono, monospace; font-size: 0.6rem; letter-spacing: 0.2em; color: #FFFF00; text-transform: uppercase; margin-bottom: 0.3rem'>Aenima · Bound</div>
        <div style='font-family: Space Mono, monospace; font-size: 1rem; font-weight: 700; color: #fff; text-transform: uppercase; letter-spacing: 0.1em'>ATALAYA</div>
        <div style='font-family: Space Mono, monospace; font-size: 0.6rem; color: #333; letter-spacing: 0.1em; text-transform: uppercase'>Monitor · v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    client_names = [c["name"] for c in st.session_state.clients] if st.session_state.clients else []
    if client_names:
        selected = st.selectbox("Cliente activo", client_names, label_visibility="collapsed")
        st.session_state.selected_client_idx = client_names.index(selected)
        st.caption(f"▶ {selected}")
    else:
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#444;text-transform:uppercase;letter-spacing:0.1em'>Sin cliente activo</div>", unsafe_allow_html=True)

    st.divider()

    page = st.radio(
        "NAV",
        ["/ Clientes", "/ Escanear", "/ Reportes"],
        label_visibility="collapsed"
    )

    # Status de config
    st.markdown("<br>", unsafe_allow_html=True)
    groq_ok = "🟢" if GROQ_KEY else "🔴"
    meta_ok   = "🟢" if META_TOKEN  else "🔴"
    st.markdown(f"""
    <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#444;text-transform:uppercase;letter-spacing:0.1em;line-height:2'>
        {groq_ok} GROQ API<br>
        {meta_ok} META TOKEN
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="roll-tag">
        EST. 2016 · AR<br>
        REC ● {datetime.now().strftime("%H:%M:%S")}
    </div>
    """, unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="bound-header">
    <div class="eyebrow">Aenima · Inteligencia Competitiva</div>
    <h1>ATALAYA · Monitor</h1>
    <div class="sub">SCAN / ANALYZE / REPORT &nbsp;·&nbsp; {datetime.now().strftime("%d.%m.%Y")}</div>
</div>
""", unsafe_allow_html=True)

# Validación de keys
if not GROQ_KEY:
    st.error("⚠ GROQ_API_KEY no configurada en secrets. Contactá al administrador.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
if page == "/ Clientes":
    col_list, col_form = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("#### AGREGAR CLIENTE")
        with st.container(border=True):
            client_name = st.text_input("Nombre del cliente", placeholder="Ej: Paladini")
            st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#555;text-transform:uppercase;letter-spacing:0.1em;margin:0.8rem 0 0.4rem'>Competidores · Hasta 6</div>", unsafe_allow_html=True)

            competitors = []
            for i in range(1, 7):
                with st.expander(f"COMP {i:02d}", expanded=(i <= 2)):
                    c_name = st.text_input("Nombre", key=f"cn_{i}", placeholder="Ej: La Salamandra")
                    c_url  = st.text_input("Sitio web", key=f"cu_{i}", placeholder="https://...")
                    c_fb   = st.text_input("Página Facebook/IG", key=f"cf_{i}", placeholder="Ej: LaSalamandraAR")
                    if c_name:
                        competitors.append({"name": c_name, "url": c_url, "facebook_page": c_fb})

            if st.button("GUARDAR CLIENTE", use_container_width=True):
                if client_name and competitors:
                    new_client = {"name": client_name, "competitors": competitors}
                    existing = [c for c in st.session_state.clients if c["name"] == client_name]
                    if existing:
                        idx = st.session_state.clients.index(existing[0])
                        st.session_state.clients[idx] = new_client
                    else:
                        st.session_state.clients.append(new_client)
                    save_clients_config(st.session_state.clients)
                    st.success(f"Cliente '{client_name}' guardado · {len(competitors)} competidor(es)")
                    st.rerun()
                else:
                    st.error("Completá nombre y al menos un competidor")

    with col_list:
        st.markdown("#### CLIENTES ACTIVOS")
        if not st.session_state.clients:
            st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#333;text-transform:uppercase;letter-spacing:0.1em;padding:2rem 0'>— Sin clientes configurados —</div>", unsafe_allow_html=True)
        else:
            for i, client in enumerate(st.session_state.clients):
                st.markdown(f"""
                <div class="comp-card">
                    <div class="roll">ROLL · {i+1:03d}</div>
                    <div class="name">{client['name'].upper()}</div>
                    <div class="url">{len(client['competitors'])} COMPETIDORES CONFIGURADOS</div>
                </div>
                """, unsafe_allow_html=True)
                for comp in client["competitors"]:
                    url_str = comp.get('url','')
                    st.markdown(f"<div style='font-size:0.75rem;color:#444;padding:0.1rem 0 0.1rem 1rem;font-family:Space Mono,monospace'>· {comp['name'].upper()} {('— ' + url_str) if url_str else ''}</div>", unsafe_allow_html=True)
                if st.button("ELIMINAR", key=f"del_{i}"):
                    st.session_state.clients.pop(i)
                    save_clients_config(st.session_state.clients)
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ESCANEAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "/ Escanear":
    if not st.session_state.clients:
        st.warning("Primero configurá un cliente en / Clientes")
        st.stop()

    client = st.session_state.clients[st.session_state.selected_client_idx]
    competitors = client["competitors"]

    st.markdown(f"""
    <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#FFFF00;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.3rem'>
        CLIENTE ACTIVO
    </div>
    <div style='font-family:Space Mono,monospace;font-size:1.3rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:1.5rem'>
        {client['name']}
    </div>
    """, unsafe_allow_html=True)

    # Métricas
    web_count  = sum(1 for c in competitors if c.get("url"))
    meta_count = sum(1 for c in competitors if c.get("facebook_page"))
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-cell"><div class="num">{len(competitors):02d}</div><div class="lbl">Competidores</div></div>
        <div class="metric-cell"><div class="num">{web_count:02d}</div><div class="lbl">Sitios Web</div></div>
        <div class="metric-cell"><div class="num">{meta_count:02d}</div><div class="lbl">Páginas Meta</div></div>
    </div>
    """, unsafe_allow_html=True)

    col_opts, col_btn = st.columns([2, 1])
    with col_opts:
        do_web  = st.checkbox("Scrapear sitios web", value=True)
        do_meta = st.checkbox("Consultar Meta Ads Library", value=bool(META_TOKEN))
        if do_meta and not META_TOKEN:
            st.caption("META_ACCESS_TOKEN no configurado en secrets")

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_scan = st.button("▶ INICIAR SCAN", use_container_width=True)

    if run_scan:
        all_data = []
        total_steps = len(competitors) * (int(do_web) + int(do_meta)) + 1
        step = 0
        progress = st.progress(0, text="")

        for comp in competitors:
            comp_data = {"competitor": comp["name"], "web": None, "meta_ads": None}

            if do_web and comp.get("url"):
                progress.progress(step / total_steps,
                    text=f"SCAN · {comp['name'].upper()} · WEB")
                comp_data["web"] = scrape_website(comp["url"])
                step += 1

            if do_meta and META_TOKEN and comp.get("facebook_page"):
                progress.progress(step / total_steps,
                    text=f"SCAN · {comp['name'].upper()} · META ADS")
                comp_data["meta_ads"] = get_meta_ads(comp["facebook_page"], META_TOKEN, META_COUNTRY)
                step += 1

            all_data.append(comp_data)

        save_scan(client["name"], {"scanned_at": datetime.now().isoformat(), "data": all_data})

        progress.progress(step / total_steps, text="ANALYZING · GROQ PROCESSING...")
        prev = get_last_report(client["name"])
        prev_md = prev["report_markdown"] if prev else None

        report = generate_report(client["name"], all_data, GROQ_KEY, prev_md)
        progress.progress(1.0, text="COMPLETE ●")

        if report["status"] == "ok":
            save_report(client["name"], report)
            st.session_state.current_report = report
            st.success("SCAN COMPLETO · Reporte generado")
        else:
            st.error(f"ERROR · {report['error']}")

    if st.session_state.current_report and st.session_state.current_report.get("report_markdown"):
        st.divider()
        st.markdown(f"""
        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#FFFF00;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:1rem'>
            OUTPUT · REPORTE GENERADO
        </div>
        """, unsafe_allow_html=True)
        st.markdown(
            f'<div class="report-wrap">{st.session_state.current_report["report_markdown"]}</div>',
            unsafe_allow_html=True
        )
        from pdf_report import generate_pdf
        pdf_bytes = generate_pdf(
            client["name"],
            st.session_state.current_report["report_markdown"],
            datetime.now().strftime("%d.%m.%Y"),
            client.get("competitors", [])
        )
        st.download_button(
            "↓ DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"atalaya_{client['name'].lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )


# ══════════════════════════════════════════════════════════════════════════════
# REPORTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "/ Reportes":
    if not st.session_state.clients:
        st.warning("Primero configurá un cliente")
        st.stop()

    client = st.session_state.clients[st.session_state.selected_client_idx]

    st.markdown(f"""
    <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#FFFF00;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.3rem'>
        HISTORIAL
    </div>
    <div style='font-family:Space Mono,monospace;font-size:1.3rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:1.5rem'>
        {client['name']}
    </div>
    """, unsafe_allow_html=True)

    reports = list_reports(client["name"])

    if not reports:
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#333;text-transform:uppercase;letter-spacing:0.1em;padding:2rem 0'>— Sin reportes. Hacé tu primer scan. —</div>", unsafe_allow_html=True)
    else:
        selected_path = st.selectbox(
            "Seleccionar reporte",
            options=[r["path"] for r in reports],
            format_func=lambda p: next(
                (f"ROLL {i+1:03d} · {r['generated_at'][:16].replace('T',' ')} · {r['status'].upper()}"
                 for i, r in enumerate(reports) if r["path"] == p), p
            )
        )
        if selected_path:
            data = load_report(selected_path)
            md = data.get("report_markdown", "")
            if md:
                st.markdown(f'<div class="report-wrap">{md}</div>', unsafe_allow_html=True)
                from pdf_report import generate_pdf
                pdf_bytes = generate_pdf(
                    client["name"],
                    md,
                    data.get("generated_at", "")[:10].replace("-", "."),
                    client.get("competitors", [])
                )
                st.download_button(
                    "↓ DESCARGAR PDF",
                    data=pdf_bytes,
                    file_name=f"atalaya_{selected_path.split('/')[-1].replace('.json','.pdf')}",
                    mime="application/pdf"
                )