import streamlit as st
import calendar
import datetime
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any

# ==============================
# Configurações da página
# ==============================
st.set_page_config(page_title="📆 Calendário de Eventos", layout="centered", initial_sidebar_state="expanded")

# ==============================
# Variáveis e Funções de Sheets (Mantidas)
# ==============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
    except KeyError:
        st.error("O secret 'gcp_service_account' não foi encontrado. Por favor, configure-o para usar o Google Sheets.")
        st.stop()
        
    try:
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        # Substitua pelo ID real da sua planilha
        SPREADSHEET_ID = "1ZZG2JJCQ4-N7Jd34hG2GUWMTPDYcVlGfL6ODTi6GYmM" 
        return client.open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.stop()

sheet = get_gspread_client()

@st.cache_data(ttl=60) 
def load_reminders() -> List[Dict[str, Any]]:
    rows = sheet.get_all_records()
    reminders = []
    today = datetime.date.today()
    ids_to_delete = []

    for r in rows:
        required_keys = ["id","title","description","date","created_by","color"]
        if not all(k in r for k in required_keys): continue
        
        try:
            date_obj = datetime.date.fromisoformat(r["date"])
        except ValueError: continue
            
        if date_obj < today - datetime.timedelta(days=10):
            ids_to_delete.append(r["id"])
            continue
            
        reminders.append(r)

    for reminder_id in ids_to_delete:
        delete_reminder(reminder_id, force_update=False) 

    return reminders

def add_reminder(title, description, date_obj, created_by, color):
    new_id = str(datetime.datetime.now().timestamp())
    sheet.append_row([new_id, title, description, date_obj.isoformat(), created_by, color])
    load_reminders.clear() 
    
def delete_reminder(reminder_id, force_update: bool = True):
    all_values = sheet.get_all_values()
    for idx, row in enumerate(all_values, start=1):
        if len(row) > 0 and row[0] == reminder_id:
            sheet.delete_rows(idx)
            if force_update:
                load_reminders.clear()
            break

def get_reminders_for_day(reminders: List[Dict], day: datetime.date) -> List[Dict[str, Any]]:
    return [r for r in reminders if r["date"] == day.isoformat()]

# ==============================
# Estilos customizados
# ==============================
st.markdown(
    """
    <style>
    /* Estilos globais e Sidebar */
    body { font-family: 'Inter', sans-serif; background-color: #f7f9fc; }
    h1, h2, h3 { text-align: center; color: #1f2937; }
    
    section[data-testid="stSidebar"] { background: #2c3e50; color: white; border-right: 1px solid #1a252f; box-shadow: 2px 0 5px rgba(0,0,0,0.15); }
    section[data-testid="stSidebar"] * { color: white; }
    section[data-testid="stSidebar"] div.reminder-card { padding: 10px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); border-left: 5px solid; background-color: #34495e; }
    
    /* --- CALENDÁRIO GERAL --- */
    div[data-testid^="stHorizontalBlock"] > div { display: flex; flex-direction: column; padding: 0 4px !important; }

    /* Contêiner da célula do dia (Borda e Fundo) */
    .day-cell-wrapper {
        position: relative; 
        width: 100%;
        aspect-ratio: 1 / 1;
        margin: 0 auto;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px; 
        height: 100%;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        overflow: hidden; 
    }
    
    .day-other-month-style { opacity: 0.5; background-color: #f7f9fc !important; border-color: #f0f0f0 !important; }

    /* Número do dia - NOVO: Centralizado Totalmente (Vertical e Horizontal) */
    .day-number-container {
        position: absolute; 
        top: 50%; /* 50% do topo */
        left: 50%; /* 50% da esquerda */
        transform: translate(-50%, -50%); /* Ajusta o elemento em -50% da sua própria largura/altura */
        font-weight: bold;
        font-size: 14px; 
        color: #1f2937;
        padding: 0; 
        line-height: 1.4;
        z-index: 2;
        width: auto; 
        text-align: center; 
        pointer-events: none; /* Garante que o número não atrapalhe cliques no dia */
    }
    
    .day-other-month-style .day-number-container { color: #6b7280; }
    
    .today-style .day-number-container > span {
        color: #4b89dc !important;
    }

    /* --- FAIXA DE EVENTO --- */
    .reminder-strip {
        position: absolute;
        bottom: 24px; /* Acima do botão */
        left: 0;
        width: 100%;
        height: 20px; 
        padding: 2px 4px;
        color: white;
        font-size: 10px;
        font-weight: 600;
        display: flex;
        justify-content: center;
        align-items: center;
        text-shadow: 0 0 1px rgba(0,0,0,0.5);
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        z-index: 3; 
    }
    .reminder-strip-title {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 95%;
    }
    
    /* --- BOTÃO DETALHES --- */
    /* Container do botão st.button: Reduz o padding lateral do Streamlit para encaixar melhor */
    .day-cell-wrapper div[data-testid="stButton"] {
        position: absolute;
        bottom: 0px;
        left: 0;
        width: 100%;
        margin: 0 !important;
        padding: 4px 5px !important; 
        z-index: 4;
        display: flex; 
        justify-content: center;
    }
    
    /* Botão em si: Define um tamanho fixo */
    .day-cell-wrapper button.details-btn {
        font-size: 10px;
        padding: 1px 4px;
        border-radius: 4px;
        font-weight: 500;
        background-color: #f0f0f0 !important;
        color: #333 !important; 
        border: 1px solid #ccc !important;
        transition: all 0.2s;
        height: 22px; 
        line-height: 1;
        width: 100%; 
        max-width: 100%;
        text-align: center;
    }
    .day-cell-wrapper button.details-btn:hover {
        background-color: #e0e0e0 !important;
    }
    .selected-day-style {
        border: 2px solid #ff4b4b !important;
        background-color: #ffe0e0 !important;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# Interface Principal
# ==============================

st.title("🗓️ **Calendário de Eventos**")

reminders = load_reminders()
today = datetime.date.today()

if "calendar_view_date" not in st.session_state:
    st.session_state.calendar_view_date = today

if "selected_day" not in st.session_state:
    st.session_state.selected_day = None

year, month = st.session_state.calendar_view_date.year, st.session_state.calendar_view_date.month
cal = calendar.Calendar(firstweekday=0) 
month_days = cal.monthdatescalendar(year, month)

col_prev, col_month, col_next = st.columns([1, 4, 1])

def navigate_month(delta: int):
    current_date = st.session_state.calendar_view_date
    new_month = current_date.month + delta
    try:
        new_date = current_date.replace(month=new_month)
    except ValueError:
        if new_month > 12:
            new_date = current_date.replace(year=current_date.year + 1, month=1)
        elif new_month < 1:
            new_date = current_date.replace(year=current_date.year - 1, month=12)
    st.session_state.calendar_view_date = new_date
    st.session_state.selected_day = None 
    
col_prev.button("◀️ Anterior", on_click=navigate_month, args=(-1,))
col_next.button("Próximo ▶️", on_click=navigate_month, args=(1,))

month_name_pt = calendar.month_name[month].capitalize()
col_month.subheader(f"{month_name_pt} {year}")

st.markdown("---")

weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
week_cols = st.columns(7, gap="small")
for i, wd in enumerate(weekdays):
    week_cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #4b89dc;'>{wd}</div>", unsafe_allow_html=True)

# Lógica de clique para abrir/fechar a sidebar
def handle_details_click(day_iso: str):
    """Define o dia selecionado e abre a sidebar."""
    if st.session_state.selected_day == day_iso:
        st.session_state.selected_day = None # Desselecionar
    else:
        st.session_state.selected_day = day_iso


# Renderizar dias do mês
for week in month_days:
    cols = st.columns(7, gap="small")
    for i, day in enumerate(week):
        day_iso = day.isoformat()
        day_reminders = get_reminders_for_day(reminders, day)
        
        # Classes CSS
        classes = "day-cell-wrapper"
        if day.month != month: classes += " day-other-month-style"
        if day == today: classes += " today-style"
        # Adiciona a classe de estilo de seleção (borda) se estiver selecionado
        if day_iso == st.session_state.selected_day: classes += " selected-day-style"
        
        with cols[i]:
            st.markdown(f"<div class='{classes}'>", unsafe_allow_html=True)
            
            # 1. Número do dia (Posição absoluta centralizada)
            st.markdown(f"<div class='day-number-container'><span>{day.day}</span></div>", unsafe_allow_html=True)

            # 2. Faixa de Evento e Botão Detalhes (só se houverem lembretes)
            if day_reminders:
                # Usa o primeiro lembrete para a cor e o título na faixa
                first_reminder = day_reminders[0]
                strip_color = first_reminder['color']
                strip_title = first_reminder['title']
                
                # Se houver mais de um, adiciona um contador
                if len(day_reminders) > 1:
                    strip_title += f" (+{len(day_reminders)-1})"
                
                # Injeta a faixa colorida (posição absoluta)
                st.markdown(
                    f"""
                    <div class="reminder-strip" style="background-color: {strip_color};">
                        <span class="reminder-strip-title">{strip_title}</span>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # 3. Botão Detalhes (Posição absoluta na base)
                btn_key_details = f"details_btn_{day_iso}"
                
                # Usamos um contêiner Streamlit normal, mas ajustamos seu estilo no CSS
                if st.button("Detalhes", key=btn_key_details):
                    handle_details_click(day_iso)
                
                # Injeta a classe CSS personalizada no botão "Detalhes"
                st.markdown(
                    f"""
                    <script>
                    setTimeout(() => {{
                        const btn = window.document.querySelector('button[data-testid*="{btn_key_details}"]');
                        if(btn) {{ btn.classList.add('details-btn'); }}
                    }}, 10);
                    </script>
                    """, unsafe_allow_html=True
                )
            
            # Fechamento do div .day-cell-wrapper
            st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# Sidebar de detalhes
# ==============================
if st.session_state.selected_day:
    day = datetime.date.fromisoformat(st.session_state.selected_day)
    day_reminders = get_reminders_for_day(reminders, day)
    
    if day_reminders:
        st.sidebar.markdown(f"## 📌 Eventos: {day.strftime('%d/%m/%Y')}")
        
        for r in day_reminders:
            card_style = f"border-color: {r['color']};"
            
            with st.sidebar.form(key=f"delete_form_{r['id']}"):
                st.markdown(
                    f"""
                    <div class="reminder-card" style="{card_style}">
                        <div style="color: white;"><b>{r['title']}</b></div>
                        <p style='margin: 4px 0 6px 0; color: #ccc;'><small>{r['description'] or 'Sem descrição'}</small></p>
                        <hr style='margin: 4px 0; border-top: 1px solid #444;'>
                        <small style="color: #ccc;">Criado por: <i>{r['created_by']}</i></small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                submitted_delete = st.form_submit_button("🗑️ Excluir Evento", help="Excluir Lembrete Permanentemente")
                
                if submitted_delete:
                     delete_reminder(r["id"])
                     st.session_state.selected_day = None 
                     st.rerun() 
    else:
         st.session_state.selected_day = None


# ==============================
# Formulário de Novo Lembrete (Mantido)
# ==============================
st.markdown("---")
st.subheader("➕ Adicionar Novo Evento")

with st.container(border=True):
    col_user, col_color = st.columns([2, 1])
    
    user = col_user.text_input("👤 **Seu Nome**", "Anônimo")
    color = col_color.color_picker("🎨 **Cor do Evento**", "#4b89dc") 

    with st.form("new_reminder", clear_on_submit=True):
        title = st.text_input("📝 **Título do Evento**", max_chars=50)
        description = st.text_area("🗒️ **Descrição**")
        
        default_date = datetime.date.today()
        if st.session_state.selected_day:
            try:
                default_date = datetime.date.fromisoformat(st.session_state.selected_day)
            except ValueError:
                pass
            
        date_input = st.date_input("🗓️ **Data**", 
                                   value=default_date, 
                                   min_value=datetime.date.today())
                                   
        submitted = st.form_submit_button("✅ **Salvar Evento**")
        
        if submitted:
            if not title:
                st.error("O **Título** é obrigatório!")
            else:
                add_reminder(title, description, date_input, user, color)
                st.success("🎉 Evento adicionado com sucesso! Atualizando o calendário...")
                st.rerun()
