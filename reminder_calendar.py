# reminder_calendar.py
# Requer: pip install streamlit
# Rodar: streamlit run reminder_calendar.py

import sqlite3
from datetime import date, datetime
import calendar
import streamlit as st

DB = "reminders.db"

# --- DB helpers ---


def init_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_by TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


conn = init_db()


def add_reminder(title, description, date_str, created_by):
    c = conn.cursor()
    c.execute(
        "INSERT INTO reminders (title, description, date, created_by, created_at) VALUES (?,?,?,?,?)",
        (title, description, date_str, created_by, datetime.utcnow().isoformat())
    )
    conn.commit()


def get_reminders_between(start_date, end_date):
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, created_by FROM reminders WHERE date BETWEEN ? AND ? ORDER BY date",
              (start_date.isoformat(), end_date.isoformat()))
    rows = c.fetchall()
    return rows


def get_all_reminders():
    c = conn.cursor()
    c.execute(
        "SELECT id, title, description, date, created_by FROM reminders ORDER BY date")
    return c.fetchall()


# --- UI ---
st.set_page_config(page_title="Calendário de Lembretes", layout="wide")
st.title("📆 Calendário de Lembretes — compartilhável")

# Sidebar: criar lembrete
st.sidebar.header("Adicionar lembrete")
with st.sidebar.form("form_add"):
    title = st.text_input("Título", max_chars=100)
    description = st.text_area("Descrição (opcional)", height=80)
    d = st.date_input("Data do lembrete", value=date.today())
    created_by = st.text_input(
        "Seu nome (aparecerá nos lembretes)", value="Anônimo")
    submitted = st.form_submit_button("Salvar lembrete")
    if submitted:
        if not title.strip():
            st.sidebar.error("Por favor, informe um título.")
        else:
            add_reminder(title.strip(), description.strip(),
                         d.isoformat(), created_by.strip() or "Anônimo")
            st.sidebar.success(f"Lembrete salvo para {d.isoformat()}")

# Controle de visualização
st.sidebar.markdown("---")
view_month = st.sidebar.date_input(
    "Mês para visualizar", value=date.today().replace(day=1))
show_own_only = st.sidebar.checkbox(
    "Mostrar só meus lembretes (filtrar por nome)", value=False)
filter_name = ""
if show_own_only:
    filter_name = st.sidebar.text_input("Nome para filtrar", value="Anônimo")

# Build month calendar
year = view_month.year
month = view_month.month
# segunda=0? (0=segunda?) -> python: 0=Monday
cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(year, month)

st.subheader(f"{calendar.month_name[month]} {year}")

# Gather reminders for month
first_day = date(year, month, 1)
last_day = month_days[-1][-1]
rows = get_reminders_between(first_day, last_day)

# Convert rows to dict by date
rem_by_date = {}
for r in rows:
    rid, title_r, desc_r, date_r, created_by_r = r
    dobj = datetime.fromisoformat(date_r).date() if isinstance(
        date_r, str) else date.fromisoformat(date_r)
    if show_own_only and filter_name.strip():
        if (created_by_r or "").lower().strip() != filter_name.lower().strip():
            continue
    rem_by_date.setdefault(dobj, []).append(
        {"id": rid, "title": title_r, "desc": desc_r, "by": created_by_r})

# Render calendar as table
cols = st.columns(len(month_days[0]))
# header with weekdays
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
hd = st.columns(7)
for i, wd in enumerate(weekdays):
    hd[i].markdown(f"**{wd}**")

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            # shade days not in current month
            if day.month != month:
                st.markdown(
                    f"<div style='opacity:0.25'>{day.day}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{day.day}**")
            # show reminders
            if day in rem_by_date:
                for item in rem_by_date[day]:
                    st.markdown(
                        f"- **{item['title']}**  \n  _por: {item['by']}_  \n  {item['desc'][:120]}{'...' if len(item['desc'] or '')>120 else ''}")

st.markdown("---")
st.subheader("Todos os lembretes")
allr = get_all_reminders()
for r in allr:
    st.write(f"- {r[3]} — **{r[1]}** (por {r[4]})")
    if r[2]:
        st.write(f"  > {r[2]}")

st.info("Dica: para compartilhar com o time, hospede este arquivo (Streamlit Cloud / Heroku / VPS) e envie o link.")
