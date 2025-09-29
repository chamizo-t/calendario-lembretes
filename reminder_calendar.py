import streamlit as st
import calendar
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# Configurações do App
# ==============================
st.set_page_config(page_title="📆 Calendário de Lembretes", layout="wide")

# ==============================
# Estilos customizados (CSS)
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
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
        font-weight: 500;
    }
    .day-cell:hover {
        transform: scale(1.07);
        box-shadow: 0px 2px 8px rgba(0,0,0,0.2);
    }

    /* Dia atual com opacidade */
    .today {
        background-color: rgba(255, 217, 102, 0.35);
        border: 2px solid #f1c232;
    }

    /* Dias com lembrete */
    .reminder {
        color: #fff;
        font-weight: bold;
    }

    /* Sidebar mais elegante */
    section[data-testid="stSidebar"] {
        background: #fafafa;
        border-left: 2px solid #e6e6e6;
        padding: 1rem;
    }

    /* Botão adicionar */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# Conexão com Google Sheets
# ==============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_ID = "1ZZG2JJCQ4-N7Jd34hG2GUWMTPDYcVlGfL6ODTi6GYmM"

try:
    sh = client.open_by_key(SPREADSHEET_ID)
    sheet = sh.sheet1
except Exception:
    st.error("⚠️ Não foi possível abrir a planilha. Verifique se foi compartilhada com o service account.")
    st.stop()

# ==============================
# Funções auxiliares
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
        except Exception:
            continue
        # Apaga vencidos há mais de 10 dias
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
st.title("📅 Calendário de Lembretes Compartilhado")

# Usuário e cor
user = st.text_input("👤 Seu nome:", "Anônimo")
color = st.color_picker("🎨 Escolha sua cor:", "#FF0000")

# Adicionar lembrete
with st.form("new_reminder", clear_on_submit=True):
    st.subheader("➕ Adicionar novo lembrete")
    title = st.text_input("Título")
    description = st.text_area("Descrição")
    date_input = st.date_input("Data", min_value=datetime.date.today())
    submitted = st.form_submit_button("Adicionar Lembrete")
    if submitted and title:
        add_reminder(title, description, date_input, user, color)
        st.success("✅ Lembrete adicionado!")

# Carregar lembretes
reminders = load_reminders()

# Mostrar calendário
today = datetime.date.today()
year, month = today.year, today.month
cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(year, month)

st.subheader(f"{calendar.month_name[month]} {year}")
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
cols = st.columns(7)
for i, wd in enumerate(weekdays):
    cols[i].markdown(f"**{wd}**")

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            day_reminders = get_reminders_for_day(reminders, day)
            classes = "day-cell"
            
            # Dia atual
            if day == today:
                classes += " today"
            
            # Se houver lembrete
            if day_reminders:
                bg = day_reminders[0]["color"]
                html = f"<div class='{classes}' style='background:{bg};opacity:0.85'>{day.day}</div>"
            else:
                html = f"<div class='{classes}'>{day.day}</div>"

            st.markdown(html, unsafe_allow_html=True)
            
            if day_reminders and st.button(f"Ver {day}", key=f"btn-{day}"):
                st.sidebar.header(f"📌 Lembretes de {day}")
                for r in day_reminders:
                    st.sidebar.markdown(
                        f"**{r.get('title','')}**  \n"
                        f"📝 {r.get('description','')}  \n"
                        f"👤 {r.get('created_by','')}"
                    )
