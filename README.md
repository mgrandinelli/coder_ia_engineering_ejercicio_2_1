# Ejercicio 2.1: Refactorización a LCEL asíncrono

Curso AI Engineering (Coderhouse), módulo 2, unidad "Arquitectura de cadenas con LCEL y runnables".

La llamada manual a los SDK del módulo 1 se reemplaza por una cadena declarativa de LangChain. La cadena recibe una pregunta como diccionario y devuelve la respuesta como texto plano:

```python
chain = prompt | model | StrOutputParser()
respuesta = await chain.ainvoke({"pregunta": "¿Qué es la entropía?"})
```

## Cómo ejecutarlo

Requiere Python 3.12 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # y completar la clave
python main.py
```

## Variables de entorno

| Variable | Obligatoria | Qué es |
|---|---|---|
| `LLM_PROVIDER` | No (por defecto `openai`) | Proveedor a usar: `openai` o `anthropic` |
| `OPENAI_API_KEY` | Con OpenAI | Clave de la API de OpenAI |
| `ANTHROPIC_API_KEY` | Con Anthropic | Clave de la API de Anthropic |
| `OPENAI_MODEL` | No (por defecto `gpt-4o-mini`) | Modelo de OpenAI |
| `ANTHROPIC_MODEL` | No (por defecto `claude-haiku-4-5`) | Modelo de Anthropic |

Solo hace falta la clave del proveedor elegido. El archivo `.env` está en `.gitignore`.

## Qué hace

`main.py` tiene cuatro piezas:

| Pieza | Qué es |
|---|---|
| `prompt` | `ChatPromptTemplate.from_messages` con un mensaje `system`, un mensaje `human` y la variable `{pregunta}` |
| `build_model()` | Devuelve `ChatOpenAI` o `ChatAnthropic` según `LLM_PROVIDER`, con modelo y `temperature` configurados |
| `build_chain()` | Compone `prompt \| model \| StrOutputParser()` con el operador `\|` |
| `main()` | Corrutina que ejecuta la cadena con `await chain.ainvoke({"pregunta": ...})` e imprime el texto |

El recorrido de los datos dentro de la cadena es:

1. El diccionario `{"pregunta": "..."}` entra al `prompt`, que arma los mensajes con sus roles.
2. El modelo recibe esos mensajes y devuelve un `AIMessage`.
3. `StrOutputParser` extrae el contenido del mensaje y entrega un `str`.

## Criterios de aceptación

| Criterio | Dónde está en `main.py` |
|---|---|
| Flujo principal solo con sintaxis LCEL (`\|`) | `build_chain()`: `prompt \| model \| StrOutputParser()` |
| Ejecución asíncrona | `main()`: `await chain.ainvoke({"pregunta": pregunta})` |
| Salida en texto plano | Último eslabón `StrOutputParser()`; `main()` imprime un `str` |
| `ChatPromptTemplate` con roles System/Human | `prompt`, definido con `from_messages` |

Los dos errores comunes que menciona la consigna están cubiertos: la llamada usa `await`, y la clave del diccionario (`pregunta`) coincide con la variable del prompt (`{pregunta}`).

## Salida esperada

Con una clave válida (el texto de la respuesta varía en cada ejecución):

```
Pregunta: ¿Qué es la entropía?
Respuesta: La entropía es una medida del desorden de un sistema...
```

Sin clave configurada el script informa el problema y termina sin error:

```
[ERROR] Falta la variable de entorno OPENAI_API_KEY
```

Si la API falla (clave inválida, límite de tasa o red), se imprime una línea `[ERROR]` con el motivo, sin traceback.

## Tests

```bash
pytest
```

Son 9 tests y tardan unos 2 segundos. No usan la red ni claves: el modelo se reemplaza por `FakeListChatModel`, el modelo falso que trae LangChain.

| Test | Qué comprueba |
|---|---|
| `test_la_cadena_es_prompt_modelo_parser_compuesta_con_lcel` | La cadena es un `RunnableSequence` con prompt, modelo y parser en ese orden |
| `test_ainvoke_devuelve_texto_plano_y_no_un_mensaje` | `await chain.ainvoke(...)` devuelve un `str` |
| `test_el_prompt_tiene_roles_system_y_human_y_la_variable_pregunta` | El prompt genera un `SystemMessage` y un `HumanMessage` |
| `test_una_clave_que_no_coincide_con_el_prompt_falla` | Un diccionario con otra clave produce un `KeyError` |
| `test_build_model_configura_modelo_y_temperature` | Modelo y `temperature` de cada proveedor |
| `test_main_imprime_la_respuesta_como_texto` | `main()` imprime y devuelve el texto |
| `test_main_sin_clave_informa_y_no_se_rompe` | Sin clave no hay excepción (un caso por proveedor) |
| `test_main_informa_un_fallo_de_la_api_sin_traceback` | Un fallo del modelo termina en una línea `[ERROR]` |

## Decisiones de diseño

- **Modelo de Anthropic elegido por la `temperature`.** La consigna pide configurar `temperature`, así que `ChatOpenAI` y `ChatAnthropic` se crean con `temperature=0.2`. Para cumplirlo en Anthropic el modelo por defecto es `claude-haiku-4-5`, que acepta ese parámetro. Los modelos Claude más recientes (por ejemplo `claude-opus-5-5`) ya no lo usan: regulan solos la variabilidad de la respuesta y rechazan `temperature` con un error 400. Con uno de esos modelos en `ANTHROPIC_MODEL`, el script informa ese error en una línea `[ERROR]`.
- **El modelo se crea dentro de una función.** `ChatOpenAI` falla al construirse si no hay clave; al crearlo en `build_model()` y no al importar el módulo, `main.py` se puede importar y testear sin credenciales.
- **`astream` y `abatch`.** Por ser una cadena LCEL, la misma `chain` admite `chain.astream(...)` para recibir la respuesta en fragmentos y `chain.abatch([...])` para procesar varias preguntas a la vez, sin cambiar su definición.
