import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Meu CRM", page_icon="🎯", layout="wide")

# ==================== SENHA ====================
if not st.session_state.get("logado"):
    st.title("🎯 Meu CRM")
    senha = st.text_input("Digite sua senha", type="password")
    if st.button("Entrar"):
        if senha and senha == st.secrets.get("APP_PASSWORD"):
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# ==================== CONEXÃO COM O GOOGLE ====================
conn = st.connection("gsheets", type=GSheetsConnection)

ETAPAS = ["Lead", "Contato feito", "Proposta enviada", "Negociação", "Fechado"]
COL_CONTATOS = ["Nome", "Empresa", "Nicho", "Telefone", "Mensagem", "Etapa", "Atualizado em"]
COL_TAREFAS = ["Tarefa", "Data", "Concluída"]

def ler_aba(nome, colunas):
    try:
        df = conn.read(worksheet=nome)
    except Exception:
        st.error(f"Não encontrei a aba '{nome}' na planilha. Crie essa aba no Google Sheets e recarregue.")
        st.stop()
    if df.empty:
        return pd.DataFrame(columns=colunas)
    for c in colunas:
        if c not in df.columns:
            df[c] = ""
    return df[colunas]

def salvar_aba(nome, df):
    conn.update(worksheet=nome, data=df)

# ==================== VISUAL ====================
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1B2A4A; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 1px 4px rgba(20, 30, 60, 0.08);
    }
    div[data-testid="stMetricValue"] { font-weight: 700; color: #1F2430; }
</style>
""", unsafe_allow_html=True)

# ==================== PIPELINE (KANBAN) ====================
def pagina_kanban():
    st.header("Pipeline de vendas")
    df = ler_aba("Contatos", COL_CONTATOS)
    cols = st.columns(len(ETAPAS), gap="small")
    for i, etapa in enumerate(ETAPAS):
        with cols[i]:
            st.markdown(f"### {etapa}")
            cartoes = df[df["Etapa"] == etapa]
            if cartoes.empty:
                st.caption("Vazio")
            for idx, linha in cartoes.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{linha['Nome']}**")
                    if str(linha["Empresa"]).strip():
                        st.caption(linha["Empresa"])
                    if str(linha["Nicho"]).strip():
                        st.caption(f"🎯 {linha['Nicho']}")
                    if str(linha["Mensagem"]).strip():
                        st.caption(linha["Mensagem"])
                    tel = "".join(ch for ch in str(linha["Telefone"]) if ch.isdigit())
                    if tel:
                        if not tel.startswith("55"):
                            tel = "55" + tel
                        st.link_button("💬 WhatsApp", f"https://wa.me/{tel}", use_container_width=True)
                    c1, c2 = st.columns(2)
                    mover = None
                    if c1.button("◀", key=f"esq_{idx}", disabled=(i == 0), use_container_width=True):
                        mover = i - 1
                    if c2.button("▶", key=f"dir_{idx}", disabled=(i == len(ETAPAS) - 1), use_container_width=True):
                        mover = i + 1
                    if mover is not None:
                        df.loc[idx, "Etapa"] = ETAPAS[mover]
                        df.loc[idx, "Atualizado em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        salvar_aba("Contatos", df)
                        st.rerun()

# ==================== CONTATOS ====================
def pagina_contatos():
    st.header("Contatos")
    df = ler_aba("Contatos", COL_CONTATOS)

    with st.form("novo_contato", border=True):
        nome = st.text_input("Nome *")
        empresa = st.text_input("Empresa")
        nicho = st.text_input("Nicho (ex: supermercado, gráfica, clínica...)")
        telefone = st.text_input("WhatsApp (só números, com DDD)")
        mensagem = st.text_area("Mensagem / observações")
        etapa = st.selectbox("Etapa inicial", ETAPAS)
        if st.form_submit_button("Salvar contato", type="primary"):
            if not nome.strip():
                st.error("O nome é obrigatório.")
            else:
                novo = pd.DataFrame([{
                    "Nome": nome.strip(), "Empresa": empresa.strip(), "Nicho": nicho.strip(),
                    "Telefone": telefone.strip(), "Mensagem": mensagem.strip(), "Etapa": etapa,
                    "Atualizado em": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }])
                salvar_aba("Contatos", pd.concat([df, novo], ignore_index=True))
                st.rerun()

    st.subheader("Todos os contatos")
    if not df.empty:
        st.dataframe(df[["Nome", "Empresa", "Nicho", "Telefone", "Etapa"]],
                     use_container_width=True, hide_index=True)
        alvo = st.selectbox("Excluir contato", df["Nome"].tolist())
        if st.button("🗑️ Excluir selecionado"):
            df = df[df["Nome"] != alvo]
            salvar_aba("Contatos", df)
            st.rerun()

# ==================== AGENDA ====================
def pagina_tarefas():
    st.header("Agenda e tarefas")
    df = ler_aba("Tarefas", COL_TAREFAS)

    with st.form("nova_tarefa", border=True):
        tarefa = st.text_input("O que precisa fazer?")
        data = st.date_input("Data", value=date.today())
        if st.form_submit_button("Salvar tarefa", type="primary"):
            if tarefa.strip():
                novo = pd.DataFrame([{
                    "Tarefa": tarefa.strip(),
                    "Data": data.strftime("%d/%m/%Y"),
                    "Concluída": "Não",
                }])
                salvar_aba("Tarefas", pd.concat([df, novo], ignore_index=True))
                st.rerun()

    hoje = date.today().strftime("%d/%m/%Y")
    pendentes = df[df["Concluída"] != "Sim"]
    de_hoje = pendentes[pendentes["Data"] == hoje]
    if not de_hoje.empty:
        st.subheader("📌 Para hoje")
        for idx, linha in de_hoje.iterrows():
            c1, c2 = st.columns([6, 1])
            c1.markdown(f"**{linha['Tarefa']}**")
            if c2.button("✅", key=f"ok_{idx}"):
                df.loc[idx, "Concluída"] = "Sim"
                salvar_aba("Tarefas", df)
                st.rerun()

    st.subheader("Todas as tarefas")
    if not df.empty:
        for idx, linha in df.sort_values("Data").iterrows():
            c1, c2, c3 = st.columns([6, 2, 1])
            texto = linha["Tarefa"]
            if linha["Concluída"] == "Sim":
                texto = f"~~{texto}~~"
            c1.markdown(texto)
            c2.caption(linha["Data"])
            if c3.button("🗑️", key=f"del_{idx}"):
                df = df.drop(idx)
                salvar_aba("Tarefas", df)
                st.rerun()

# ==================== NAVEGAÇÃO ====================
st.sidebar.title("🎯 Meu CRM")
menu = st.sidebar.radio("Navegação", ["Pipeline", "Contatos", "Agenda"])
if menu == "Pipeline":
    pagina_kanban()
elif menu == "Contatos":
    pagina_contatos()
else:
    pagina_tarefas()
