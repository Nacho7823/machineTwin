# MachineTwin
Un gemelo digital para maquinas


## Crear entorno
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion del LLM

La aplicacion usa un cliente compatible con OpenAI mediante LangChain. Por defecto se utiliza Kilo AI:

- `LLM_BASE_URL=https://api.kilo.ai/api/gateway/`
- `LLM_MODEL=stepfun/step-3.7-flash:free`
- `LLM_API_KEY=` puede quedar vacio en esta configuracion.

Para usar la configuracion por defecto:

```bash
cp .env.example .env
```

Si se utiliza otro proveedor compatible con OpenAI, se deben modificar estas variables en `.env`.

## Correr

Iniciar simulador con:
```bash
python ./simulator/simulator.py 2
```
El 2 es el intervalo

El simulador crea datos en la carpeta data
 - **operation_history.csv:** historia de la maquina
 - **machine_current.json:** estado actual de la maquina


En `docs-machines` se encuentran los documentos tecnicos de la maquina, usados por el rag


### Correr la app

#### 1 Compilar el frontend

```bash
cd frontend
npm i
npm run build
```
#### 2 Iniciar app
Correr app
```bash
python main.py web
```
La aplicacion expone la pagina web en localhost:8000. (se tiene que correr npm run build). 

## Arquitectura
La app se divide en:

**frontend**: pagina web para el chatbot  
**uiWen.py:** backend de la ui web(carpeta frontend)  
**uiTerminal.py:** Interfaz grafica terminal  
**utils.py:** Utilidades  
**config.py:** Configuracion  
**main.py:** Donde esta el agente  
**rag:** Carpeta de implementacion del rag  
**tools.py:** Herramientas del agente. tool de rag y de acceso a archivos







