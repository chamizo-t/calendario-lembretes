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
# Estilos customizados (Ajuste Final de Cursor)
# ==============================
st.markdown(
    """
    <style>
    /* Estilos globais */
    body { font-family: 'Inter', sans-serif; background-color: #f7f9fc; }
    h1, h2, h3 { text-align: center; color: #1f2937; }
    .st-emotion-cache-10trblm { color: #4b89dc !important; }

    /* --- SIDEBAR ESCURA E PROFISSIONAL --- */
    section[data-testid="stSidebar"] {
        background: #2c3e50;
        color: white;
        border-right: 1px solid #1a252f;
        box-shadow: 2px 0 5px rgba(0,0,0,0.15);
    }
    section[data-testid="stSidebar"] * { color: white; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #79a6dc;
    }
    section[data-testid="stSidebar"] div.reminder-card {
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        border-left: 5px solid; 
        background-color: #34495e;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: #e74c3c !important; 
        color: white !important;
        border-radius: 5px;
        padding: 4px 8px;
        font-size: 11px;
        line-height: 1;
        transition: background 0.2s;
        width: auto !important; 
        position: relative;
        z-index: 20;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: #c0392b !important;
    }

    /* --- CALENDÁRIO --- */
    .day-cell-wrapper {
        position: relative; 
        width: 100%;
        aspect-ratio: 1 / 1;
        margin: 0 auto;
    }
    
    .day-cell {
        border: 1px solid #e5e7eb;
        border-radius: 8px; 
        width: 100%; 
        height: 100%;
        text-align: center;
        transition: all 0.3s ease;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: white;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        pointer-events: none;
    }

    /* Dia de outro mês e selecionado (estilos visuais) */
    .day-other-month-style { opacity: 0.5; background-color: #f7f9fc !important; }
    .selected-style { border: 2px solid #ff4b4b !important; background-color: #ffe0e0 !important; }

    /* Número do dia */
    .day-number-container {
        font-weight: bold;
        font-size: 14px; 
        margin-bottom: 4px;
        color: #1f2937;
        padding: 1px; 
        transition: all 0.2s;
        line-height: 1.4;
    }
    .day-other-month-style .day-number-container { color: #6b7280; }
    
    /* DIA ATUAL (Anel Azul) */
    .today-style .day-number-container {
        background-color: transparent !important;
        color: #4b89dc !important;
        border: 2px solid #4b89dc; 
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Texto do lembrete */
    .reminder-title {
        font-size: 10px;
        margin-top: 2px;
        padding: 1px 4px;
        border-radius: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 90%;
        font-weight: 500;
        color: white !important; 
        text-shadow: 0 0 1px rgba(0,0,0,0.3);
    }
    
    /* Botão Streamlit que cobre a célula para o clique */
    .stButton>button {
        background: transparent !important; 
        color: transparent !important;
        border: none;
        box-shadow: none;
        
        /* CURSOR PADRÃO (Para seleção de dia) */
        cursor: default;
        
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
        z-index: 10; 
        transition: all 0.2s;
    }

    /* Cursor de PONTEIRO (Somente se a célula tiver a classe 'has-reminders') */
    .day-cell-wrapper.has-reminders .stButton>button {
        cursor: pointer;
    }
    
    /* Efeito de hover */
    .day-cell-wrapper.has-reminders .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        background: rgba(75, 137, 220, 0.1) !important; 
    }
    
    .st-emotion-cache-1n76cwh a{ display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# Conexão Google Sheets (Funções de Conexão e CRUD - Mantidas)
# ==============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_gspread_client():
    """Autoriza e retorna o cliente gspread."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        SPREADSHEET_ID = "1ZZG2JJCQ4-N7Jd34hG2GUWMTPDYcVlGfL6ODTi6GYmM"
        return client.open_by_key(SPREADSHEET_ID).sheet1
    except Exception:
        st.error("Erro ao conectar com o Google Sheets. Verifique o arquivo `secrets.toml`.")
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
# Interface Principal
# ==============================

st.title("🗓️ **Calendário de Eventos**")

reminders = load_reminders()
today = datetime.date.today()

if "calendar_view_date" not in st.session_state:
    st.session_state.calendar_view_date = today

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

if "selected_day" not in st.session_state:
    st.session_state.selected_day = None

def handle_day_click(day_iso: str):
    if st.session_state.selected_day == day_iso:
        st.session_state.selected_day = None 
    else:
        st.session_state.selected_day = day_iso

# Renderizar dias do mês
for week in month_days:
    cols = st.columns(7, gap="small")
    for i, day in enumerate(week):
        day_iso = day.isoformat()
        day_reminders = get_reminders_for_day(reminders, day)
        
        # Classes CSS
        classes = "day-cell"
        wrapper_classes = "day-cell-wrapper" # Classe base do wrapper
        
        if day.month != month:
            classes += " day-other-month-style"
            
        if day == today:
            classes += " today-style"
        
        if day_iso == st.session_state.selected_day:
            classes += " selected-style" 
        
        # Adiciona classe para MUDAR O CURSOR se houver lembretes
        if day_reminders:
            wrapper_classes += " has-reminders"
        
        # HTML do CONTEÚDO da célula
        content_html = f"<div class='day-number-container'>{day.day}</div>"

        # Títulos dos lembretes (máx 2)
        for r in day_reminders[:2]:
            content_html += f"<div class='reminder-title' style='background-color:{r['color']}'>{r['title']}</div>"
            
        if len(day_reminders) > 2:
            content_html += f"<div class='reminder-title' style='background-color:#ccc; color:#333 !important;'>+{len(day_reminders)-2}</div>"

        # HTML COMPLETO da célula (o wrapper visual)
        full_cell_wrapper_html = f"""
        <div class='{wrapper_classes}'>
            <div class='{classes}'>
                {content_html}
            </div>
        """
        
        with cols[i]:
            # 1. Renderiza o visual da célula com st.markdown.
            st.markdown(full_cell_wrapper_html, unsafe_allow_html=True)
            
            # 2. Renderiza o botão de clique com um rótulo simples (" ").
            # O Streamlit ainda precisa de um "label" (rótulo) simples para criar o botão.
            # REMOVIDO: help=f"Ver detalhes do dia {day.day}"
            if st.button(" ", key=f"btn_{day_iso}"):
                 handle_day_click(day_iso)
            
            # 3. Fecha o wrapper
            st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# Sidebar de detalhes
# ==============================
if st.session_state.selected_day:
    day = datetime.date.fromisoformat(st.session_state.selected_day)
    day_reminders = get_reminders_for_day(reminders, day)
    
    st.sidebar.markdown(f"## 📌 Eventos: {day.strftime('%d/%m/%Y')}")
    
    if day_reminders:
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
         st.sidebar.info("Nenhum evento registrado para esta data.")


# ==============================
# Formulário de Novo Lembrete
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
