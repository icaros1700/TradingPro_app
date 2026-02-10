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
    .stApp { background-color: #f5f7f9; color: #31333F; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #1f77b4; }
    div.stButton > button {
        background-color: #2E86C1; color: white; border-radius: 8px; font-weight: bold;
        border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover { background-color: #1B4F72; color: white; }
    [data-testid="stForm"] { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# Listas Maestras
LISTA_ACTIVOS = ["Boom 300", "Boom 500", "Boom 1000", "Crash 300", "Crash 500", "Crash 1000", "Volatility 75", "EURUSD", "XAUUSD", "US30", "BTCUSD"]
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

if 'user' not in st.session_state:
    st.session_state.user = None
if 'session' not in st.session_state:
    st.session_state.session = None

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
            "fecha": "Fecha", "hora": "Hora", "activo": "Activo", "direccion": "Direccion",
            "estrategia": "Estrategia", "origen": "Origen", "lotaje": "Lotaje",
            "precio_entrada": "Precio_Entrada", "precio_salida": "Precio_Salida",
            "resultado_neto": "Resultado_Neto", "resultado_bruto": "Resultado_Bruto",
            "comision": "Comision", "swap": "Swap", "emocion": "Emocion", "sesion": "Sesion",
            "stop_loss": "Stop_Loss", "take_profit": "Take_Profit", "rr_planeado": "RR_Planeado"
        }
        
        cols_existentes = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=cols_existentes)
        
        if "Fecha" in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        if "Resultado_Neto" in df.columns:
            df['Resultado_Neto'] = pd.to_numeric(df['Resultado_Neto'], errors='coerce').fillna(0)
            
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
            "hora": str(data["Hora"]),
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
        st.title("🦅 TradePro Cloud")
        st.markdown("##### Accede a tu terminal segura")
        
        tab_log, tab_reg = st.tabs(["🔑 Ingresar", "📝 Registrarse"])
        with tab_log:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Iniciar Sesión", use_container_width=True):
                    login(email, password)
        with tab_reg:
            with st.form("reg_form"):
                new_email = st.text_input("Email")
                new_pass = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Crear Cuenta", use_container_width=True):
                    register(new_email, new_pass)
    st.stop()

# --- SIDEBAR & CAPITAL INICIAL ---
with st.sidebar:
    st.success(f"🟢 {st.session_state.user.email}")
    if st.button("Cerrar Sesión", type="secondary"):
        logout()
    
    st.divider()
    st.header("💼 Configuración")
    # --- NUEVO: CAPITAL INICIAL ---
    capital_inicial = st.number_input("Capital Inicial ($)", min_value=0.0, value=1000.0, step=100.0, help="Define con cuánto iniciaste para ver el balance real.")

    st.header("🔍 Filtros Globales")
    df = cargar_datos()
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
        c1, c2, c3, c4 = st.columns(4)
        fecha = c1.date_input("Fecha", date.today())
        hora = c2.time_input("Hora", datetime.now().time())
        sesion = c3.selectbox("Sesión", LISTA_SESIONES)
        emocion = c4.selectbox("Psicología", LISTA_EMOCIONES)

        c5, c6, c7, c8 = st.columns(4)
        activo = c5.selectbox("Activo", LISTA_ACTIVOS)
        direccion = c6.selectbox("Dirección", ["BUY", "SELL", "BUY LIMIT", "SELL LIMIT"])
        estrategia = c7.selectbox("Estrategia", LISTA_ESTRATEGIAS)
        origen = c8.selectbox("Origen", LISTA_ORIGEN)

        st.markdown("---")
        c9, c10, c11, c12 = st.columns(4)
        precio_in = c9.number_input("Precio Entrada", format="%.5f")
        sl = c10.number_input("Stop Loss", format="%.5f")
        tp = c11.number_input("Take Profit", format="%.5f")
        lotaje = c12.number_input("Lotaje", min_value=0.001, step=0.01, format="%.3f")

        c13, c14, c15 = st.columns(3)
        precio_out = c13.number_input("Precio Salida", format="%.5f")
        comision = c14.number_input("Comisión ($)", min_value=0.0, step=0.1, format="%.2f")
        swap = c15.number_input("Swap ($)", step=0.1, format="%.2f")
        
        st.markdown("---")
        res_previo = 0.0
        if precio_out > 0:
            diff = (precio_out - precio_in) if "BUY" in direccion else (precio_in - precio_out)
            res_previo = diff * lotaje 
            st.info(f"💡 Estimación Bruta: ${res_previo:.2f}")

        res_manual = st.number_input("Ganancia/Pérdida Bruta Real ($)", value=float(res_previo), step=1.0, format="%.2f")

        if st.form_submit_button("🚀 EJECUTAR REGISTRO", type="primary", use_container_width=True):
            neto = res_manual - comision + swap
            rr_calc = calcular_rr(precio_in, sl, tp)
            
            nuevo_trade = {
                "Fecha": fecha, "Hora": hora, "Activo": activo, "Direccion": direccion,
                "Estrategia": estrategia, "Origen": origen, "Lotaje": lotaje, 
                "Precio_Entrada": precio_in, "Precio_Salida": precio_out,
                "Stop_Loss": sl, "Take_Profit": tp, "RR_Planeado": rr_calc,
                "Comision": comision, "Swap": swap,
                "Resultado_Bruto": res_manual, "Resultado_Neto": neto,
                "Emocion": emocion, "Sesion": sesion
            }
            
            if guardar_registro(nuevo_trade):
                if neto > 0: st.balloons()
                st.success(f"✅ Registrado. Neto: ${neto:.2f}")
                time.sleep(1)
                st.rerun()

# --- TAB 2: DASHBOARD ---
with tab2:
    if not df.empty:
        df_view = df.copy()
        if f_activo: df_view = df_view[df_view["Activo"].isin(f_activo)]
        if f_estrat: df_view = df_view[df_view["Estrategia"].isin(f_estrat)]
        
        # --- CÁLCULOS DE BALANCE ---
        pnl_total = df_view["Resultado_Neto"].sum()
        balance_actual = capital_inicial + pnl_total # <--- NUEVO CÁLCULO
        
        trades_total = len(df_view)
        wins = df_view[df_view["Resultado_Neto"] > 0]
        losses = df_view[df_view["Resultado_Neto"] <= 0]
        win_rate = (len(wins) / trades_total * 100) if trades_total > 0 else 0
        pf = (wins["Resultado_Neto"].sum() / abs(losses["Resultado_Neto"].sum())) if not losses.empty else 0

        # --- MÉTRICAS SUPERIORES ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Balance Actual", f"${balance_actual:,.2f}", f"{pnl_total:,.2f} PnL") # <--- NUEVA MÉTRICA
        k2.metric("📊 Win Rate", f"{win_rate:.1f}%", f"{len(wins)}W - {len(losses)}L")
        k3.metric("⚖️ Profit Factor", f"{pf:.2f}")
        
        # Drawdown básico
        df_sorted = df_view.sort_values("Fecha")
        df_sorted["CumPnL"] = df_sorted["Resultado_Neto"].cumsum()
        df_sorted["Equity"] = capital_inicial + df_sorted["CumPnL"]
        df_sorted["Peak"] = df_sorted["Equity"].cummax()
        df_sorted["DD"] = df_sorted["Equity"] - df_sorted["Peak"]
        max_dd = df_sorted["DD"].min()
        k4.metric("📉 Max Drawdown", f"${max_dd:,.2f}")

        st.divider()

        # --- GRÁFICOS NIVEL 1 ---
        g1, g2 = st.columns([2, 1])
        with g1:
            # GRÁFICO DE EQUITY (CURVA DE CRECIMIENTO)
            fig_eq = px.line(df_sorted, x="Fecha", y="Equity", title="🚀 Curva de Crecimiento (Equity)", markers=True)
            fig_eq.add_hline(y=capital_inicial, line_dash="dash", line_color="gray", annotation_text="Capital Inicial")
            st.plotly_chart(fig_eq, use_container_width=True)
        
        with g2:
            # GRÁFICO DE PSICOLOGÍA (NUEVO)
            fig_psy = px.pie(df_view, names="Emocion", title="🧠 Estado Psicológico", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_psy, use_container_width=True)

        st.divider()
        
        # --- GRÁFICOS NIVEL 2 (HORA DORADA Y ACTIVOS) ---
        g3, g4 = st.columns(2)
        
        with g3:
            # GRÁFICO DE HORA DORADA (NUEVO)
            # Extraemos la hora simple (0-23)
            df_view["Hora_Simple"] = pd.to_datetime(df_view["Hora"].astype(str)).dt.hour
            hourly_pnl = df_view.groupby("Hora_Simple")["Resultado_Neto"].sum().reset_index()
            
            fig_hour = px.bar(hourly_pnl, x="Hora_Simple", y="Resultado_Neto", 
                              title="⏰ Tu Hora Dorada (PnL por Hora)", 
                              color="Resultado_Neto", 
                              color_continuous_scale="RdBu",
                              labels={"Hora_Simple": "Hora del Día (0-23)", "Resultado_Neto": "Ganancia/Pérdida"})
            st.plotly_chart(fig_hour, use_container_width=True)
            

        with g4:
            # GRÁFICO DE ACTIVOS (MEJORADO)
            asset_pnl = df_view.groupby("Activo")["Resultado_Neto"].sum().reset_index().sort_values("Resultado_Neto", ascending=False)
            fig_asset = px.bar(asset_pnl, x="Resultado_Neto", y="Activo", orientation='h', 
                               title="🏆 Rendimiento por Activo", 
                               color="Resultado_Neto", 
                               color_continuous_scale="RdBu")
            st.plotly_chart(fig_asset, use_container_width=True)

    else:
        st.info("👋 Registra tu primer trade para desbloquear el Dashboard.")

# --- TAB 3: BITÁCORA ---
with tab3:
    if not df.empty:
        df_log = df.copy()
        if f_activo: df_log = df_log[df_log["Activo"].isin(f_activo)]
        if f_estrat: df_log = df_log[df_log["Estrategia"].isin(f_estrat)]

        cols_show = ["Fecha", "Hora", "Activo", "Direccion", "Estrategia", "Lotaje", "Precio_Entrada", "Precio_Salida", "Resultado_Neto", "Emocion"]
        cols_final = [c for c in cols_show if c in df_log.columns]
        
        st.dataframe(
            df_log[cols_final].sort_values("Fecha", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Resultado_Neto": st.column_config.NumberColumn("PnL", format="$%.2f"),
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            }
        )
    else:
        st.write("Bitácora vacía.")