import sqlite3
from datetime import date, datetime, timedelta
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

def update_reminder(rid, title, description):
    c = conn.cursor()
    c.execute(
        "UPDATE reminders SET title=?, description=? WHERE id=?",
        (title, description, rid)
    )
    conn.commit()

def delete_reminder(rid):
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=?", (rid,))
    conn.commit()

def cleanup_old_reminders():
    """Remove lembretes com mais de 10 dias após a data do evento"""
    cutoff = (date.today() - timedelta(days=10)).isoformat()
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE date < ?", (cutoff,))
    conn.commit()

def get_reminders_between(start_date, end_date):
    c = conn.cursor()
    c.execute(
        "SELECT id, title, description, date, created_by FROM reminders WHERE date BETWEEN ? AND ? ORDER BY date",
        (start_date.isoformat(), end_date.isoformat())
    )
    return c.fetchall()

def get_all_reminders():
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, created_by FROM reminders ORDER BY date")
    return c.fetchall()

# --- UI ---
st.set_page_config(page_title="Calendário de Lembretes", layout="wide")
st.title("📆 Calendário de Lembretes — colaborativo")

# Limpeza automática
cleanup_old_reminders()

# Sidebar: criar lembrete
st.sidebar.header("➕ Adicionar lembrete")
with st.sidebar.form("form_add"):
    title = st.text_input("Título", max_chars=100)
    description = st.text_area("Descrição (opcional)", height=80)
    d = st.date_input("Data do lembrete", value=date.today())
    created_by = st.text_input("Seu nome", value="Anônimo")
    submitted = st.form_submit_button("Salvar")
    if submitted:
        if not title.strip():
            st.sidebar.error("Por favor, informe um título.")
        else:
            add_reminder(title.strip(), description.strip(), d.isoformat(), created_by.strip() or "Anônimo")
            st.sidebar.success(f"Lembrete salvo para {d.isoformat()}")

# Controle de visualização
st.sidebar.markdown("---")
view_month = st.sidebar.date_input("📅 Escolha o mês", value=date.today().replace(day=1))

year = view_month.year
month = view_month.month
cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(year, month)

st.subheader(f"{calendar.month_name[month]} {year}")

# Obter lembretes do mês
first_day = date(year, month, 1)
last_day = month_days[-1][-1]
rows = get_reminders_between(first_day, last_day)

rem_by_date = {}
for rid, title_r, desc_r, date_r, created_by_r in rows:
    dobj = datetime.fromisoformat(date_r).date()
    rem_by_date.setdefault(dobj, []).append({
        "id": rid,
        "title": title_r,
        "desc": desc_r,
        "by": created_by_r
    })

# Renderizar calendário (responsivo)
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
cols = st.columns(7)
for i, wd in enumerate(weekdays):
    cols[i].markdown(f"**{wd}**")

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            style = "background:#ffd966; padding:4px; border-radius:6px;" if day == date.today() else ""
            st.markdown(f"<div style='{style}'><b>{day.day}</b></div>", unsafe_allow_html=True)

            if day in rem_by_date:
                for item in rem_by_date[day]:
                    with st.expander(f"🔔 {item['title']} (por {item['by']})", expanded=False):
                        st.write(item["desc"] if item["desc"] else "_(sem descrição)_")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✏️ Editar", key=f"edit-{item['id']}"):
                                new_title = st.text_input("Novo título", item["title"], key=f"t-{item['id']}")
                                new_desc = st.text_area("Nova descrição", item["desc"], key=f"d-{item['id']}")
                                if st.button("Salvar alterações", key=f"save-{item['id']}"):
                                    update_reminder(item["id"], new_title, new_desc)
                                    st.experimental_rerun()
                        with col2:
                            if st.button("🗑️ Excluir", key=f"del-{item['id']}"):
                                delete_reminder(item["id"])
                                st.experimental_rerun()

# Lista geral
st.markdown("---")
st.subheader("📋 Todos os lembretes")
for r in get_all_reminders():
    st.write(f"- {r[3]} — **{r[1]}** (por {r[4]})")



st.info("Dica: para compartilhar com o time, hospede este arquivo (Streamlit Cloud / Heroku / VPS) e envie o link.")


