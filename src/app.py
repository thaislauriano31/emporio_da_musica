import streamlit as st
from agent import LLM
from settings import AppSettings
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(
    page_title="Empório da Música - Atendimento",
    page_icon="🎸",
    layout="centered"
)

if "agent" not in st.session_state:
    st.session_state.agent = LLM(settings=AppSettings())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou o Tom, especialista aqui da **Empório da Música**. Como posso ajudar você hoje?"}
    ]

with st.sidebar:
    st.title("🎸 Empório da Música")
    st.subheader("Atendimento",
                 text_alignment="center")
    if st.button("🧹 Limpar Conversa", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Sou o Tom, especialista aqui da **Empório da Música**. Como posso ajudar você hoje?"}
        ]
        st.rerun()

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="👤").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="🎸").write(msg["content"])

if user_input := st.chat_input("Digite sua dúvida aqui..."):
    st.chat_message("user", avatar="👤").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="🎸"):
        with st.spinner("TEstou consultando o sistema..."):
            try:
                resposta_tom = st.session_state.agent.responder(user_input)
                st.write(resposta_tom)
                st.session_state.messages.append({"role": "assistant", "content": resposta_tom})
            except Exception as e:
                st.error("Ops! Ocorreu um erro ao processar sua pergunta. Tente novamente.")
                print(f"[ERRO APP]: {e}")