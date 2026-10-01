import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CRM do Ale", page_icon="📊", layout="wide")

# ---------- LOGIN ----------
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 CRM do Ale")
    senha = st.text_input("Digite sua senha", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["APP_PASSWORD"]:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# ---------- CONEXÃO GOOGLE SHEETS ----------
@st.cache_resource
def get_planilha():
    credenciais = Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    cliente = gspread.authorize(credenciais)
    return cliente.open("CRM_Ale")

planilha = get_planilha()

def tela_aba(aba, titulo):
    st.header(titulo)
    valores = aba.get_all_values()
    if not valores:
        st.info("Aba vazia. Adicione cabeçalhos na primeira linha da planilha.")
        return
    cabecalhos = valores[0]
    linhas = valores[1:]

    with st.form("form_" + aba.title, clear_on_submit=True):
        st.subheader("Novo registro")
        campos = {}
        colunas_form = st.columns(min(len(cabecalhos), 3))
        for i, cab in enumerate(cabecalhos):
            with colunas_form[i % len(colunas_form)]:
                campos[cab] = st.text_input(cab)
        if st.form_submit_button("Salvar"):
            if any(v.strip() for v in campos.values()):
                aba.append_row([campos[c] for c in cabecalhos])
                st.success("Salvo com sucesso!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Preencha pelo menos um campo.")

    st.subheader("Registros cadastrados")
    if linhas:
        df = pd.DataFrame(linhas, columns=cabecalhos)
        for _, linha in df.iterrows():
            partes = []
            for cab in cabecalhos:
                valor = str(linha[cab])
                if not valor:
                    continue
                if any(p in cab.lower() for p in ["whatsapp", "zap", "telefone", "celular"]):
                    numero = "".join(ch for ch in valor if ch.isdigit())
                    if numero:
                        valor = f"[{valor}](https://wa.me/55{numero})"
                partes.append(f"**{cab}:** {valor}")
            st.markdown(" • ".join(partes))
            st.divider()
    else:
        st.info("Nenhum registro ainda.")

# ---------- ABAS ----------
aba1, aba2 = st.tabs(["📞 Contatos", "✅ Tarefas"])
with aba1:
    tela_aba(planilha.worksheet("Contatos"), "Contatos")
with aba2:
    tela_aba(planilha.worksheet("Tarefas"), "Tarefas")
