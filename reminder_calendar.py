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
    /* Estilos globais e Sidebar (Mantidos) */
    body { font-family: 'Inter', sans-serif; background-color: #f7f9fc; }
    h1, h2, h3 { text-align: center; color: #1f2937; }
    
    section[data-testid="stSidebar"] { background: #2c3e50; color: white; border-right: 1px solid #1a252f; box-shadow: 2px 0 5px rgba(0,0,0,0.15); }
    section[data-testid="stSidebar"] * { color: white; }
    section[data-testid="stSidebar"] div.reminder-card { padding: 10px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); border-left: 5px solid; background-color: #34495e; }
    section[data-testid="stSidebar"] .stButton button { background: #e74c3c !important; color: white !important; border-radius: 5px; padding: 4px 8px; font-size: 11px; line-height: 1; transition: background 0.2s; width: auto !important; }

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
        align-items: center;
        overflow: hidden; /* Importante para a faixa */
    }
    
    .day-other-month-style { opacity: 0.5; background-color: #f7f9fc !important; border-color: #f0f0f0 !important; }

    /* Número do dia - Centralizado no topo */
    .day-number-container {
        font-weight: bold;
        font-size: 14px; 
        color: #1f2937;
        padding: 1px 0; 
        line-height: 1.4;
        text-align: center;
        width: 100%;
        flex-shrink: 0;
        margin-bottom: 2px;
    }
    .day-other-month-style .day-number-container { color: #6b7280; }
    
    .today-style .day-number-container > span {
        color: #4b89dc !important;
        border: 2px solid #4b89dc; 
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    /* --- FAIXA DE SELEÇÃO (NOVO ESTILO) --- */
    .selected-strip {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 25%; /* Altura da faixa */
        padding: 2px 4px;
        color: white;
        font-size: 10px;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        text-shadow: 0 0 1px rgba(0,0,0,0.5);
    }
    .selected-strip-title {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 80%;
        flex-grow: 1;
    }
    .selected-strip-icon {
        font-size: 14px;
        cursor: pointer;
        padding-left: 4px;
        line-height: 1;
    }
    .day-cell-wrapper.selected-style {
        /* Remove a borda vermelha e usa a faixa colorida */
        border: 2px solid #ddd;
        background-color: #f5f5f5 !important;
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        z-index: 5;
    }
    
    /* --- BOTÃO INDIVIDUAL DE TÍTULO (Estilo mantido para não selecionado) --- */
    .day-cell-wrapper div[data-testid="stButton"] { margin: 1px 0 0 0 !important; width: 100%; display: flex; justify-content: center; transition: all 0.2s; min-height: 0; }
    .day-cell-wrapper button.reminder-title-btn {
        font-size: 10px; padding: 1px 4px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 90%; 
        font-weight: 500; color: white !important; text-shadow: 0 0 1px rgba(0,0,0,0.3); border: none !important; cursor: pointer; line-height: 1.4; transition: transform 0.1s; min-height: 20px; height: auto;
    }
    .day-cell-wrapper button.reminder-title-btn:hover { transform: scale(1.05); box-shadow: 0 1px 3px rgba(0,0,0,0.4); }
    .day-cell-wrapper .more-reminders { font-size: 10px; margin-top: 2px; padding: 1px 4px; border-radius: 3px; background-color:#ccc; color:#333; font-weight: 500; text-align: center; width: fit-content; line-height: 1.4; }

    .st-emotion-cache-1n76cwh a{ display: none !important; }
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

# Lógica de clique (acionada pelo botão do título ou pelo ícone '?')
def handle_reminder_click(day_iso: str):
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
        has_reminders = bool(day_reminders)
        
        # Classes CSS
        classes = "day-cell-wrapper"
        if day.month != month: classes += " day-other-month-style"
        if day == today: classes += " today-style"
        
        # AQUI: Se o dia estiver selecionado, usamos a classe SELECTED_STYLE
        if day_iso == st.session_state.selected_day: classes += " selected-style" 
        
        with cols[i]:
            st.markdown(f"<div class='{classes}'>", unsafe_allow_html=True)
            
            # Renderiza o número do dia (centralizado no topo)
            st.markdown(f"<div class='day-number-container'><span>{day.day}</span></div>", unsafe_allow_html=True)

            # Renderiza o TÍTULO como um BOTÃO (máx 1 se selecionado, máx 2 se não)
            
            # 1. Se o dia NÃO estiver selecionado (mostra títulos em formato de botões)
            if day_iso != st.session_state.selected_day:
                for r in day_reminders[:2]:
                    btn_label = f"**{r['title']}**"
                    btn_key = f"title_btn_{r['id']}_{day_iso}"
                    
                    if st.button(btn_label, key=btn_key, use_container_width=True, help=f"Ver detalhes de: {r['title']}"):
                        handle_reminder_click(day_iso)
                    
                    # Aplica a cor de fundo e a classe de estilo via CSS e Script injetado
                    st.markdown(
                        f"""
                        <style>
                        div[data-testid="stButton"] button[data-testid*="{btn_key}"] {{ background-color: {r['color']} !important; }}
                        </style>
                        <script>
                        setTimeout(() => {{
                            const btn = window.document.querySelector('button[data-testid*="{btn_key}"]');
                            if(btn) {{ btn.classList.add('reminder-title-btn'); }}
                        }}, 10);
                        </script>
                        """, unsafe_allow_html=True
                    )
                    
                # Renderiza o contador de mais eventos
                if len(day_reminders) > 2:
                    st.markdown(
                        f"""
                        <div style='display: flex; justify-content: center;'>
                            <div class='more-reminders'> +{len(day_reminders)-2} </div>
                        </div>
                        """, unsafe_allow_html=True
                    )
            
            # 2. Se o dia ESTIVER selecionado (mostra apenas a faixa colorida)
            else:
                if day_reminders:
                    # Usa o primeiro lembrete para a cor e o título na faixa
                    first_reminder = day_reminders[0]
                    strip_color = first_reminder['color']
                    strip_title = first_reminder['title']
                    if len(day_reminders) > 1:
                        strip_title += f" (+{len(day_reminders)-1})"
                    
                    # Injeta a faixa colorida e o ícone '?'
                    st.markdown(
                        f"""
                        <div class="selected-strip" style="background-color: {strip_color};">
                            <span class="selected-strip-title">{strip_title}</span>
                            <span class="selected-strip-icon">?</span>
                        </div>
                        """, unsafe_allow_html=True
                    )
                    
                    # Adiciona um botão invisível para o ícone '?' para re-clicar no dia
                    # Isso garante que a lógica de deselecionar funcione ao clicar no '?'
                    btn_key_strip = f"strip_btn_{day_iso}"
                    if st.button(" ", key=btn_key_strip):
                        handle_reminder_click(day_iso)
                    
                    # CSS para esconder o botão, mas manter o clique (similar ao antigo botão de célula inteira, mas só agora)
                    st.markdown(
                        f"""
                        <style>
                        div[data-testid="stButton"] button[data-testid*="{btn_key_strip}"] {{
                            position: absolute;
                            bottom: 0; 
                            right: 0;
                            width: 25px; /* Tamanho do ícone */
                            height: 25px; /* Altura da faixa */
                            background: transparent !important;
                            border: none;
                            z-index: 10;
                            cursor: pointer;
                        }}
                        </style>
                        """, unsafe_allow_html=True
                    )
                    
            # Fechamento do div .day-cell-wrapper
            st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# Sidebar de detalhes (Mantida)
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
