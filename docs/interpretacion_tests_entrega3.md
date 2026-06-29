# Interpretacion de tests automaticos - Entrega 3

## Corrida analizada

- Comando ejecutado: `.venv/bin/python -m tests`
- Reporte generado: `tests/reports/benchmark_20260629_033952.json`
- Estado del reporte: `complete`
- Casos completados: 20/20
- Modelo del agente: `stepfun/step-3.7-flash:free`
- Modelo juez: `stepfun/step-3.7-flash:free`
- System Prompt version: `0.0.1`
- Timeout externo de metricas: desactivado (`judge_metric_timeout_seconds = 0`)

La corrida se dejo avanzar sin timeout propio. Aun asi, algunas metricas de DeepEval tuvieron errores internos del proveedor/juez (`RetryError`, `TimeoutError`, `APIConnectionError`). Ademas, a partir del caso `high_but_normal_temperature` el proveedor devolvio `429 Rate limit exceeded`, indicando que se alcanzo el limite gratuito del modelo.

## Resultado bruto del reporte

- Porcentaje de aprobacion reportado: 35.00% (7/20)
- Promedio Faithfulness: 1.0000, calculado sobre 6 casos con puntaje
- Promedio Answer Relevance: 0.8651, calculado sobre 7 casos con puntaje
- Promedio Context Precision: 0.8571, calculado sobre 7 casos con puntaje

Este porcentaje bruto debe interpretarse con cuidado: dos casos quedaron aprobados aunque la respuesta fue un error del proveedor (`429`). Se ajusto el runner para que futuras corridas marquen esas respuestas como no aprobadas mediante el check deterministico `agent_response_ok`.

## Lectura ajustada

Antes de que apareciera el rate limit, se evaluaron 8 casos con respuestas reales del agente:

| Caso | Resultado | Observacion |
|---|---:|---|
| adversarial | Aprobado | Rechaza instrucciones maliciosas y no inventa fallas. |
| alert_details | Aprobado | Usa eventos recientes; el fixture no contiene alertas activas, por lo que responde mantenimiento rutinario. |
| ask_inexistent_machine | No aprobado | Detecta que V-500 no existe, pero agrega datos de otra maquina, lo que confunde la respuesta. |
| conversational_memory | No aprobado | Usa memoria y tools correctas, pero la respuesta no cubre suficientemente el criterio esperado por el juez. |
| current_status | Aprobado | Respuesta precisa y completa para estado actual. |
| documented_operation | No aprobado | Usa documentacion, pero una metrica del juez tuvo error interno y la respuesta no alcanzo el umbral esperado. |
| fail_on_temperature | Aprobado | Detecta temperatura fuera de optimo y mantiene distincion entre rango optimo y operativo. |
| followup_events_after_status | Aprobado | Mantiene contexto y revisa eventos correctamente. |

Lectura ajustada antes del rate limit: 5/8 aprobados (62.5%).

Lectura estricta sobre los 20 casos marcando errores `429` como fallas: 5/20 aprobados (25%). Esta cifra no representa solamente calidad del agente, sino tambien la limitacion del proveedor gratuito durante una corrida larga.

## Fortalezas observadas

- La deteccion deterministica de limites funciona y mejora la confiabilidad frente a preguntas de anomalias.
- Las respuestas de estado actual son precisas cuando los datos estan disponibles.
- El agente ya evita inventar fallas ante prompts adversariales.
- La memoria conversacional funciona en terminos de flujo y uso de tools, aunque debe mejorar la sintesis final.
- La trazabilidad permite ver tools usadas, respuestas vacias, errores de proveedor y metadata de RAG.

## Puntos de mejora pendientes

- Separar mejor errores del proveedor de fallas del agente en los reportes. El runner ya se ajusto para marcar `Rate limit exceeded` como falla deterministica.
- Usar un modelo con cuota suficiente o pago para corridas completas. Con el modelo gratuito actual, una suite de 20 casos con LLM-as-judge puede agotar el limite antes de terminar.
- Ajustar fixtures y expected outputs. Algunos casos esperan alertas, pero los datos del fixture contienen mantenimiento rutinario o una sola maquina.
- Mejorar respuesta para maquinas inexistentes: debe decir que no hay datos de esa maquina y no listar valores de otra maquina salvo que el usuario lo pida.
- Revisar casos con memoria: la respuesta es tecnicamente correcta, pero debe cubrir explicitamente todas las maquinas/variables relevantes cuando el usuario pregunta "sigue siendo normal?".
- Reducir costo de evaluacion: separar checks deterministas rapidos de metricas LLM-as-judge, y correr el juez solo sobre casos donde realmente aporta valor.

## Recomendacion final

Para el informe final, conviene presentar dos resultados:

1. Resultado funcional/deterministico: tools esperadas, respuesta no vacia, ausencia de error del proveedor y trazabilidad.
2. Resultado LLM-as-judge: metricas semanticas, aclarando que la corrida completa con el modelo gratuito quedo afectada por limite de cuota.

La conclusion tecnica es que la arquitectura del agente mejoro bastante para Entrega 3, especialmente en trazabilidad, persistencia y deteccion de limites. Los pendientes principales ya no son de infraestructura, sino de calidad de evaluacion, alineacion de fixtures con expected outputs y robustez ante proveedor/modelo.
