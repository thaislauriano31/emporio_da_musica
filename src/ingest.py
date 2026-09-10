from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from settings import AppSettings
from langchain_mongodb import MongoDBAtlasVectorSearch

def gerar_banco_vetorial():
    loader = PyPDFLoader("../data/politicas_da_loja.pdf")
    docs = loader.load()
    settings = AppSettings()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs)

    for chunk in chunks:
        chunk.page_content = f"passage: {chunk.page_content}"

    embedding_generator = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-small",
        model_kwargs={'device': 'cpu', 'token': settings.hf_token},
        encode_kwargs={'normalize_embeddings': True}
    )

    vector_store = MongoDBAtlasVectorSearch(
        embedding=embedding_generator,
        collection=settings.MONGODB_COLLECTION,
        index_name=settings.VECTOR_SEARCH_INDEX_NAME,
        relevance_score_fn="cosine",
        type="vectorSearch"
    )
    vector_ids = vector_store.add_documents(chunks)

if __name__ == "__main__":
    gerar_banco_vetorial()