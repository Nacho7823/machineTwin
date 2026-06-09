# MachineTwin


## Crear entorno

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

## Correr

Iniciar simulador con 


```bash
python ./simulator/simulator.py 2
```
El 2 es el intervalo

el simulador crea datos en la carpeta data

**operation_history.csv:** historia de la maquina

**machine_current.json:** estado actual de la maquina


En `docs-machines` se encuentran los documentos tecnicos de la maquina



Correr la app

```bash
python main.py
```

## Arquitectura
La app se divide en:

**ui.py:** Interfaz grafica terminal

**utils.py:** Utilidades

**config.py:** Configuracion

**main.py:** Donde esta el agente

**rag.py:** Implementacion del rag

**tools.py:** Herramientas del agente. tool de rag y de acceso a archivos








