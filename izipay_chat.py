import streamlit as st
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Zona horaria de Lima, Perú
LIMA_TZ = ZoneInfo("America/Lima")

# Configuración de la página
st.set_page_config(
    page_title="Chat izipay",
    page_icon="🤖",
    layout="wide"
)

# ─────────────────────────────────────────
# ENDPOINTS por temática
# ─────────────────────────────────────────
ENDPOINTS = {
    # Bloque 1 - endpoint genérico /conversation
    "app_izipay":             "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    "izipay_ya":              "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    "soporte_tecnico":        "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    "agente_izipay":          "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    "retiro_inmediato":       "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    "arisale":                "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    "compra_estatus_pedido":  "https://dev-chat-izipay-postventa-genai-api-460336703195.us-central1.run.app/conversation",
    # Bloque 4 - microservicios propios (confirmados)
    "ventas_abonos":          "https://dev-chat-izipay-postventa-veab-genai-api-v1-vx462fvktq-uc.a.run.app/conversation",
    "datos_comercio":         "https://dev-chat-izipay-postventa-daco-genai-api-v1-vx462fvktq-uc.a.run.app/conversation",
    # Bloque 4 - pendiente confirmar con Juan Carlos
    "productos_virtuales":    None,
    "solicitud_contometros":  None,
}

KNOWLEDGE_STORES = {
    "app_izipay":            ["dev_izipay_index_apiz_azureopenai"],
    "izipay_ya":             ["dev_izipay_index_izya_azureopenai"],
    "soporte_tecnico":       ["dev_izipay_index_sote_azureopenai_2"],
    "agente_izipay":         ["dev_izipay_index_agiz_azureopenai"],
    "retiro_inmediato":      ["dev_izipay_index_rein_azureopenai"],
    "arisale":               ["dev_izipay_index_aris_azureopenai"],
    "compra_estatus_pedido": ["dev_izipay_index_coes_azureopenai"],
}

# Temáticas con microservicio propio (body simplificado)
TEMATICAS_BLOQUE4 = {"ventas_abonos", "datos_comercio", "productos_virtuales", "solicitud_contometros"}


def call_api(message, user_id=None, session_id=None, tematica="app_izipay"):
    try:
        url = ENDPOINTS.get(tematica)

        if url is None:
            return "⚠️ Endpoint no disponible aún para esta temática. Consultar con el equipo técnico.", "error"

        API_HEADERS = {
            "Content-Type": "application/json",
            "token": "dev-chatpgt-token-xbpr435"
        }

        if tematica in TEMATICAS_BLOQUE4:
            # Bloque 4: body simplificado según manual de endpoints
            body = {
                "question": message,
                "metadata": {
                    "userId": user_id,
                    "channelType": "Demo-Web",
                    "sessionId": session_id
                },
                "configuration": {},
                "save": True
            }
        else:
            # Bloque 1: body completo con knowledge stores
            body = {
                "question": message,
                "metadata": {
                    "userId": user_id,
                    "channelType": "Demo-Web",
                    "sessionId": session_id
                },
                "configuration": {
                    "business_case": "Asistente virtual de Izipay",
                    "prompt_params": {
                        "assistant_name": "Izi",
                        "assistant_role": "el experto digital en soluciones de pago",
                        "company_name": "Izipay",
                        "company_activity": "proveer las mejores soluciones de pago del mercado, incluyendo terminales POS (Izi Smart, Izi Jr), cobros online y gestión de ventas para emprendedores y empresas.",
                        "company_mission": "Empoderar a los negocios con respuestas rápidas, fáciles de entender y soluciones efectivas.",
                        "conversation_purpose": "Resolver dudas sobre el funcionamiento de los POS, tasas, afiliación y soporte técnico básico. Tu meta es que el usuario sienta que usar Izipay es fácil ('Izi')."
                    },
                    "config_params": {
                        "maxMinutes": "None",
                        "temperature": 0.3,
                        "k_top_retrieval": 3
                    },
                    "knowledge_stores": KNOWLEDGE_STORES.get(tematica, [])
                }
            }

        response = requests.post(url, headers=API_HEADERS, json=body, timeout=90)

        if response.status_code == 200:
            result = response.json()
            return {
                "answer":            result.get("answer", "Sin respuesta disponible"),
                "trace":             result.get("trace", ""),
                "trace_description": result.get("trace_description", ""),
                "citations":         result.get("citations", []),
                "satisfaction":      result.get("satisfaction", ""),
                "transfer":          result.get("transfer", ""),
                "finish":            result.get("finish", ""),
                "current_agent":     result.get("current_agent", ""),
                "raw_response":      result
            }, None
        else:
            return f"Error API: {response.status_code} - {response.text}", "error"

    except requests.exceptions.RequestException as e:
        return f"Error de conexión: {str(e)}", "error"
    except Exception as e:
        return f"Error inesperado: {str(e)}", "error"


# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"SESSION-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
if "user_id" not in st.session_state:
    st.session_state.user_id = f"USER-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
if "tematica_seleccionada" not in st.session_state:
    st.session_state.tematica_seleccionada = "app_izipay"

# ─────────────────────────────────────────
# TÍTULO
# ─────────────────────────────────────────
TEMATICA_NOMBRES = {
    "app_izipay":            "App Izipay",
    "izipay_ya":             "Izipay YA",
    "soporte_tecnico":       "Soporte técnico",
    "agente_izipay":         "Agente Izipay",
    "retiro_inmediato":      "Retiro Inmediato",
    "arisale":               "Arisale",
    "compra_estatus_pedido": "Compra o estatus de mi pedido",
    "ventas_abonos":         "Mis ventas y abonos",
    "datos_comercio":        "Mis datos de comercio",
    "productos_virtuales":   "Otros productos virtuales",
    "solicitud_contometros": "Solicitud de contómetros",
}

tematica_nombre = TEMATICA_NOMBRES.get(st.session_state.tematica_seleccionada, "Chat Izipay")
st.title(f"🤖 {tematica_nombre}")

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.header("🗂️ Temáticas")

    def sidebar_button(label, key):
        is_active = st.session_state.tematica_seleccionada == key
        if st.button(label, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.tematica_seleccionada = key
            st.session_state.messages = []
            st.session_state.session_id = f"SESSION-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
            st.rerun()

    sidebar_button("📱 App Izipay",                    "app_izipay")
    sidebar_button("🚀 Izipay YA",                     "izipay_ya")
    sidebar_button("🛠️ Soporte técnico",               "soporte_tecnico")
    sidebar_button("🏪 Agente Izipay",                 "agente_izipay")
    sidebar_button("💸 Retiro inmediato",              "retiro_inmediato")
    sidebar_button("💳 Arisale",                       "arisale")
    sidebar_button("📦 Compra o estatus de mi pedido", "compra_estatus_pedido")
    sidebar_button("💰 Mis ventas y abonos",           "ventas_abonos")
    sidebar_button("🏢 Mis datos de comercio",         "datos_comercio")
    sidebar_button("🌐 Otros productos virtuales",     "productos_virtuales")
    sidebar_button("📄 Solicitud de contómetros",      "solicitud_contometros")

    st.markdown("---")
    st.subheader("⚙️ Gestión de Usuario y Sesión")

    with st.expander("Ver Usuario y Sesión", expanded=False):
        st.caption("Usuario")
        st.text_input("User ID", value=st.session_state.user_id, disabled=True, label_visibility="collapsed")
        st.caption("Sesión")
        st.text_input("Session ID", value=st.session_state.session_id, disabled=True, label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 Nuevo Usuario", help="Reinicia identidad y chat", use_container_width=True):
            st.session_state.user_id    = f"USER-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
            st.session_state.session_id = f"SESSION-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
            st.session_state.messages   = []
            st.rerun()
    with col2:
        if st.button("💬 Nueva Sesión", help="Mantiene usuario, reinicia chat", use_container_width=True):
            st.session_state.session_id = f"SESSION-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Limpiar Historial", use_container_width=True, type="primary"):
        st.session_state.messages   = []
        st.session_state.session_id = f"SESSION-{datetime.now(LIMA_TZ).strftime('%Y%m%d%H%M%S')}"
        st.rerun()

# ─────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("timestamp"):
                st.caption(f"🕐 {message['timestamp']}")

if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    timestamp = datetime.now(LIMA_TZ).strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": timestamp})

    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"🕐 {timestamp}")

    with st.chat_message("assistant"):
        with st.spinner("Respondiendo..."):
            response_data, error = call_api(
                prompt,
                st.session_state.user_id,
                st.session_state.session_id,
                st.session_state.tematica_seleccionada
            )

        if error:
            st.error(response_data)
            response_text = "Lo siento, ocurrió un error al procesar tu mensaje."
            response_info = None
        else:
            response_text = response_data["answer"]
            response_info = response_data

        st.markdown(response_text)
        response_timestamp = datetime.now(LIMA_TZ).strftime("%H:%M")
        st.caption(f"🕐 {response_timestamp}")

        if response_info and response_info.get("trace_description"):
            with st.expander("📋 Información adicional"):
                if response_info.get("trace"):
                    st.write(f"**Traza:** {response_info['trace']}")
                st.write(f"**Descripción de la traza:** {response_info['trace_description']}")
                st.write(f"**Satisfacción:** {response_info['satisfaction']}")
                st.write(f"**Transferir:** {response_info['transfer']}")
                st.write(f"**Finalizar:** {response_info['finish']}")
                if response_info.get("current_agent"):
                    st.write(f"**Agente actual:** {response_info['current_agent']}")
                if response_info.get("citations"):
                    st.write("**Citas:**")
                    for citation in response_info["citations"][:3]:
                        option = citation.get("metadata", {}).get("option", "N/A")
                        st.write(f"- {option}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": response_timestamp,
            "metadata": response_info
        })
