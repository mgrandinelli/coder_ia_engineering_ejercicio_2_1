"""Ejercicio 2.1 - Refactorización a LCEL asíncrono.

La llamada manual al SDK del módulo 1 pasa a ser una cadena declarativa:
ChatPromptTemplate | modelo | StrOutputParser.
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

PREGUNTA = "¿Qué es la entropía?"
TEMPERATURE = 0.2
API_KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
SIN_CLAVE = "sin-configurar"  # permite construir el modelo e importar el módulo sin credenciales


# --- 2. Modelo de LangChain en lugar del cliente manual ---
def build_model(provider: str | None = None) -> BaseChatModel:
    provider = provider or os.getenv("LLM_PROVIDER") or "openai"
    # Cada integración se importa solo si se usa: alcanza con tener instalada una de las dos.
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL") or "claude-haiku-4-5",
            temperature=TEMPERATURE,
            max_tokens=1024,
            api_key=os.getenv("ANTHROPIC_API_KEY") or SIN_CLAVE,
        )
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
        temperature=TEMPERATURE,
        api_key=os.getenv("OPENAI_API_KEY") or SIN_CLAVE,
    )


model = build_model()

# --- 3. Template con roles System/Human y una variable ---
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Sos un divulgador científico. Respondé en español, en dos o tres oraciones."),
        ("human", "{pregunta}"),
    ]
)

parser = StrOutputParser()

# --- 4. Cadena LCEL: dict -> PromptValue -> AIMessage -> str ---
chain = prompt | model | parser


# --- 5. Ejecución asíncrona ---
async def main(pregunta: str = PREGUNTA) -> str | None:
    provider = os.getenv("LLM_PROVIDER") or "openai"
    variable = API_KEY_ENV.get(provider)
    if variable is None:
        print(f"[ERROR] LLM_PROVIDER debe ser 'openai' o 'anthropic', no '{provider}'")
        return None
    if not os.getenv(variable):
        print(f"[ERROR] Falta la variable de entorno {variable}")
        return None

    try:
        respuesta = await chain.ainvoke({"pregunta": pregunta})
    except Exception as exc:
        # Clave inválida, límite de tasa o red: el script informa y termina sin traceback.
        print(f"[ERROR] {type(exc).__name__}: {exc}")
        return None

    print(f"Pregunta: {pregunta}")
    print(f"Respuesta: {respuesta}")
    return respuesta


if __name__ == "__main__":
    asyncio.run(main())
