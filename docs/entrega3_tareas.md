# Entrega 3 - Backlog de tareas MachineTwin

## Objetivo

Cerrar la entrega final con trazabilidad demostrable, memoria persistente por chat, detección determinística de rangos, evaluación automatizada y documentación técnica suficiente para responder acciones de operación y mantenimiento.

## Estado auditado

- Hay una implementación inicial de persistencia (`persistence.py`), endpoints de conversaciones/trazas, Docker Compose y migraciones versionadas.
- La UI de chat ya consulta y sincroniza conversaciones persistidas, manteniendo `localStorage` como fallback visual.
- La vista `Trazas` muestra metadata enriquecida como latencia, modelo, prompt version y chunks RAG recuperados.
- La migración y la capa PostgreSQL fueron verificadas localmente con Docker Compose; falta capturar evidencia visual/salidas para el informe final y probar el flujo completo desde la UI web.
- Hay fixtures automatizados nuevos, pero el dataset aún no llega al mínimo recomendado de 20 casos y debe validarse en un entorno con dependencias instaladas.

## Prioridad Alta

- [x] Implementar `detectar_fuera_de_limites` como tool pública del agente.
  - Fuente de rangos: `config/machines.json`.
  - Estados requeridos: `normal`, `fuera_rango_optimo`, `fuera_rango_operativo`, `sin_datos`.
  - Debe informar valor, unidad, rango óptimo y rango operativo por variable.

- [x] Completar PostgreSQL como persistencia operativa principal.
  - Configuración vía `DATABASE_URL`.
  - Guardar conversaciones, mensajes, trazas, tool calls y respuestas.
  - Mantener JSONL como respaldo de observabilidad local.
  - Estado actual: implementado con migraciones versionadas y verificado localmente contra Docker.

- [x] Agregar Docker Compose para PostgreSQL.
  - Crear `docker-compose.yml` con servicio `postgres`.
  - Definir usuario, password, base y puerto por variables de entorno.
  - Persistir datos en un volumen Docker.
  - Agregar healthcheck para que la app pueda esperar a que la base esté lista.

- [x] Agregar migraciones versionadas de base de datos.
  - Crear carpeta de migraciones SQL o configurar una herramienta liviana de migraciones.
  - Versionar tablas de conversaciones, mensajes y trace events.
  - Evitar depender solo de `CREATE TABLE IF NOT EXISTS` al iniciar la app.
  - Documentar cómo aplicar y re-aplicar migraciones en un entorno limpio.
  - Incluir una tabla de control tipo `schema_migrations` para saber qué migraciones se aplicaron.

- [x] Crear comando de gestión de base de datos.
  - Agregar un módulo ejecutable, por ejemplo `python -m db migrate`, para aplicar migraciones.
  - Agregar `python -m db status` para verificar conexión y versión aplicada.
  - Agregar `python -m db reset` para desarrollo local, con confirmación o flag explícito.
  - Evitar que la app cree/modifique schema de forma silenciosa en cada arranque.

- [x] Asegurar que todos los datos conversacionales queden en PostgreSQL.
  - Guardar mensajes de usuario y respuestas del agente.
  - Guardar requests/responses del LLM.
  - Guardar tool calls con inputs, outputs y errores.
  - Guardar eventos de limpieza de conversación.
  - Mantener `logs/traces.jsonl` solo como respaldo local, no como fuente principal.
  - Persistir errores del LLM y de tools, no solo ejecuciones exitosas.
  - Asociar cada evento a `conversation_id` y `trace_id`.

- [x] Sincronizar la UI de chat con conversaciones persistidas.
  - Cargar conversaciones desde PostgreSQL al iniciar la app web.
  - Cargar mensajes persistidos al seleccionar una conversación.
  - Mantener `localStorage` solo como fallback o caché visual, no como fuente principal.
  - Al eliminar una conversación desde el sidebar, borrar también mensajes y trazas de PostgreSQL.
  - Al limpiar un chat, registrar el evento de limpieza en trazas.

- [x] Documentar setup de base de datos en README.
  - Comando para levantar PostgreSQL con Docker.
  - Variables necesarias en `.env`.
  - Comando para aplicar migraciones.
  - Comando para verificar conexión.
  - Cómo resetear datos de desarrollo sin borrar el código.
  - Flujo completo esperado: `docker compose up -d postgres`, migraciones, simulador, backend web.

- [x] Completar memoria persistente por chat.
  - Cargar historial por `conversation_id`.
  - Guardar cada mensaje de usuario y respuesta del agente.
  - Limpiar memoria persistida cuando el usuario limpia una conversación.
  - Estado actual: integrada con backend y frontend; falta validar manualmente el flujo completo desde navegador.

- [ ] Completar vista web de trazas.
  - Navegación interna entre `Chat` y `Trazas`.
  - Listado de conversaciones persistidas.
  - Detalle de mensajes, eventos, tools ejecutadas, inputs/outputs y timestamps.
  - Mostrar estados de carga, vacío y error con claridad.
  - Mostrar metadata enriquecida cuando se implemente: modelo, latencia, prompt version, duración de tools y chunks RAG.
  - Estado actual: existe una primera vista React integrada con endpoints; falta metadata completa y evidencia contra DB real.

## Prioridad Media

- [ ] Completar suite automatizada de evaluación.
  - Cubrir los 9 casos manuales de `docs/casos_prueba.md`.
  - Validar tools esperadas por caso.
  - Calcular promedio por métrica y porcentaje de aprobación.
  - Guardar reporte JSON por corrida.
  - Separar checks determinísticos de métricas LLM-as-judge.
  - Marcar tests DeepEval con `pytest.mark.deepeval` o runner separado para que no bloqueen tests unitarios.
  - Ejecutar la suite en un entorno con dependencias instaladas y guardar evidencia del resultado.
  - Estado actual: hay fixtures y runner inicial, pero falta ejecución validada y limpieza de duplicados.

- [ ] Ejecutar evaluación con segundo juez.
  - Configurar `SECOND_JUDGE_LLM_MODEL`.
  - Comparar métricas principales contra el juez base.
  - Reportar divergencias relevantes.
  - Guardar resultados del segundo juez en el reporte final.

- [x] Expandir dataset automatizado de 9 a 20 casos.
  - Agregar paráfrasis de consultas existentes.
  - Agregar preguntas ambiguas, fuera de dominio y adversariales.
  - Agregar casos donde falten datos o documentación suficiente.
  - Mantener expected tools y criterio de aprobación por caso.

- [x] Versionar el system prompt y registrar `System Prompt version`.
  - Definir una versión explícita para `config/systemprompt.md`.
  - Registrar `System Prompt version` en trazas y reportes de benchmarks.
  - Guardar copia historica en `config/prompts/systemprompt-0.0.1.md`.
  - Resolver prompt activo por `SYSTEM_PROMPT_PATH`, luego `SYSTEM_PROMPT_VERSION`, y fallback a `config/systemprompt.md`.
  - Usar la versión para comparar corridas cuando cambien prompt, modelo, datos o tools.
  - Documentar cuándo se incrementa la versión del prompt.

- [x] Enriquecer trazas con metadata operativa.
  - Registrar `latency_ms` por request del LLM.
  - Registrar duración de cada tool call.
  - Registrar modelo usado en cada respuesta.
  - Mantener `trace_id` y `conversation_id` como identificadores principales.
  - Registrar `System Prompt version`.
  - Registrar errores y límite de pasos de razonamiento.
  - Mostrar estos campos en la vista `Trazas`.

- [x] Registrar metadata de chunks RAG recuperados.
  - Guardar título/documento, `doc_id`, `chunk_index` y distancia de similitud en la traza.
  - Usar esta metadata para auditoría interna aunque no se muestre siempre al usuario.
  - Conservar la política actual de citas contextuales, sin exigir línea exacta por defecto.
  - Mostrar un resumen compacto en UI, por ejemplo cantidad de chunks y documentos fuente.

- [ ] Revisar alineación del RAG con material de clase.
  - Mantener RAG dense/naive si las métricas alcanzan.
  - Considerar BM25/hybrid solo si los casos de evaluación muestran fallas por jerga técnica, IDs o vocabulario exacto.
  - Documentar la decisión en el informe final.

- [x] Extender documentación técnica de máquinas.
  - Agregar operación recomendada.
  - Agregar verificación de fallas.
  - Agregar acciones sugeridas.
  - Agregar criterios de parada o escalamiento.

- [ ] Revisar documentación técnica contra casos de prueba.
  - Verificar que cada recomendación frecuente tenga soporte en `docs-machines`.
  - Agregar faltantes detectados por los casos 5, 6 y 7.
  - Evitar que el agente dependa de conocimiento genérico no documentado.

## Prioridad Baja

- [x] Preparar evidencia para informe final.
  - Capturas de la vista de chat.
  - Capturas de la vista de trazas.
  - Resumen de arquitectura final.
  - Tabla de resultados de tests y porcentaje de aprobación.
  - Captura o salida de `docker compose ps`.
  - Captura o salida del comando de migraciones aplicado.
  - Captura o salida de consultas a endpoints `/api/conversations` y `/api/traces/{conversation_id}`.

- [ ] Revisar prompts y respuestas observadas.
  - Mantener política de citas contextual.
  - Evitar exigir líneas exactas de documentación salvo pedido explícito del usuario.
  - Confirmar que las recomendaciones no inventen causas ni tareas.
  - Re-ejecutar casos manuales después de completar DB, trazas y prompt version.
  - Completar campos `Resultado` y `Comentario` en `docs/casos_prueba.md`.

## Criterios de aceptación

- El agente puede detectar variables fuera de rango sin depender del LLM ni del RAG.
- PostgreSQL se levanta con Docker Compose y queda documentado en README.
- Las migraciones se aplican con un comando reproducible y versionado.
- Cada conversación mantiene memoria independiente y persistente en PostgreSQL.
- La UI permite inspeccionar trazas y uso de tools por conversación desde datos persistidos.
- Los tests automatizados generan reporte con métricas y porcentaje de aprobación en un entorno reproducible.
- La documentación técnica permite responder qué revisar ante temperatura, vibración, presión, caudal, corriente, RPM, consumo o eficiencia anómalos.
