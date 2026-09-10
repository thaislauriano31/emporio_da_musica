from settings import AppSettings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool

embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-small",
    model_kwargs={'device': 'cpu', 'token': AppSettings().hf_token},
    encode_kwargs={'normalize_embeddings': True}
)

vectorstore = FAISS.load_local(
    "../faiss_index", 
    embeddings, 
    allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

@tool
def consultar_politicas(query: str) -> str:
    """Consulte esta ferramenta sempre que o cliente fizer perguntas sobre:
    regras da loja, políticas de troca, devolução, garantia, formas de pagamento,
    prazos de entrega, frete ou horários de funcionamento.
    
    Args:
        query: A dúvida do cliente.
    """
    busca_formatada = f"query: {query}"
    docs = retriever.invoke(busca_formatada)
    
    resultados = [doc.page_content.replace("passage: ", "") for doc in docs]
    
    resultado_final = "\n\n".join(resultados)
    return resultado_final if resultado_final else "Nenhuma política encontrada sobre este assunto."