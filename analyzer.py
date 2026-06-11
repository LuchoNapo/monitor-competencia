"""
Genera reportes de inteligencia competitiva usando Groq API (gratuita).
Modelo: llama-3.3-70b-versatile — rápido, contexto largo, free tier generoso.
"""
import json
from datetime import datetime
from groq import Groq


SYSTEM_PROMPT = """Sos un analista de inteligencia competitiva especializado en marketing digital latinoamericano.
Tu trabajo es analizar datos de competidores y generar reportes accionables para agencias de publicidad.
Escribís en español argentino, con tono profesional pero directo. Sin vueltas."""


def build_analysis_prompt(client_name: str, competitors_data: list, previous_report: str = None) -> str:
    data_str = json.dumps(competitors_data, ensure_ascii=False, indent=2)

    prev_context = ""
    if previous_report:
        prev_context = f"""
--- REPORTE ANTERIOR (para comparar cambios) ---
{previous_report[:2000]}
--- FIN REPORTE ANTERIOR ---
"""

    return f"""Analizá los siguientes datos de competidores del cliente "{client_name}".
{prev_context}
DATOS RECOPILADOS:
{data_str}

Generá un reporte de inteligencia competitiva con esta estructura EXACTA en Markdown:

# Monitor de Competencia — {client_name}
**Fecha:** {datetime.now().strftime("%d/%m/%Y")}

## Resumen Ejecutivo
(3-4 oraciones con los hallazgos más importantes)

## Análisis por Competidor
Para cada competidor:
### [Nombre del competidor]
- **Qué está comunicando:**
- **Tono y posicionamiento:**
- **Avisos pagos activos:** (cantidad y descripción general)
- **Cambios respecto al período anterior:** (si hay datos previos)

## Tendencias del Mercado
(Patrones comunes entre competidores: temas, promociones, formatos)

## Oportunidades para {client_name}
(Gaps concretos que los competidores no están cubriendo — mínimo 3 puntos accionables)

## Alertas
(Movimientos urgentes a tener en cuenta: lanzamientos, cambios de pricing, nuevas campañas agresivas)

Sé específico y accionable. Evitá generalidades. Si no hay datos suficientes de algún competidor, indicalo claramente."""


def generate_report(
    client_name: str,
    competitors_data: list,
    api_key: str,
    previous_report: str = None
) -> dict:
    result = {
        "generated_at": datetime.now().isoformat(),
        "client_name": client_name,
        "model": "llama-3.3-70b-versatile",
        "status": "ok",
        "report_markdown": "",
        "error": None,
        "usage": None,        # tokens usados en esta llamada
        "rate_limit": None,   # estado del límite diario
    }

    try:
        client = Groq(api_key=api_key)
        prompt = build_analysis_prompt(client_name, competitors_data, previous_report)

        # with_raw_response permite leer los headers de rate limit
        raw = client.chat.completions.with_raw_response.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.4,
            max_tokens=4096,
        )
        response = raw.parse()
        result["report_markdown"] = response.choices[0].message.content

        # Tokens usados en esta llamada
        if response.usage:
            result["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        # Estado del límite diario desde los headers
        h = raw.headers
        result["rate_limit"] = {
            "limit_tokens": h.get("x-ratelimit-limit-tokens"),
            "remaining_tokens": h.get("x-ratelimit-remaining-tokens"),
            "reset_tokens": h.get("x-ratelimit-reset-tokens"),
            "limit_requests": h.get("x-ratelimit-limit-requests"),
            "remaining_requests": h.get("x-ratelimit-remaining-requests"),
        }

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result