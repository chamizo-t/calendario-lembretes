import streamlit as st
import calendar
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# Configurações do App
# ==============================
st.set_page_config(page_title="Calendário de Lembretes", layout="wide")

# ==============================
# Conexão com Google Sheets
# ==============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_NAME = "Reminders"
try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception:
    st.error(f"⚠️ Não achei a planilha chamada **{SHEET_NAME}**. Crie ela no Google Sheets e compartilhe com o service account.")
    st.stop()

# ==============================
# Funções auxiliares
# ==============================
def load_reminders():
    """Carrega lembretes da planilha e remove os vencidos há mais de 10 dias"""
    rows = sheet.get_all_records()
    reminders = []
    today = datetime.date.today()
    for r in rows:
        try:
            date = datetime.date.fromisoformat(r["date"])
            if date < today - datetime.timedelta(days=10):
                # Apaga lembretes muito antigos
                delete_reminder(r["id"])
                continue
            reminders.append(r)
        except Exception:
            continue
    return reminders

def add_reminder(title, description, date, created_by, color):
    """Adiciona novo lembrete"""
    new_id = str(datetime.datetime.now().timestamp())
    sheet.append_row([new_id, title, description, date.isoformat(), created_by, color])

def delete_reminder(reminder_id):
    """Deleta lembrete pelo ID"""
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if row and row[0] == reminder_id:
            sheet.delete_rows(i + 1)
            break

def get_reminders_for_day(reminders, day):
    """Filtra lembretes de um dia específico"""
    return [r for r in reminders if r["date"] == day.isoformat()]

# ==============================
# Interface
# ==============================
st.title("📆 Calendário de Lembretes")

# Usuário
user = st.text_input("Seu nome:", "Anônimo")
color = st.color_picker("Escolha sua cor para marcar os dias:", "#FF0000")

# Adicionar lembrete
with st.form("new_reminder", clear_on_submit=True):
    title = st.text_input("Título")
    description = st.text_area("Descrição")
    date = st.date_input("Data", min_value=datetime.date.today())
    submitted = st.form_submit_button("➕ Adicionar")
    if submitted and title:
        add_reminder(title, description, date, user, color)
        st.success("✅ Lembrete adicionado!")

# Carregar lembretes
reminders = load_reminders()

# Mostrar calendário
today = datetime.date.today()
year, month = today.year, today.month
cal = calendar.Calendar(firstweekday=0)
month_days = cal.itermonthdates(year, month)

st.subheader(f"{calendar.month_name[month]} {year}")
cols = st.columns(7)
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Cabeçalho
for i, wd in enumerate(weekdays):
    cols[i].markdown(f"**{wd}**")

# Dias
for week in calendar.monthcalendar(year, month):
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
            continue
        date = datetime.date(year, month, day)
        day_reminders = get_reminders_for_day(reminders, date)
        
        if day_reminders:
            # Escolhe cor do primeiro lembrete do dia (poderia ser várias cores em stack)
            bg_color = day_reminders[0]["color"]
            btn_label = f"📌 {day}"
            if cols[i].button(btn_label, key=f"{date}"):
                st.sidebar.subheader(f"Lembretes em {date}")
                for r in day_reminders:
                    st.sidebar.write(f"**{r['title']}** - {r['description']} (por {r['created_by']})")
        else:
            cols[i].write(str(day))

