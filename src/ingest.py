import os
from utf8_sanitize import sanitize_utf8
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector 
from dotenv import load_dotenv

load_dotenv()


def _resolve_pdf_path() -> str:
    raw = os.getenv("PDF_PATH")
    if not raw:
        raise RuntimeError("Environment variable PDF_PATH is not set")
    raw = os.path.expanduser(raw)
    if os.path.isdir(raw):
        name = os.getenv("PDF_FILENAME") or "document.pdf"
        return os.path.join(raw, name)
    return raw


def ingest_pdf():
    for k in ("GOOGLE_EMBEDDING_MODEL","DATABASE_URL","PG_VECTOR_COLLECTION_NAME","GOOGLE_API_KEY"):
        if not os.getenv(k):
            raise RuntimeError(f"Environment variable {k} is not set")

    pdf_path = _resolve_pdf_path()
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(
            f"PDF não encontrado: {pdf_path}. "
            "Defina PDF_PATH como diretório existente (e opcionalmente PDF_FILENAME) "
            "ou como caminho absoluto/relativo para o arquivo .pdf."
        )

    docs = PyPDFLoader(str(pdf_path)).load()

    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=False,
    ).split_documents(docs)
    if not splits:
        raise RuntimeError(
            "Nenhum trecho foi extraído do PDF (lista de chunks vazia). "
            "Verifique se o arquivo tem texto extraível e não está corrompido."
        )

    enriched = [
        Document(
            page_content=sanitize_utf8(d.page_content),
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        for d in splits
    ]    

    ids = [f"doc-{i}" for i in range(len(enriched))]

    embeddings = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL"))

    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )

    store.add_documents(documents=enriched, ids=ids)

if __name__ == "__main__":
    ingest_pdf()