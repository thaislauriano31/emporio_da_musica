from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def gerar_banco_vetorial():
    loader = PyPDFLoader("../data/politicas_da_loja.pdf")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs)

    for chunk in chunks:
        chunk.page_content = f"passage: {chunk.page_content}"

    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-small",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("../faiss_index")
    print("Base vetorial salva na pasta 'faiss_index/'.")

if __name__ == "__main__":
    gerar_banco_vetorial()