import streamlit as st
import json
import os
from datetime import datetime

from scrapers.web_scraper import scrape_website
from scrapers.meta_ads import get_meta_ads
from analyzer import generate_report
from storage import (
    save_scan, save_report, get_last_report,
    list_reports, load_report, load_clients_config, save_clients_config
)

# ── Config de página ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitor de Competencia",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    .main-header {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2rem; }
    .main-header p { color: #aaa; margin: 0.3rem 0 0; font-size: 0.95rem; }

    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card .number { font-size: 2rem; font-weight: 700; color: #0f0f0f; font-family: 'Space Grotesk', sans-serif; }
    .metric-card .label { font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }

    .status-ok { color: #28a745; font-weight: 600; }
    .status-error { color: #dc3545; font-weight: 600; }

    .competitor-card {
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        background: white;
    }
    .competitor-card .comp-name { font-weight: 600; font-size: 1rem; }
    .competitor-card .comp-url { font-size: 0.8rem; color: #888; }

    .scan-btn > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        border-radius: 8px !important;
    }

    .report-container {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 2rem;
        line-height: 1.7;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "clients" not in st.session_state:
    st.session_state.clients = load_clients_config()
if "selected_client_idx" not in st.session_state:
    st.session_state.selected_client_idx = 0
if "last_scan_data" not in st.session_state:
    st.session_state.last_scan_data = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Monitor de Competencia")
    st.divider()

    # API Keys
    st.markdown("**Configuración de APIs**")
    anthropic_key = st.text_input("Gemini API Key", type="password",
                                   value=os.getenv("GEMINI_API_KEY", ""),
                                   help="Tu API Key de Google AI Studio (aistudio.google.com)")
    meta_token = st.text_input("Meta App Token", type="password",
                                value=os.getenv("META_ACCESS_TOKEN", ""),
                                help="app_id|app_secret de tu Meta App")
    meta_country = st.selectbox("País de ads", ["AR", "UY", "CL", "MX", "CO", "BR"], index=0)

    st.divider()

    # Selector de cliente
    client_names = [c["name"] for c in st.session_state.clients] if st.session_state.clients else []
    if client_names:
        selected = st.selectbox("Cliente activo", client_names)
        st.session_state.selected_client_idx = client_names.index(selected)
    else:
        st.info("Agregá un cliente primero →")

    st.divider()
    st.markdown("**Navegación**")
    page = st.radio("", ["Clientes", "Escanear", "Reportes"], label_visibility="collapsed")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔍 Monitor de Competencia</h1>
    <p>Inteligencia competitiva automatizada · Powered by Claude AI</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
if page == "Clientes":
    st.subheader("Gestión de clientes y competidores")

    col_list, col_form = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("#### Agregar / editar cliente")
        with st.container(border=True):
            client_name = st.text_input("Nombre del cliente", placeholder="Ej: Paladini")

            st.markdown("**Competidores** (podés agregar hasta 6)")
            competitors = []
            for i in range(1, 7):
                with st.expander(f"Competidor {i}", expanded=(i <= 2)):
                    c_name = st.text_input(f"Nombre", key=f"cn_{i}", placeholder="Ej: La Salamandra")
                    c_url = st.text_input(f"Sitio web", key=f"cu_{i}", placeholder="https://...")
                    c_fb = st.text_input(f"Página de Facebook/IG", key=f"cf_{i}", placeholder="Ej: LaSalamandraAR")
                    if c_name:
                        competitors.append({"name": c_name, "url": c_url, "facebook_page": c_fb})

            if st.button("💾 Guardar cliente", use_container_width=True):
                if client_name and competitors:
                    new_client = {"name": client_name, "competitors": competitors}
                    # Reemplazar si ya existe
                    existing = [c for c in st.session_state.clients if c["name"] == client_name]
                    if existing:
                        idx = st.session_state.clients.index(existing[0])
                        st.session_state.clients[idx] = new_client
                    else:
                        st.session_state.clients.append(new_client)
                    save_clients_config(st.session_state.clients)
                    st.success(f"✅ Cliente '{client_name}' guardado con {len(competitors)} competidor(es)")
                    st.rerun()
                else:
                    st.error("Completá el nombre del cliente y al menos un competidor")

    with col_list:
        st.markdown("#### Clientes configurados")
        if not st.session_state.clients:
            st.info("Todavía no hay clientes. Completá el formulario para agregar el primero.")
        else:
            for i, client in enumerate(st.session_state.clients):
                with st.container(border=True):
                    st.markdown(f"**{client['name']}**")
                    st.caption(f"{len(client['competitors'])} competidor(es) configurado(s)")
                    for comp in client["competitors"]:
                        url_str = f" · {comp['url']}" if comp.get("url") else ""
                        st.markdown(f"  • {comp['name']}{url_str}")
                    if st.button("🗑️ Eliminar", key=f"del_{i}"):
                        st.session_state.clients.pop(i)
                        save_clients_config(st.session_state.clients)
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: ESCANEAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Escanear":
    if not st.session_state.clients:
        st.warning("⚠️ Primero configurá un cliente en la sección **Clientes**.")
        st.stop()

    client = st.session_state.clients[st.session_state.selected_client_idx]
    competitors = client["competitors"]

    st.subheader(f"Escanear competidores de {client['name']}")

    # Métricas rápidas
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="number">{len(competitors)}</div>
            <div class="label">Competidores</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        web_count = sum(1 for c in competitors if c.get("url"))
        st.markdown(f"""<div class="metric-card">
            <div class="number">{web_count}</div>
            <div class="label">Sitios web</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        meta_count = sum(1 for c in competitors if c.get("facebook_page"))
        st.markdown(f"""<div class="metric-card">
            <div class="number">{meta_count}</div>
            <div class="label">Páginas Meta</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Opciones de escaneo
    col_opts, col_btn = st.columns([2, 1])
    with col_opts:
        do_web = st.checkbox("Scrapear sitios web", value=True)
        do_meta = st.checkbox("Consultar Meta Ads Library", value=bool(meta_token))
        if do_meta and not meta_token:
            st.warning("Necesitás el Meta App Token en la barra lateral")

    with col_btn:
        st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
        run_scan = st.button("🚀 Iniciar escaneo", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Escaneo ──
    if run_scan:
        if not anthropic_key:
            st.error("❌ Necesitás la Gemini API Key para generar el reporte (aistudio.google.com)")
            st.stop()

        all_data = []
        progress = st.progress(0, text="Iniciando escaneo...")
        total_steps = len(competitors) * (int(do_web) + int(do_meta)) + 1
        step = 0

        for comp in competitors:
            comp_data = {"competitor": comp["name"], "web": None, "meta_ads": None}

            if do_web and comp.get("url"):
                progress.progress(step / total_steps, text=f"🌐 Scrapeando {comp['name']}...")
                comp_data["web"] = scrape_website(comp["url"])
                step += 1

            if do_meta and meta_token and comp.get("facebook_page"):
                progress.progress(step / total_steps, text=f"📢 Meta Ads: {comp['name']}...")
                comp_data["meta_ads"] = get_meta_ads(comp["facebook_page"], meta_token, meta_country)
                step += 1

            all_data.append(comp_data)

        # Guardar scan crudo
        save_scan(client["name"], {"scanned_at": datetime.now().isoformat(), "data": all_data})

        # Generar reporte con Claude
        progress.progress(step / total_steps, text="🤖 Claude está analizando los datos...")
        prev = get_last_report(client["name"])
        prev_md = prev["report_markdown"] if prev else None

        report = generate_report(client["name"], all_data, anthropic_key, prev_md)
        step += 1
        progress.progress(1.0, text="✅ ¡Listo!")

        if report["status"] == "ok":
            save_report(client["name"], report)
            st.session_state.current_report = report
            st.success("✅ Escaneo completado. El reporte está listo.")
        else:
            st.error(f"❌ Error generando el reporte: {report['error']}")
            st.session_state.last_scan_data = all_data

    # Mostrar reporte actual
    if st.session_state.current_report and st.session_state.current_report.get("report_markdown"):
        st.markdown("---")
        st.markdown("### 📄 Reporte generado")
        with st.container():
            st.markdown(
                f'<div class="report-container">{st.session_state.current_report["report_markdown"]}</div>',
                unsafe_allow_html=True
            )
            # Botón de descarga
            st.download_button(
                "⬇️ Descargar reporte (.md)",
                data=st.session_state.current_report["report_markdown"],
                file_name=f"reporte_{client['name'].lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: REPORTES (historial)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Reportes":
    if not st.session_state.clients:
        st.warning("⚠️ Primero configurá un cliente.")
        st.stop()

    client = st.session_state.clients[st.session_state.selected_client_idx]
    st.subheader(f"Historial de reportes — {client['name']}")

    reports = list_reports(client["name"])

    if not reports:
        st.info("Todavía no hay reportes para este cliente. Hacé tu primer escaneo.")
    else:
        selected_report_path = st.selectbox(
            "Seleccioná un reporte",
            options=[r["path"] for r in reports],
            format_func=lambda p: next(
                (f"📄 {r['generated_at'][:16].replace('T',' ')} — {r['status']}"
                 for r in reports if r["path"] == p), p
            )
        )

        if selected_report_path:
            report_data = load_report(selected_report_path)
            md = report_data.get("report_markdown", "")
            if md:
                st.markdown(
                    f'<div class="report-container">{md}</div>',
                    unsafe_allow_html=True
                )
                st.download_button(
                    "⬇️ Descargar reporte",
                    data=md,
                    file_name=f"reporte_{selected_report_path.split('/')[-1].replace('.json','.md')}",
                    mime="text/markdown"
                )
            else:
                st.warning("Este reporte no tiene contenido.")
