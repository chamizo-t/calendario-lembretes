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
# Conexão com Google Sheets via ID
# ==============================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# Cole o ID da sua planilha aqui
SPREADSHEET_ID = "1ZZG2JJCQ4-N7Jd34hG2GUWMTPDYcVlGfL6ODTi6GYmM"

try:
    sh = client.open_by_key(SPREADSHEET_ID)
    sheet = sh.sheet1  # pega a primeira aba da planilha
except Exception as e:
    st.error("⚠️ Não foi possível abrir a planilha pelo ID. Verifique se foi compartilhada corretamente com o service account.")
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
            date_obj = datetime.date.fromisoformat(r["date"])
        except Exception:
            continue
        if date_obj < today - datetime.timedelta(days=10):
            delete_reminder(r["id"])
            continue
        reminders.append(r)
    return reminders

def add_reminder(title, description, date_obj, created_by, color):
    """Adiciona novo lembrete"""
    new_id = str(datetime.datetime.now().timestamp())
    sheet.append_row([new_id, title, description, date_obj.isoformat(), created_by, color])

def delete_reminder(reminder_id):
    """Deleta lembrete pelo ID"""
    all_values = sheet.get_all_values()
    for idx, row in enumerate(all_values, start=1):
        # row[0] é a coluna ID
        if len(row) > 0 and row[0] == reminder_id:
            sheet.delete_rows(idx)
            break

def get_reminders_for_day(reminders, day):
    """Filtra lembretes de um dia específico"""
    return [r for r in reminders if r["date"] == day.isoformat()]

# ==============================
# Interface
# ==============================
st.title("📆 Calendário de Lembretes")

# Usuário e cor
user = st.text_input("Seu nome:", "Anônimo")
color = st.color_picker("Escolha sua cor para marcar os dias:", "#FF0000")

# Adicionar lembrete
with st.form("new_reminder", clear_on_submit=True):
    title = st.text_input("Título")
    description = st.text_area("Descrição")
    date_input = st.date_input("Data", min_value=datetime.date.today())
    submitted = st.form_submit_button("➕ Adicionar")
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
            if day.month != month:
                st.markdown(f"<div style='opacity:0.3'>{day.day}</div>", unsafe_allow_html=True)
            else:
                # se há lembretes naquele dia
                day_reminders = get_reminders_for_day(reminders, day)
                if day_reminders:
                    # usar a cor do primeiro lembrete desse dia
                    bg = day_reminders[0]["color"]
                    style = f"background:{bg}; padding:4px; border-radius:6px; text-align:center;"
                    if day == today:
                        style += " border:2px solid #000;"  # destaque extra para hoje
                    st.markdown(f"<div style='{style}'><b>{day.day}</b></div>", unsafe_allow_html=True)

                    # Ao clicar no dia
                    if st.button(f"Ver {day}", key=f"btn-{day}"):
                        st.sidebar.header(f"Lembretes de {day}")
                        for r in day_reminders:
                            st.sidebar.markdown(f"**{r['title']}** — {r['description']} _(por {r['created_by']})_")
                else:
                    # dia sem lembrete
                    style = ""
                    if day == today:
                        style = "background:#ffd966; padding:4px; border-radius:6px; text-align:center;"
                        st.markdown(f"<div style='{style}'><b>{day.day}</b></div>", unsafe_allow_html=True)
                    else:
                        st.write(day.day)
