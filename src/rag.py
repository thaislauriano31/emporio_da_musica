from settings import AppSettings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool
from langchain_mongodb import MongoDBAtlasVectorSearch

settings = AppSettings()
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-small",
    model_kwargs={'device': 'cpu', 'token': settings.hf_token},
    encode_kwargs={'normalize_embeddings': True}
)

vector_store = MongoDBAtlasVectorSearch(
    embedding=embeddings,
    collection=settings.MONGODB_COLLECTION,
    index_name=settings.VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
    type="vectorSearch"
)

@tool
def consultar_politicas(query: str) -> str:
    """Consulte esta ferramenta sempre que o cliente fizer perguntas sobre:
    regras da loja, políticas de troca, devolução, garantia, formas de pagamento,
    prazos de entrega, frete ou horários de funcionamento.
    
    Args:
        query: A dúvida do cliente.
    """
    busca_formatada = f"query: {query}"
    docs = vector_store.similarity_search(busca_formatada, k=3)
    
    resultados = [doc.page_content.replace("passage: ", "") for doc in docs]
    
    resultado_final = "\n\n".join(resultados)
    return resultado_final if resultado_final else "Nenhuma política encontrada sobre este assunto."