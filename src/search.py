import os
from dotenv import load_dotenv

from utf8_sanitize import sanitize_utf8
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def search_prompt():
  for k in ("GOOGLE_EMBEDDING_MODEL","DATABASE_URL","PG_VECTOR_COLLECTION_NAME","GOOGLE_API_KEY"):
      if not os.getenv(k):
          raise RuntimeError(f"Environment variable {k} is not set")

  embeddings = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL"))

  store = PGVector(
      embeddings=embeddings,
      collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
      connection=os.getenv("DATABASE_URL"),
      use_jsonb=True,
  )

  llm = init_chat_model(model="gemini-2.5-flash", model_provider="google_genai")

  prompt_template = PromptTemplate(
      input_variables=["contexto", "pergunta"],
      template=PROMPT_TEMPLATE
  )

  def retrieve_and_answer(query: str) -> str:
      query = sanitize_utf8(query)
      results = store.similarity_search_with_score(query, k=10)

      contexto = sanitize_utf8(
          "\n\n".join(doc.page_content for doc, _ in results)
      )

      chain = prompt_template | llm | StrOutputParser()

      response = chain.invoke({"contexto": contexto, "pergunta": query})
      return response

  return retrieve_and_answer