"""Tests del ejercicio 2.1. No usan la red: el modelo se reemplaza por uno falso de LangChain.

Ejecutar con: pytest
"""

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence

import main

pytestmark = pytest.mark.asyncio

RESPUESTA = "La entropía mide el desorden de un sistema."


def modelo_falso() -> FakeListChatModel:
    return FakeListChatModel(responses=[RESPUESTA])


async def test_la_cadena_es_prompt_modelo_parser_compuesta_con_lcel():
    modelo = modelo_falso()

    chain = main.build_chain(modelo)

    assert isinstance(chain, RunnableSequence)
    assert isinstance(chain.steps[0], ChatPromptTemplate)
    assert chain.steps[1] is modelo
    assert isinstance(chain.steps[2], StrOutputParser)


async def test_ainvoke_devuelve_texto_plano_y_no_un_mensaje():
    respuesta = await main.build_chain(modelo_falso()).ainvoke({"pregunta": "¿Qué es la entropía?"})

    assert isinstance(respuesta, str)
    assert respuesta == RESPUESTA


async def test_el_prompt_tiene_roles_system_y_human_y_la_variable_pregunta():
    mensajes = main.prompt.format_messages(pregunta="¿Qué es un qubit?")

    assert main.prompt.input_variables == ["pregunta"]
    assert isinstance(mensajes[0], SystemMessage)
    assert isinstance(mensajes[1], HumanMessage)
    assert mensajes[1].content == "¿Qué es un qubit?"


async def test_una_clave_que_no_coincide_con_el_prompt_falla():
    with pytest.raises(KeyError):
        await main.build_chain(modelo_falso()).ainvoke({"question": "¿Qué es la entropía?"})


async def test_build_model_configura_modelo_y_temperature(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    openai = main.build_model("openai")
    anthropic = main.build_model("anthropic")

    assert (openai.model_name, openai.temperature) == ("gpt-4o-mini", 0.2)
    assert (anthropic.model, anthropic.temperature) == ("claude-haiku-4-5", 0.2)


async def test_main_imprime_la_respuesta_como_texto(monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(main, "build_model", modelo_falso)

    respuesta = await main.main()

    assert respuesta == RESPUESTA
    assert f"Respuesta: {RESPUESTA}" in capsys.readouterr().out


@pytest.mark.parametrize("provider, variable", [("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")])
async def test_main_sin_clave_informa_y_no_se_rompe(monkeypatch, capsys, provider, variable):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.delenv(variable, raising=False)

    assert await main.main() is None
    assert f"Falta la variable de entorno {variable}" in capsys.readouterr().out


async def test_main_informa_un_fallo_de_la_api_sin_traceback(monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(main, "build_model", lambda: FakeListChatModel(responses=[]))

    assert await main.main() is None
    assert "[ERROR]" in capsys.readouterr().out
