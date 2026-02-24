import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from supabase import create_client, Client
import time

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="TradePro Cloud", layout="wide", page_icon="🦅")

st.markdown("""
<style>
    /* --- ESTILOS GENERALES --- */
    .stApp { background-color: #f5f7f9; color: #31333F; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #1f77b4; }
    
    /* --- BOTONES --- */
    div.stButton > button {
        background-color: #2E86C1; color: white; border-radius: 8px; font-weight: bold;
        border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { 
        background-color: #1B4F72; color: white; transform: translateY(-2px);
    }
    
    /* --- FORMULARIOS --- */
    [data-testid="stForm"] { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    
    /* --- FOOTER / FIRMA (FIXED) --- */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ffffff;
        color: #808080;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #e0e0e0;
        z-index: 999;
    }
    
    .block-container { padding-bottom: 70px; }
</style>

<div class="footer">
    <p>Developed by <b>William Ruiz</b> for all users | TradePro 🦅 | © 2026</p>
</div>
""", unsafe_allow_html=True)

# --- LISTAS MAESTRAS ---
LISTA_ACTIVOS = ["XAUUSD (Oro)", "SPX500 (S&P 500)", "NDX100 (Nasdaq)"]
LISTA_ESTRATEGIAS = ["Pullback", "Rompimiento", "Reversión", "Continuidad", "Smart Money", "Scalping", "Caza Spikes"]
LISTA_EMOCIONES = ["🎯 Confiado", "😨 Miedo", "😡 Venganza", "🤩 Euforia", "😴 Aburrido", "😰 Ansioso"]
LISTA_SESIONES = ["Londres", "Nueva York", "Asia", "Cierre Londres", "Pre-Mercado", "Indefinido"]
LISTA_ORIGEN = ["Propio", "Señal", "Mentoría", "Bot"]

# ==============================================================================
# 2. CONEXIÓN Y AUTENTICACIÓN
# ==============================================================================

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None
if 'session' not in st.session_state: st.session_state.session = None

if st.session_state.session is not None:
    try:
        supabase.auth.set_session(
            st.session_state.session.access_token, 
            st.session_state.session.refresh_token
        )
    except Exception as e:
        st.warning("La sesión ha expirado.")
        st.session_state.user = None
        st.session_state.session = None

def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = response.user
        st.session_state.session = response.session
        st.success("🔓 Acceso concedido")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error de acceso: {e}")

def register(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        st.session_state.user = response.user
        st.session_state.session = response.session
        st.success("✉️ Usuario creado.")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error de registro: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.session = None
    st.rerun()

# ==============================================================================
# 3. MOTOR DE DATOS
# ==============================================================================

def cargar_datos():
    if not st.session_state.user: return pd.DataFrame()
    
    try:
        response = supabase.table("trades").select("*").order("fecha", desc=True).execute()
        df = pd.DataFrame(response.data)
        
        if df.empty: return pd.DataFrame()
        
        rename_map = {
            "fecha": "Fecha", "hora_entrada": "Hora_Entrada", "hora_salida": "Hora_Salida", 
            "activo": "Activo", "direccion": "Direccion", "estrategia": "Estrategia", 
            "origen": "Origen", "lotaje": "Lotaje", "precio_entrada": "Precio_Entrada", 
            "precio_salida": "Precio_Salida", "resultado_neto": "Resultado_Neto", 
            "resultado_bruto": "Resultado_Bruto", "resultado_texto": "Resultado",
            "comision": "Comision", "swap": "Swap", "emocion": "Emocion", "sesion": "Sesion",
            "stop_loss": "Stop_Loss", "take_profit": "Take_Profit", "rr_planeado": "RR_Planeado"
        }
        
        cols_existentes = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=cols_existentes)
        
        if "Fecha" in df.columns: df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        if "Resultado_Neto" in df.columns: df['Resultado_Neto'] = pd.to_numeric(df['Resultado_Neto'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

def guardar_registro(data):
    if not st.session_state.user: return False
    
    try:
        payload = {
            "user_id": st.session_state.user.id,
            "fecha": str(data["Fecha"]),
            "hora_entrada": str(data["Hora_Entrada"]),
            "hora_salida": str(data["Hora_Salida"]),
            "activo": data["Activo"],
            "direccion": data["Direccion"],
            "estrategia": data["Estrategia"],
            "origen": data["Origen"],
            "precio_entrada": data["Precio_Entrada"],
            "precio_salida": data["Precio_Salida"],
            "stop_loss": data["Stop_Loss"],
            "take_profit": data["Take_Profit"],
            "lotaje": data["Lotaje"],
            "comision": data["Comision"],
            "swap": data["Swap"],
            "resultado_bruto": data["Resultado_Bruto"],
            "resultado_neto": data["Resultado_Neto"],
            "resultado_texto": data["Resultado"],
            "rr_planeado": data["RR_Planeado"],
            "emocion": data["Emocion"],
            "sesion": data["Sesion"]
        }
        supabase.table("trades").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Fallo al guardar: {e}")
        return False

def calcular_rr(entrada, sl, tp):
    try:
        riesgo = abs(entrada - sl)
        beneficio = abs(entrada - tp)
        return round(beneficio / riesgo, 2) if riesgo != 0 else 0.0
    except: return 0.0

# ==============================================================================
# 4. FLUJO PRINCIPAL
# ==============================================================================

if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True) 
        st.markdown("<h1 style='text-align: center;'>🦅 TradePro Cloud</h1>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align: center; color: gray;'>Accede a tu terminal segura</h5>", unsafe_allow_html=True)
        st.markdown("---")
        
        tab_log, tab_reg = st.tabs(["🔑 Ingresar", "📝 Registrarse"])
        with tab_log:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Iniciar Sesión", use_container_width=True): login(email, password)
        with tab_reg:
            with st.form("reg_form"):
                new_email = st.text_input("Email")
                new_pass = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Crear Cuenta", use_container_width=True): register(new_email, new_pass)
    st.stop()

# --- APP PRINCIPAL (SIDEBAR) ---
df = cargar_datos()

with st.sidebar:
    st.success(f"🟢 {st.session_state.user.email}")
    if st.button("Cerrar Sesión", type="secondary"): logout()
    
    st.divider()
    st.header("💼 Configuración")
    capital_inicial = st.number_input("Capital Inicial ($)", min_value=0.0, value=1000.0, step=100.0)
    
    pnl_historico = df["Resultado_Neto"].sum() if not df.empty else 0
    balance_dinamico = capital_inicial + pnl_historico
    st.metric("💰 Balance Dinámico", f"${balance_dinamico:,.2f}", f"{pnl_historico:,.2f} USD")

    st.header("🔍 Filtros Globales")
    f_activo, f_estrat = [], []
    if not df.empty:
        f_activo = st.multiselect("Activo", df["Activo"].unique())
        f_estrat = st.multiselect("Estrategia", df["Estrategia"].unique())

st.title("🦅 Panel de Comando")
tab1, tab2, tab3 = st.tabs(["📝 Registrar Operación", "📈 Master Dashboard", "🗃️ Bitácora Detallada"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("trade_form", clear_on_submit=True):
        st.subheader("Nuevo Trade")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        fecha = c1.date_input("Fecha", date.today())
        hora_in = c2.time_input("Hora Entrada", datetime.now().time(), step=60)
        hora_out = c3.time_input("Hora Salida", datetime.now().time(), step=60)
        sesion = c4.selectbox("Sesión", LISTA_SESIONES)
        emocion = c5.selectbox("Psicología", LISTA_EMOCIONES)

        c6, c7, c8, c9 = st.columns(4)
        activo = c6.selectbox("Activo", LISTA_ACTIVOS)
        direccion = c7.selectbox("Dirección", ["BUY", "SELL", "BUY LIMIT", "SELL LIMIT"])
        estrategia = c8.selectbox("Estrategia", LISTA_ESTRATEGIAS)
        origen = c9.selectbox("Origen", LISTA_ORIGEN)

        st.markdown("---")
        c10, c11, c12, c13 = st.columns(4)
        precio_in = c10.number_input("Precio Entrada", format="%.5f")
        sl = c11.number_input("Stop Loss", format="%.5f")
        tp = c12.number_input("Take Profit", format="%.5f")
        lotaje = c13.number_input("Lotaje", min_value=0.001, step=0.01, format="%.3f")

        # Casilla de multiplicador eliminada para una vista más limpia
        c14, c15 = st.columns(2)
        comision = c14.number_input("Comisión ($)", min_value=0.0, step=0.1, format="%.2f")
        swap = c15.number_input("Swap ($)", step=0.1, format="%.2f")
        
        st.markdown("---")
        st.markdown("<h5 style='text-align: center;'>Registrar Resultado de la Operación</h5>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        btn_ganada = col_btn1.form_submit_button("🟢 GANADA", use_container_width=True)
        btn_perdida = col_btn2.form_submit_button("🔴 PERDIDA", use_container_width=True)

        if btn_ganada or btn_perdida:
            estado_trade = "Ganada" if btn_ganada else "Perdida"
            precio_out_auto = tp if btn_ganada else sl
            
            # MAGIA MATEMÁTICA: Calculamos la diferencia real de puntos
            if "BUY" in direccion:
                diff = precio_out_auto - precio_in
            else: # Es un SELL
                diff = precio_in - precio_out_auto
            
            # MULTIPLICADOR INVISIBLE: Determinado automáticamente por el activo seleccionado
            if "XAUUSD" in activo:
                multiplicador_oculto = 100
            elif "SPX" in activo or "NDX" in activo:
                multiplicador_oculto = 10
            else:
                multiplicador_oculto = 1
                
            # Calculamos el dinero exacto
            resultado_bruto = diff * lotaje * multiplicador_oculto
            neto = resultado_bruto - comision + swap
            
            rr_calc = calcular_rr(precio_in, sl, tp)
            
            nuevo_trade = {
                "Fecha": fecha, "Hora_Entrada": hora_in, "Hora_Salida": hora_out,
                "Activo": activo, "Direccion": direccion, "Estrategia": estrategia, 
                "Origen": origen, "Lotaje": lotaje, "Precio_Entrada": precio_in, 
                "Precio_Salida": precio_out_auto, "Stop_Loss": sl, "Take_Profit": tp, 
                "RR_Planeado": rr_calc, "Comision": comision, "Swap": swap,
                "Resultado_Bruto": resultado_bruto, "Resultado_Neto": neto, 
                "Resultado": estado_trade, "Emocion": emocion, "Sesion": sesion
            }
            
            if guardar_registro(nuevo_trade):
                if neto > 0: st.balloons()
                st.success(f"✅ Operación {estado_trade} registrada automáticamente. Neto: ${neto:.2f}")
                time.sleep(2) 
                st.rerun()

# --- TAB 2: DASHBOARD ---
with tab2:
    if not df.empty:
        df_view = df.copy()
        if f_activo: df_view = df_view[df_view["Activo"].isin(f_activo)]
        if f_estrat: df_view = df_view[df_view["Estrategia"].isin(f_estrat)]
        
        pnl_total_dash = df_view["Resultado_Neto"].sum()
        balance_actual = capital_inicial + pnl_total_dash
        
        trades_total = len(df_view)
        wins = df_view[df_view["Resultado_Neto"] > 0]
        losses = df_view[df_view["Resultado_Neto"] <= 0]
        win_rate = (len(wins) / trades_total * 100) if trades_total > 0 else 0
        
        ganancias_por_activo = df_view.groupby("Activo")["Resultado_Neto"].sum()
        mejor_activo = ganancias_por_activo.idxmax() if not ganancias_por_activo.empty else "N/A"
        peor_activo = ganancias_por_activo.idxmin() if not ganancias_por_activo.empty else "N/A"

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Balance Actual", f"${balance_actual:,.2f}", f"{pnl_total_dash:,.2f} PnL")
        k2.metric("📊 Win Rate", f"{win_rate:.1f}%", f"{len(wins)}W - {len(losses)}L")
        
        if mejor_activo != "N/A":
            k3.metric(f"🏆 Mejor Activo ({mejor_activo})", f"${ganancias_por_activo.max():,.2f}")
            k4.metric(f"🔻 Peor Activo ({peor_activo})", f"${ganancias_por_activo.min():,.2f}")

        st.divider()

        df_sorted = df_view.sort_values(["Fecha", "Hora_Entrada"])
        df_sorted["CumPnL"] = df_sorted["Resultado_Neto"].cumsum()
        df_sorted["Equity"] = capital_inicial + df_sorted["CumPnL"]

        g1, g2 = st.columns([2, 1])
        with g1:
            fig_eq = px.line(df_sorted, x="Fecha", y="Equity", title="🚀 Curva de Crecimiento (Equity)", markers=True)
            fig_eq.add_hline(y=capital_inicial, line_dash="dash", line_color="gray", annotation_text="Capital Inicial")
            st.plotly_chart(fig_eq, use_container_width=True)
        
        with g2:
            fig_psy = px.pie(df_view, names="Emocion", title="🧠 Estado Psicológico", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_psy, use_container_width=True)

    else:
        st.info("👋 Registra tu primer trade para desbloquear el Dashboard.")

# --- TAB 3: BITÁCORA ---
with tab3:
    if not df.empty:
        df_log = df.copy()
        if f_activo: df_log = df_log[df_log["Activo"].isin(f_activo)]
        if f_estrat: df_log = df_log[df_log["Estrategia"].isin(f_estrat)]

        df_log = df_log.sort_values(by=["Fecha"], ascending=True)
        df_log["Acumulado"] = capital_inicial + df_log["Resultado_Neto"].cumsum()
        
        df_log = df_log.sort_values(by=["Fecha"], ascending=False)
        
        if "Hora_Entrada" in df_log.columns:
            df_log["Hora_Entrada"] = pd.to_datetime(df_log["Hora_Entrada"], errors='coerce').dt.strftime('%H:%M')
        if "Hora_Salida" in df_log.columns:
            df_log["Hora_Salida"] = pd.to_datetime(df_log["Hora_Salida"], errors='coerce').dt.strftime('%H:%M')

        cols_show = [
            "Fecha", "Hora_Entrada", "Hora_Salida", "Activo", "Direccion", 
            "Estrategia", "Lotaje", "Precio_Entrada", "Stop_Loss", "Take_Profit", 
            "Comision", "Resultado", "Resultado_Neto", "Acumulado", "Emocion"
        ]
        
        cols_final = [c for c in cols_show if c in df_log.columns]
        
        st.dataframe(
            df_log[cols_final],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Resultado_Neto": st.column_config.NumberColumn("Valor Ganado/Perdido", format="$%.2f"),
                "Acumulado": st.column_config.NumberColumn("Acumulado", format="$%.2f"),
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            }
        )
    else:
        st.write("Bitácora vacía.")