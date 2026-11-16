"""
Hyperpersonalisation Lab
Tarea de viñetas sobre fraude ejecutivo hiperpersonalizado mediante IA.

Los participantes observan los mensajes que recibe un director de sucursal
bancaria ficticio en Valencia. Para cada mensaje puntúan cuánto les parece
legítimo (0-100) y eligen una acción. Al final se resume el rendimiento con
medidas de la teoría de detección de señales (aciertos, falsas alarmas, d', c).
"""

import json
import random
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from statistics import NormalDist

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Hyperpersonalisation Lab", layout="centered")

# ---------------------------------------------------------------------------
# Perfil ficticio
# ---------------------------------------------------------------------------
PROFILE = {
    "name": "Javier Ortega",
    "role": "Director de sucursal de un banco ficticio en Valencia (oficina de Ruzafa)",
    "public": [
        "Terminó el Medio Maratón de Valencia en 1:38 (lo publicó en Instagram)",
        "Participó en una mesa redonda sobre banca digital en un evento fintech en Madrid (LinkedIn)",
        "Estudió Administración y Dirección de Empresas en la Universitat de València (LinkedIn)",
        "Noticia en la prensa local sobre la reforma de su oficina",
    ],
    "private": [
        "Su hija Lucía tiene una función del colegio el próximo viernes",
        "Este mes hay una auditoría interna programada en su oficina",
        "La plataforma interna donde sube los informes se llama «Gestor»",
    ],
}

# ---------------------------------------------------------------------------
# Estímulos. is_fraud: True = fraudulento. data_source: tipo de dato personal
# que usa el mensaje (público = se encuentra en internet, privado = no).
# ---------------------------------------------------------------------------
MESSAGES = [
    {
        "id": "F1", "is_fraud": True, "data_source": "Dato público", "channel": "Correo electrónico",
        "sender": "Ana Ferrer, directora regional",
        "text": "Javier, enhorabuena por ese 1:38 en el medio, impresionante. Necesito que me "
                "hagas un favor antes de que se haga pública la adquisición: una transferencia "
                "de 48.000 € a un proveedor nuevo hoy mismo. Que quede entre nosotros hasta el "
                "lunes, estoy todo el día reunida.",
        "cues": "Urgencia, secreto y una petición de pago fuera de lo normal. El dato personal "
                "(el tiempo en la carrera) está publicado en Instagram, así que no demuestra "
                "nada sobre quién envía el mensaje.",
    },
    {
        "id": "F2", "is_fraud": True, "data_source": "Dato público", "channel": "WhatsApp",
        "sender": "Número desconocido",
        "text": "Hola Javier, soy Marcos, coincidimos en la mesa de banca digital de Madrid. "
                "Tengo número nuevo. Un cliente mío es de tu oficina y necesita que le aprueben "
                "una transferencia urgente antes de las 14:00, ¿me echas un cable?",
        "cues": "Número nuevo y un favor que se salta el procedimiento. La mesa redonda aparece "
                "en LinkedIn, cualquiera podría mencionarla.",
    },
    {
        "id": "F3", "is_fraud": True, "data_source": "Dato público", "channel": "LinkedIn",
        "sender": "Headhunter de una firma de selección",
        "text": "¡Otro exalumno de la UV por aquí! Tenemos un puesto directivo confidencial que "
                "encaja con tu perfil. Entra en nuestro portal de candidatos con tu correo y tu "
                "contraseña corporativos para ver la oferta.",
        "cues": "Pide las credenciales corporativas. La universidad compartida es pública en "
                "LinkedIn y se usa para crear una falsa familiaridad.",
    },
    {
        "id": "F4", "is_fraud": True, "data_source": "Dato público", "channel": "Correo electrónico",
        "sender": "Equipo de Seguridad Informática",
        "text": "Tras las obras de reforma en la oficina de Ruzafa, todas las cuentas de la "
                "sucursal deben volver a verificarse hoy. Utiliza el enlace de abajo para "
                "confirmar tu acceso o se suspenderá.",
        "cues": "Amenaza de suspensión y un enlace externo. La reforma salió en la prensa local, "
                "por eso da una credibilidad falsa.",
    },
    {
        "id": "L1", "is_fraud": False, "data_source": "Dato privado", "channel": "Correo electrónico",
        "sender": "Ana Ferrer, directora regional",
        "text": "Hola Javier, de cara a la auditoría de este mes, ¿puedes subir a Gestor el "
                "informe habitual de la oficina cuando puedas? Sin prisa, con que esté a final "
                "de semana vale.",
        "cues": "Usa datos privados (la auditoría, el nombre de la plataforma interna), sigue el "
                "canal habitual y no mete presión de tiempo.",
    },
    {
        "id": "L2", "is_fraud": False, "data_source": "Dato privado", "channel": "WhatsApp",
        "sender": "Hermana (contacto guardado)",
        "text": "¿Vienes el viernes a la función de Lucía? Mamá está guardando sitios.",
        "cues": "Contacto conocido, un dato familiar privado y ninguna petición de dinero ni de accesos.",
    },
    {
        "id": "L3", "is_fraud": False, "data_source": "Dato público", "channel": "Correo electrónico",
        "sender": "Recursos Humanos, programa de bienestar",
        "text": "Hemos visto tu publicación del medio maratón, ¡enhorabuena! Estamos montando un "
                "equipo de la plantilla para el 10K de primavera. Responde a este correo si te "
                "apetece apuntarte.",
        "cues": "Usa un dato público, pero no pide nada sensible ni tiene urgencia. Que un "
                "mensaje use datos públicos no lo convierte en fraude.",
    },
    {
        "id": "L4", "is_fraud": False, "data_source": "Dato público", "channel": "LinkedIn",
        "sender": "Antiguo compañero de clase",
        "text": "¡Javier! Te vi en la mesa de fintech, muy buena charla. Vuelvo a Valencia el "
                "mes que viene, ¿un café?",
        "cues": "Datos públicos, pero la petición es inofensiva y fácil de comprobar.",
    },
]

ACTIONS = ["Hacer lo que le piden", "Verificarlo por otro canal", "Marcarlo como sospechoso"]
THRESHOLD = 50  # por debajo de este valor se cuenta como juicio de «fraude»


# ---------------------------------------------------------------------------
# Pantalla inicial (aviso legal + instrucciones)
# ---------------------------------------------------------------------------
INTRO_CSS = """
<style>
.hl-section {margin: 1.6rem 0 0.8rem 0; display:flex; align-items:center; gap:.6rem;}
.hl-section .num {width:1.9rem; height:1.9rem; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-weight:700; font-size:.95rem;
  background:#4f6bed; color:#fff;}
.hl-section h3 {margin:0; padding:0; font-size:1.25rem;}
.hl-grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:.8rem;}
.hl-card {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:1rem 1.1rem;
  background:rgba(128,128,128,.06); border-left:4px solid #4f6bed;}
.hl-card .title {font-weight:700; margin-bottom:.3rem; font-size:.98rem;}
.hl-card .body {font-size:.88rem; opacity:.85; line-height:1.45;}
.hl-card.wide {grid-column:1/-1;}
.hl-steps {position:relative; margin-left:.9rem; padding-left:1.6rem;
  border-left:2px solid rgba(79,107,237,.45);}
.hl-step {position:relative; margin-bottom:1.1rem;}
.hl-step:last-child {margin-bottom:0;}
.hl-step .dot {position:absolute; left:-2.45rem; top:0; width:1.6rem; height:1.6rem;
  border-radius:50%; background:#4f6bed; color:#fff; font-size:.8rem; font-weight:700;
  display:flex; align-items:center; justify-content:center;}
.hl-step .title {font-weight:700; font-size:.98rem;}
.hl-step .body {font-size:.88rem; opacity:.85; line-height:1.45;}
.hl-time {display:inline-block; margin-top:1rem; padding:.3rem .8rem; border-radius:999px;
  background:rgba(79,107,237,.15); font-size:.85rem; font-weight:600;}
</style>
"""

INTRO_HTML = """
<div class="hl-section"><div class="num">1</div><h3>Información y consentimiento</h3></div>
<div class="hl-grid">
  <div class="hl-card">
    <div class="title">Qué es este estudio</div>
    <div class="body">Una investigación de un Trabajo Fin de Grado del doble grado en Derecho y
    Criminología de la Universidad Europea de Valencia sobre cómo juzgamos mensajes que usan
    datos personales. Todas las personas, empresas y mensajes son ficticios.</div></div>
  <div class="hl-card">
    <div class="title">Participación voluntaria</div>
    <div class="body">Participar es voluntario y no tiene ninguna consecuencia no hacerlo.
    Puedes dejarlo en cualquier momento cerrando la pestaña, y en ese caso no se guarda nada.
    Es necesario tener 18 años o más.</div></div>
  <div class="hl-card">
    <div class="title">Qué se guarda</div>
    <div class="body">Solo tus respuestas (puntuaciones, acciones elegidas y tiempo de respuesta),
    asociadas a un código aleatorio. No se te pide nombre, correo ni ningún otro dato que te
    identifique. Las respuestas se envían al terminar el último mensaje.</div></div>
  <div class="hl-card">
    <div class="title">Para qué se usan</div>
    <div class="body">Solo para el análisis estadístico de esta investigación y su posible
    publicación académica, siempre de forma agregada. Como los datos son anónimos, una vez
    enviados no es posible identificar ni retirar las respuestas de una persona concreta.</div></div>
  <div class="hl-card">
    <div class="title">Alojamiento</div>
    <div class="body">La aplicación funciona en Streamlit Community Cloud, que puede tratar datos
    técnicos como tu dirección IP conforme a su propia política de privacidad. Esos datos no
    llegan a la investigadora.</div></div>
  <div class="hl-card">
    <div class="title">Contacto</div>
    <div class="body">Investigadora responsable: Mar&iacute;a Mart&iacute;nez Melero, Universidad
    Europea de Valencia. No es una herramienta de seguridad ni asesoramiento profesional.</div></div>
</div>

<div class="hl-section"><div class="num">2</div><h3>Cómo funciona</h3></div>
<div class="hl-steps">
  <div class="hl-step"><div class="dot">1</div>
    <div class="title">Lee primero el perfil</div>
    <div class="body">Está en la columna de la izquierda (en el móvil, pulsa la flecha de arriba
    a la izquierda). Muestra lo que cualquiera puede encontrar sobre Javier en internet y lo que
    solo sabe su gente cercana. Puedes volver a consultarlo cuando quieras.</div></div>
  <div class="hl-step"><div class="dot">2</div>
    <div class="title">Ocho mensajes en orden aleatorio</div>
    <div class="body">Le llegan a Javier por correo, WhatsApp o LinkedIn. Algunos son
    fraudulentos y otros legítimos.</div></div>
  <div class="hl-step"><div class="dot">3</div>
    <div class="title">Puntúa y decide</div>
    <div class="body">Indica cuánto te parece legítimo cada mensaje, de 0 (seguro que es fraude)
    a 100 (seguro que es legítimo), y elige qué debería hacer Javier.</div></div>
  <div class="hl-step"><div class="dot">4</div>
    <div class="title">No se puede volver atrás</div>
    <div class="body">Cuando pulses <i>Siguiente</i>, esa respuesta queda registrada, así que
    tómate tu tiempo.</div></div>
  <div class="hl-step"><div class="dot">5</div>
    <div class="title">Mira tus resultados</div>
    <div class="body">Verás lo bien que has distinguido los fraudes de los mensajes legítimos,
    tu tendencia de respuesta y las señales que escondía cada mensaje.</div></div>
</div>
<div class="hl-time">Unos 5 minutos</div>
<br><br>
"""


# ---------------------------------------------------------------------------
# Estado de la sesión
# ---------------------------------------------------------------------------
def init_state():
    order = MESSAGES.copy()
    random.shuffle(order)
    st.session_state.order = order
    st.session_state.idx = 0
    st.session_state.responses = []
    st.session_state.participant_id = uuid.uuid4().hex[:12]
    st.session_state.shown_at = None
    st.session_state.sent = False


if "order" not in st.session_state:
    init_state()
if "started" not in st.session_state:
    st.session_state.started = False


def get_endpoint():
    """URL del script de Google que guarda las respuestas (en los secrets de Streamlit)."""
    try:
        return st.secrets["SHEET_ENDPOINT"]
    except Exception:
        return None


def send_responses(responses):
    """Envía las respuestas a la hoja de cálculo. Devuelve True si se guardaron."""
    url = get_endpoint()
    if not url:
        return False
    payload = json.dumps({"rows": responses}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except Exception:
        return False


def sdt(responses):
    """Tasa de aciertos, de falsas alarmas, d' y c con corrección log-lineal."""
    frauds = [r for r in responses if r["is_fraud"]]
    legits = [r for r in responses if not r["is_fraud"]]
    hits = sum(r["judged_fraud"] for r in frauds)
    fas = sum(r["judged_fraud"] for r in legits)
    hr = (hits + 0.5) / (len(frauds) + 1)
    far = (fas + 0.5) / (len(legits) + 1)
    z = NormalDist().inv_cdf
    d_prime = z(hr) - z(far)
    c = -0.5 * (z(hr) + z(far))
    return hits / len(frauds), fas / len(legits), d_prime, c


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------
st.title("Hyperpersonalisation Lab")
st.caption(
    "Una tarea de viñetas sobre fraude ejecutivo hiperpersonalizado con IA. "
    "Todas las personas, empresas y mensajes son ficticios."
)

with st.sidebar:
    st.subheader("Perfil de Javier")
    st.markdown(f"**{PROFILE['name']}**  \n{PROFILE['role']}")
    st.markdown("**Público (se encuentra en internet)**")
    for item in PROFILE["public"]:
        st.markdown(f"- {item}")
    st.markdown("**Privado (no está en internet)**")
    for item in PROFILE["private"]:
        st.markdown(f"- {item}")

total = len(st.session_state.order)
idx = st.session_state.idx

if not st.session_state.started:
    st.markdown(INTRO_CSS, unsafe_allow_html=True)
    st.markdown(INTRO_HTML, unsafe_allow_html=True)

    adult = st.checkbox("Tengo 18 años o más.")
    agreed = st.checkbox(
        "He leído la información anterior y doy mi consentimiento para participar "
        "y para que mis respuestas anónimas se usen en esta investigación."
    )
    if st.button("Empezar", type="primary", disabled=not (adult and agreed)):
        st.session_state.started = True
        st.rerun()

elif idx < total:
    msg = st.session_state.order[idx]
    if st.session_state.shown_at is None:
        st.session_state.shown_at = time.time()
    st.progress(idx / total, text=f"Mensaje {idx + 1} de {total}")

    with st.container(border=True):
        st.markdown(f"**{msg['channel']}** · de *{msg['sender']}*")
        st.write(msg["text"])

    with st.form(key=f"form_{msg['id']}"):
        rating = st.slider(
            "¿Cuánto te parece legítimo este mensaje? (0 = seguro que es fraude, 100 = seguro que es legítimo)",
            0, 100, 50,
        )
        action = st.radio("¿Qué debería hacer Javier?", ACTIONS, index=None)
        submitted = st.form_submit_button("Siguiente")

    if submitted:
        if action is None:
            st.warning("Elige una acción antes de continuar.")
        else:
            st.session_state.responses.append({
                "participant_id": st.session_state.participant_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "position": idx + 1,
                "id": msg["id"],
                "is_fraud": msg["is_fraud"],
                "data_source": msg["data_source"],
                "channel": msg["channel"],
                "rating": rating,
                "action": action,
                "judged_fraud": rating < THRESHOLD,
                "rt_seconds": round(time.time() - st.session_state.shown_at, 2),
            })
            st.session_state.shown_at = None
            st.session_state.idx += 1
            st.rerun()

else:
    responses = st.session_state.responses
    if not st.session_state.sent:
        with st.spinner("Guardando tus respuestas..."):
            st.session_state.sent = send_responses(responses)
    if st.session_state.sent:
        st.success("Tus respuestas se han guardado. ¡Gracias por participar!")
    else:
        st.warning("No se han podido guardar tus respuestas.")
        if st.button("Reintentar el envío"):
            st.rerun()

    hr, far, d_prime, c = sdt(responses)

    st.subheader("Tus resultados")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fraudes detectados", f"{hr:.0%}")
    col2.metric("Falsas alarmas", f"{far:.0%}")
    col3.metric("d'", f"{d_prime:.2f}".replace(".", ","))
    col4.metric("Criterio c", f"{c:.2f}".replace(".", ","))

    st.markdown(
        "**d'** mide lo bien que has distinguido los fraudes de los mensajes legítimos "
        "(0 = como lanzar una moneda, cuanto más alto, mejor). **c** muestra tu tendencia: "
        "si es negativo, tiendes a ver fraude en todo; si es positivo, tiendes a fiarte."
    )

    df = pd.DataFrame(responses)
    df["Tipo"] = df["is_fraud"].map({True: "Fraude", False: "Legítimo"})

    st.subheader("Legitimidad media que has dado")
    means = df.groupby(["Tipo", "data_source"])["rating"].mean().unstack()
    st.bar_chart(means)
    st.caption(
        "La pregunta clave: ¿hacen los datos personales públicos que un fraude parezca "
        "tan fiable como un mensaje legítimo?"
    )

    st.subheader("Mensaje a mensaje")
    lookup = {m["id"]: m for m in MESSAGES}
    for r in responses:
        m = lookup[r["id"]]
        correct = r["judged_fraud"] == r["is_fraud"]
        label = "Fraude" if m["is_fraud"] else "Legítimo"
        mark = "Acierto" if correct else "Fallo"
        with st.expander(f"{mark} · {m['channel']} de {m['sender']} · {label} · le diste {r['rating']}"):
            st.write(m["text"])
            st.info(m["cues"])

    st.download_button(
        "Descargar tus respuestas (CSV)",
        df.drop(columns=["Tipo"]).to_csv(index=False).encode("utf-8"),
        file_name="respuestas.csv",
        mime="text/csv",
    )
