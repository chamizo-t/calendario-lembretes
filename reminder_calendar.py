import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import date, datetime, timedelta

# =====================
# Configuração inicial
# =====================
st.set_page_config(page_title="📅 Calendário de Lembretes", layout="wide")

# Autenticação Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Abre a planilha "Reminders"
sheet = client.open("Reminders").sheet1

# =====================
# Funções auxiliares
# =====================
def get_reminders():
    data = sheet.get_all_records()
    today = date.today().isoformat()
    return [
        r for r in data
        if r.get("title") and r.get("date") >= today
    ]

def add_reminder(title, description, reminder_date, created_by, color):
    sheet.append_row([title, description, reminder_date, created_by, color])

def group_reminders_by_date(reminders):
    grouped = {}
    for r in reminders:
        grouped.setdefault(r["date"], []).append(r)
    return grouped

# =====================
# Layout principal
# =====================
st.title("📅 Calendário de Lembretes")

# Seleção de mês/ano
col1, col2 = st.columns([1,1])
with col1:
    year = st.selectbox("Ano", list(range(2023, 2031)), index=list(range(2023, 2031)).index(date.today().year))
with col2:
    month = st.selectbox("Mês", list(range(1, 13)), index=date.today().month - 1)

cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(year, month)

reminders = get_reminders()
reminders_by_date = group_reminders_by_date(reminders)

today = date.today()

# =====================
# CSS customizado
# =====================
st.markdown(
    """
    <style>
    .calendar { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
    .day-cell {
        border-radius: 6px;
        width: 50px;
        height: 50px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
        font-size: 11px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        padding: 2px;
        margin: 0 auto;
    }
    .day-today {
        background-color: rgba(200, 0, 0, 0.2);
        border: 1px solid rgba(200, 0, 0, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================
# Renderização do calendário
# =====================
st.subheader(f"{calendar.month_name[month]} {year}")

days_header = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
cols = st.columns(7)
for i, d in enumerate(days_header):
    with cols[i]:
        st.markdown(f"**{d}**")

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            css_class = "day-cell"
            if day == today:
                css_class += " day-today"

            st.markdown(f"<div class='{css_class}'>{day.day}</div>", unsafe_allow_html=True)

            day_reminders = reminders_by_date.get(day.isoformat(), [])
            for r in day_reminders[:2]:
                if st.button(
                    r["title"],
                    key=f"{r['title']}_{day}",
                    use_container_width=True,
                    help="Clique para ver detalhes"
                ):
                    st.session_state.selected_day = day.isoformat()

                # aplicar cor no botão do lembrete
                st.markdown(
                    f"""
                    <style>
                    div[data-testid="stButton"] button[kind="secondary"][key="{r['title']}_{day}"] {{
                        background-color: {r['color']} !important;
                        color: white !important;
                        font-size: 10px;
                        padding: 0px 2px;
                        height: 18px;
                        line-height: 18px;
                        border-radius: 4px;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

# =====================
# Barra lateral com lembretes
# =====================
st.sidebar.title("🔔 Lembretes")
for r in reminders:
    st.sidebar.markdown(f"**{r['title']}** — {r['description']} _(por {r['created_by']})_")
