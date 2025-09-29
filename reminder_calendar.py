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
# Estilos customizados (Aprimorados)
# ==============================
st.markdown(
    """
    <style>
    /* Estilos globais para a aplicação */
    body {
        font-family: 'Inter', sans-serif;
        background-color: #f7f9fc;
    }

    h1, h2, h3 {
        text-align: center;
        font-family: 'Inter', sans-serif;
        color: #1f2937;
    }

    /* Título principal */
    .st-emotion-cache-10trblm {
        color: #4b89dc !important; /* Cor principal da paleta */
    }

    /* Células quadradas com grade */
    .day-cell {
        border: 1px solid #e5e7eb;
        border-radius: 8px; /* Mais arredondado */
        width: 100%; /* Ocupa a coluna */
        aspect-ratio: 1 / 1; /* Força o formato quadrado */
        text-align: center;
        transition: all 0.3s ease;
        font-size: 12px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        margin: 0 auto;
        padding: 4px;
        cursor: pointer;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); /* Sombra suave */
    }
    .day-cell:hover {
        background: #f0f4f8 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Botões do Streamlit (para cliques nas células) */
    .stButton>button {
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
        background: none;
        border: none;
        box-shadow: none;
    }

    /* Dia atual */
    .today {
        background-color: #e3f2fd !important; /* Azul claro suave */
        border: 2px solid #4b89dc !important; /* Borda azul */
    }
    
    /* Dia de outro mês */
    .day-other-month {
        opacity: 0.6;
    }

    /* Número do dia */
    .day-number {
        font-weight: bold;
        font-size: 14px; /* Aumentar o número */
        margin-bottom: 4px;
        color: #1f2937;
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
        color: white !important; /* Forçar texto branco */
        text-shadow: 0 0 1px rgba(0,0,0,0.3);
    }
    
    /* Sidebar aprimorada */
    section[data-testid="stSidebar"] {
        background: #ffffff; /* Fundo claro para a sidebar */
        color: #1f2937;
        border-right: 1px solid #e5e7eb;
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #4b89dc;
    }

    /* Card de lembrete na Sidebar */
    section[data-testid="stSidebar"] div.reminder-card {
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 8px;
        font-size: 13px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid; /* Usado para cor */
    }
    
    .st-emotion-cache-1n76cwh a{
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# Conexão Google Sheets
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
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.stop()

sheet = get_gspread_client()

# ==============================
# Funções (Com otimização de cache)
# ==============================
@st.cache_data(ttl=60) # Cache por 60 segundos
def load_reminders() -> List[Dict[str, Any]]:
    """Carrega lembretes e exclui os muito antigos."""
    rows = sheet.get_all_records()
    reminders = []
    today = datetime.date.today()
    
    # Prepara uma lista de IDs para exclusão
    ids_to_delete = []

    for r in rows:
        # Garante que todos os campos necessários estão presentes
        required_keys = ["id","title","description","date","created_by","color"]
        if not all(k in r for k in required_keys):
            continue
        
        try:
            date_obj = datetime.date.fromisoformat(r["date"])
        except ValueError:
            continue
            
        # Exclui lembretes com mais de 10 dias no passado
        if date_obj < today - datetime.timedelta(days=10):
            ids_to_delete.append(r["id"])
            continue
            
        reminders.append(r)

    # Exclui em lote (se suportado pelo gspread, ou um por um)
    # Por simplicidade, vamos usar a função existente (que não é ideal, mas funciona)
    # Em um app de produção, uma solução de exclusão em lote seria melhor.
    for reminder_id in ids_to_delete:
        delete_reminder(reminder_id, force_update=False) # Não força update do cache aqui

    return reminders

def add_reminder(title, description, date_obj, created_by, color):
    """Adiciona um novo lembrete ao Sheet e limpa o cache."""
    new_id = str(datetime.datetime.now().timestamp())
    sheet.append_row([new_id, title, description, date_obj.isoformat(), created_by, color])
    load_reminders.clear() # Limpa o cache para recarregar
    
def delete_reminder(reminder_id, force_update: bool = True):
    """Exclui um lembrete pelo ID e limpa o cache."""
    all_values = sheet.get_all_values()
    # A primeira linha (cabeçalho) tem índice 1 no gspread
    for idx, row in enumerate(all_values, start=1):
        if len(row) > 0 and row[0] == reminder_id:
            sheet.delete_rows(idx)
            if force_update:
                load_reminders.clear()
            break

def get_reminders_for_day(reminders: List[Dict], day: datetime.date) -> List[Dict[str, Any]]:
    """Filtra lembretes para um dia específico."""
    return [r for r in reminders if r["date"] == day.isoformat()]

# ==============================
# Interface Principal
# ==============================

st.title("🗓️ **Calendário de Eventos**")

reminders = load_reminders()

today = datetime.date.today()

# Estado para navegação do calendário
if "calendar_view_date" not in st.session_state:
    st.session_state.calendar_view_date = today

year, month = st.session_state.calendar_view_date.year, st.session_state.calendar_view_date.month
cal = calendar.Calendar(firstweekday=0) # 0 = Segunda-feira
month_days = cal.monthdatescalendar(year, month)

# Controles de navegação
col_prev, col_month, col_next = st.columns([1, 4, 1])

def navigate_month(delta: int):
    """Função para mudar o mês e limpar a seleção de dia."""
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
    st.session_state.selected_day = None # Limpa a seleção ao mudar o mês
    
col_prev.button("◀️ Anterior", on_click=navigate_month, args=(-1,))
col_next.button("Próximo ▶️", on_click=navigate_month, args=(1,))

# Título do mês
month_name_pt = calendar.month_name[month].capitalize()
col_month.subheader(f"{month_name_pt} {year}")

st.markdown("---")

# Cabeçalho dos dias da semana
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
week_cols = st.columns(7, gap="small")
for i, wd in enumerate(weekdays):
    week_cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #4b89dc;'>{wd}</div>", unsafe_allow_html=True)

# Estado para dia clicado
if "selected_day" not in st.session_state:
    st.session_state.selected_day = None

# Função de callback para clique no dia
def handle_day_click(day_iso: str):
    """Define o dia selecionado e abre/fecha a sidebar."""
    if st.session_state.selected_day == day_iso:
        st.session_state.selected_day = None # Desseleciona se já estiver selecionado
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
        cell_style = ""
        
        if day.month != month:
            classes += " day-other-month"
            
        if day == today:
            classes += " today"
        
        if day_iso == st.session_state.selected_day:
            cell_style = "border: 2px solid #ff4b4b; background-color: #ffe0e0;" # Estilo de seleção
        
        # HTML do dia
        html = f"<div class='{classes}' style='{cell_style}'>"
        html += f"<div class='day-number'>{day.day}</div>"

        # Títulos dos lembretes (máx 2)
        for r in day_reminders[:2]:
            html += f"<div class='reminder-title' style='background-color:{r['color']}'>{r['title']}</div>"
            
        if len(day_reminders) > 2:
            html += f"<div class='reminder-title' style='background-color:#ccc; color:#333 !important;'>+{len(day_reminders)-2}</div>"

        html += "</div>"
        
        # Renderiza o container com o HTML, usando um botão transparente para clique
        with cols[i]:
            # st.button é usado para capturar o clique
            if st.button(html, key=f"btn_{day_iso}", help=f"Ver detalhes de {day}", unsafe_allow_html=True):
                 handle_day_click(day_iso)


# ==============================
# Sidebar de detalhes (Aprimorada)
# ==============================
if st.session_state.selected_day:
    day = datetime.date.fromisoformat(st.session_state.selected_day)
    day_reminders = get_reminders_for_day(reminders, day)
    
    st.sidebar.markdown(f"## 📌 Detalhes: {day.strftime('%d/%m/%Y')}")
    
    if day_reminders:
        for r in day_reminders:
            # Usa o border-left para mostrar a cor do evento
            card_style = f"border-color: {r['color']};"
            st.sidebar.markdown(
                f"""
                <div class="reminder-card" style="{card_style}">
                    <b>{r['title']}</b>
                    <p style='margin: 4px 0 6px 0;'><small>{r['description'] or 'Sem descrição'}</small></p>
                    <hr style='margin: 4px 0; border-top: 1px solid #eee;'>
                    <small>Criado por: <i>{r['created_by']}</i></small>
                    <div style='text-align: right; margin-top: 5px;'>
                        <a href="#" onclick="window.parent.postMessage('streamlit:delete_reminder:{r['id']}', '*')" title="Excluir" style="color: #ff4b4b; text-decoration: none;">🗑️</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Adiciona um placeholder para o botão de exclusão
            # **NOTA:** Streamlit não permite botões na sidebar que alteram o estado sem truques.
            # O link acima é um "placeholder" visual. Para a exclusão funcionar, precisaria de:
            # 1. Um formulário (st.form) ou uma forma de recarregar a página/estado.
            # 2. Um botão real com a lógica `delete_reminder(r["id"])`.
            # Exemplo de botão funcional (mas que não se encaixa bem no visual do card):
            # if st.sidebar.button("Excluir", key=f"del_{r['id']}"):
            #     delete_reminder(r["id"])
            #     st.rerun() # Força a atualização após a exclusão
            
            # Vamos usar o botão real com um design compacto
            delete_col, _ = st.sidebar.columns([1, 4])
            if delete_col.button("🗑️", key=f"del_{r['id']}", help="Excluir Lembrete"):
                 delete_reminder(r["id"])
                 st.rerun() # Necessário para recarregar o estado após a mudança
    else:
         st.sidebar.info("Nenhum evento registrado para esta data.")


# ==============================
# Formulário de Novo Lembrete
# ==============================
st.markdown("---")
st.subheader("➕ Adicionar Novo Evento")

# Usa um container para o formulário para melhor organização
with st.container(border=True):
    col_user, col_color = st.columns([2, 1])
    
    user = col_user.text_input("👤 **Seu Nome**", "Anônimo")
    color = col_color.color_picker("🎨 **Cor do Evento**", "#4b89dc") # Cor padrão mais profissional

    with st.form("new_reminder", clear_on_submit=True):
        title = st.text_input("📝 **Título do Evento**", max_chars=50)
        description = st.text_area("🗒️ **Descrição**")
        
        # Define a data inicial para o dia selecionado, se houver
        default_date = datetime.date.today()
        if st.session_state.selected_day:
            default_date = datetime.date.fromisoformat(st.session_state.selected_day)
            
        date_input = st.date_input("🗓️ **Data**", 
                                   value=default_date, 
                                   min_value=datetime.date.today())
                                   
        submitted = st.form_submit_button("✅ **Salvar Evento**")
        
        if submitted:
            if not title:
                st.error("O **Título** é obrigatório!")
            else:
                add_reminder(title, description, date_input, user, color)
                st.success("🎉 Evento adicionado com sucesso! Recarregando...")
                st.rerun() # Força a atualização para mostrar o novo lembrete no calendário
