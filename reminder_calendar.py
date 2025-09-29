import streamlit as st
import calendar
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# Configurações
# ==============================
st.set_page_config(page_title="📆 Calendário de Lembretes", layout="wide")

# ==============================
# Estilos customizados
# ==============================
st.markdown(
    """
    <style>
    h1, h2, h3 {
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Dias do calendário */
    .day-cell {
        border-radius: 8px;
        padding: 6px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
        font-weight: 500;
        min-height: 70px;
        max-height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        font-size: 13px;
    }
    .day-cell:hover {
        transform: scale(1.03);
        box-shadow: 0px 2px 6px rgba(0,0,0,0.2);
    }

    /* Dia atual */
    .today {
        background-color: rgba(255, 217, 102, 0.25);
        border: 2px solid #f1c232;
    }

    /* Título do lembrete dentro do quadrado */
    .reminder-title {
        margin-top: 2px;
        font-size: 11px;
        font-weight: 600;
        padding: 1px 3px;
        border-radius: 5px;
        color: white;
        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;
        max-width: 95%;
        cursor: pointer;
    }

    /* Sidebar moderna */
    section[data-testid="stSidebar"] {
        background: #2c3e50;
        color: white;
        border-left: 2px solid #1a252f;
        padding: 1rem;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# Conexão Google Sheets
# ==============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_ID = "1ZZG2JJCQ4-N7Jd34hG2GUWMTPDYcVlGfL6ODTi6GYmM"
sh = client.open_by_key(SPREADSHEET_ID)
sheet = sh.sheet1

# ==============================
# Funções
# ==============================
def load_reminders():
    rows = sheet.get_all_records()
    reminders = []
    today = datetime.date.today()
    for r in rows:
        if not all(k in r for k in ["id","title","description","date","created_by","color"]):
            continue
        try:
            date_obj = datetime.date.fromisoformat(r["date"])
        except:
            continue
        if date_obj < today - datetime.timedelta(days=10):
            delete_reminder(r["id"])
            continue
        reminders.append(r)
    return reminders

def add_reminder(title, description, date_obj, created_by, color):
    new_id = str(datetime.datetime.now().timestamp())
    sheet.append_row([new_id, title, description, date_obj.isoformat(), created_by, color])

def delete_reminder(reminder_id):
    all_values = sheet.get_all_values()
    for idx, row in enumerate(all_values, start=1):
        if len(row) > 0 and row[0] == reminder_id:
            sheet.delete_rows(idx)
            break

def get_reminders_for_day(reminders, day):
    return [r for r in reminders if r["date"] == day.isoformat()]

# ==============================
# Interface
# ==============================
st.title("📅 Calendário de Lembretes")

reminders = load_reminders()

today = datetime.date.today()
year, month = today.year, today.month
cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(year, month)

st.subheader(f"{calendar.month_name[month]} {year}")
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
cols = st.columns(7)
for i, wd in enumerate(weekdays):
    cols[i].markdown(f"**{wd}**")

# Estado para dia clicado
if "selected_day" not in st.session_state:
    st.session_state.selected_day = None

for week in month_days:
    cols = st.columns(7, gap="small")
    for i, day in enumerate(week):
        with cols[i]:
            day_reminders = get_reminders_for_day(reminders, day)
            classes = "day-cell"
            if day == today:
                classes += " today"

            # Renderiza o dia
            st.markdown(f"<div class='{classes}'>{day.day}</div>", unsafe_allow_html=True)

            # Renderiza lembretes como botões clicáveis
            for r in day_reminders[:2]:
                if st.button(r["title"], key=f"{r['id']}_{day}", help="Clique para ver detalhes", use_container_width=True):
                    st.session_state.selected_day = day.isoformat()

            if len(day_reminders) > 2:
                st.caption(f"+{len(day_reminders)-2} mais...")

# ==============================
# Sidebar de detalhes
# ==============================
if st.session_state.selected_day:
    day = datetime.date.fromisoformat(st.session_state.selected_day)
    day_reminders = get_reminders_for_day(reminders, day)
    st.sidebar.title(f"📌 {day.strftime('%d/%m/%Y')}")
    for r in day_reminders:
        st.sidebar.markdown(
            f"""
            <div style="padding:8px;margin-bottom:8px;border-radius:8px;background:{r['color']};color:white;">
                <b>{r['title']}</b><br>
                {r['description']}<br>
                <i>por {r['created_by']}</i>
            </div>
            """,
            unsafe_allow_html=True
        )

# ==============================
# Formulário (vem por último)
# ==============================
st.divider()
user = st.text_input("👤 Seu nome:", "Anônimo")
color = st.color_picker("🎨 Escolha sua cor:", "#FF0000")

with st.form("new_reminder", clear_on_submit=True):
    st.subheader("➕ Adicionar novo lembrete")
    title = st.text_input("Título")
    description = st.text_area("Descrição")
    date_input = st.date_input("Data", min_value=datetime.date.today())
    submitted = st.form_submit_button("Adicionar Lembrete")
    if submitted and title:
        add_reminder(title, description, date_input, user, color)
        st.success("✅ Lembrete adicionado!")
