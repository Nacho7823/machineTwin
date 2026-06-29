# Evaluacion benchmark semantic_rag con dos jueces

## Corrida analizada

- Reporte: `tests/reports/benchmark_20260629_183950.json`
- Log de consola: `logs/test-runs/nemotron-super_prompt-0.0.1_semantic-rag_2judges.log`
- Estado: `complete`
- System Prompt version: `0.0.1`
- Perfil: `semantic_rag`
- Casos completados: 19/19
- Agente: `nvidia/nemotron-3-super-120b-a12b`
- Juez principal: `nvidia/nemotron-3-super-120b-a12b`
- Segundo juez: `meta/llama-3.3-70b-instruct`

No se encontro en `tests/reports/` una corrida nueva equivalente para `System Prompt version = 0.0.2`; este documento analiza la corrida completa disponible.

## Metodologia de lectura

El runner calcula la aprobacion oficial con el juez principal. Para esta evaluacion se agrega una lectura combinada:

1. Para cada metrica y caso, se promedia el puntaje disponible del juez principal y del segundo juez.
2. Si solo uno de los dos jueces produjo puntaje, se usa ese puntaje disponible.
3. El promedio combinado del caso es el promedio de sus metricas combinadas disponibles.
4. Un caso se considera aprobado en la lectura combinada si pasa los checks deterministas y, cuando tiene metricas, su promedio combinado es mayor o igual a 0.7.

Las metricas usadas son:

- `faithfulness`
- `answer_relevance`
- `context_precision`

## Resultado global

| Lectura | Resultado |
|---|---:|
| Aprobacion oficial del runner | 12/19 (63.16%) |
| Aprobacion combinada de ambos jueces | 13/19 (68.42%) |
| Aprobacion combinada excluyendo el caso con timeout de LLM | 13/18 (72.22%) |

## Promedios por metrica

| Metrica | Juez principal | Segundo juez | Promedio combinado |
|---|---:|---:|---:|
| `faithfulness` | 0.9063 (n=3) | 0.9583 (n=6) | 0.9349 (n=6) |
| `answer_relevance` | 0.9419 (n=7) | 0.7338 (n=7) | 0.8379 (n=7) |
| `context_precision` | 0.6423 (n=2) | 0.7227 (n=2) | 0.5767 (n=3) |

La metrica mas debil sigue siendo `context_precision`. Esto sugiere que, aunque las respuestas suelen ser relevantes y bastante fieles, el orden/calidad de los fragmentos recuperados por RAG no siempre coincide con lo que el juez espera como contexto mas preciso.

## Resultado por caso

| Caso | Checks | Juez principal | Segundo juez | Promedio jueces | Resultado combinado | Observacion |
|---|---|---:|---:|---:|---|---|
| `adversarial` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `ask_inexistent_machine` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `conversational_memory` | `expected_tools_used` | - | - | - | No aprobado | No paso checks deterministas: falta uso de tool esperada. |
| `current_status` | OK | 1.000 | 1.000 | 1.000 | Aprobado | Ambos jueces coinciden en resultado excelente. |
| `documented_operation` | OK | 1.000 | 0.625 | 0.720 | Aprobado | Pasa por poco en lectura combinada; el segundo juez fue mas estricto. |
| `fail_on_temperature` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `followup_events_after_status` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `high_but_normal_temperature` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `high_vibration_advice` | `expected_tools_used` | - | - | - | No aprobado | La respuesta existe, pero no se registro una tool esperada. |
| `maintenance_recommendation` | OK | 0.797 | 0.875 | 0.870 | Aprobado | Buen resultado documental con acuerdo razonable entre jueces. |
| `missing_variable_trend` | `expected_tools_used` | - | - | - | No aprobado | La respuesta fue util, pero no se registro `analizar_tendencia`. |
| `operational_problem_summary` | `expected_tools_used` | 1.000 | 1.000 | 1.000 | No aprobado | La respuesta fue muy buena para ambos jueces, pero fallo trazabilidad por tool esperada. |
| `out_of_limits` | OK | 1.000 | 0.667 | 0.771 | Aprobado | Pasa combinado; Llama fue mas exigente con la respuesta. |
| `rag_source_request` | `expected_tools_used` | - | - | - | No aprobado | Responde con fuentes, pero no queda trazada la tool de documentacion esperada. |
| `recent_events` | OK | 1.000 | 0.750 | 0.875 | Aprobado | Buen resultado; el segundo juez fue mas conservador. |
| `stop_criteria` | OK | 0.668 | 1.000 | 0.715 | Aprobado | Con un solo juez no alcanzaba el umbral; con promedio de jueces queda aprobado. |
| `temperature_trend` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `tool_free_domain_guard` | OK | - | - | - | Aprobado | Evaluado solo por checks deterministas. |
| `verify_failure_actions` | `agent_response_ok` | - | - | - | No aprobado | Falla por timeout del LLM en la respuesta final. |

## Caso fallido por LLM

El caso `verify_failure_actions` no fallo por contenido incorrecto sino por una falla de proveedor/modelo:

```text
Error al consultar el LLM: Request timed out.
```

El check `expected_tools_used` paso, por lo que el agente llego a ejecutar la tool esperada. La falla se produjo al generar la respuesta final. Para el informe conviene reportarlo como error de ejecucion del LLM y no como evidencia semantica contra el agente.

## Interpretacion

La corrida muestra una mejora clara respecto de benchmarks anteriores: el agente completa los 19 casos, no hay rate limit, y la mayoria de los casos relevantes aprueban. Con lectura combinada de ambos jueces, el resultado queda en 68.42%, o 72.22% si se excluye el unico caso afectado por timeout del LLM.

Los principales problemas no son de contenido final sino de trazabilidad de tools. Hay casos donde la respuesta parece adecuada, e incluso obtiene buen puntaje del juez, pero falla porque no quedo registrada una tool esperada:

- `operational_problem_summary`: ambos jueces dan 1.0, pero falta tool esperada.
- `rag_source_request`: responde fuentes, pero no queda trazada la consulta documental.
- `high_vibration_advice`: responde tecnicamente, pero falta una tool esperada.
- `missing_variable_trend`: responde correctamente que no existe humedad relativa, pero no queda trazado `analizar_tendencia`.

Tambien se observa variabilidad entre jueces. Nemotron tiende a ser mas favorable en algunos casos, mientras que Llama penaliza mas la relevancia o precision documental. Por eso el promedio combinado es una lectura mas robusta que mirar solo un juez.

## Puntos de mejora

- Mejorar la obediencia del agente al checklist de tools obligatorias, especialmente en preguntas de seguimiento, fuentes documentales y variables inexistentes.
- Revisar trazas de casos donde la respuesta es buena pero falla `expected_tools_used`; puede haber un problema real de ruteo o una expectativa demasiado estricta del test.
- Mejorar `context_precision` en casos documentales, revisando recuperacion y ranking de chunks.
- Repetir la corrida con `System Prompt version = 0.0.2` para comparar contra esta base `0.0.1`.
- Si se vuelve a ejecutar `verify_failure_actions`, conviene mantener el mismo perfil y jueces para confirmar si el timeout fue aislado.
