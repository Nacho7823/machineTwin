import asyncio
import signal
import sys
from pathlib import Path

try:
    from simulator.config import DATA_DIR
    from simulator.simulator import create_simulators, start_simulators, stop_simulators
except ImportError:
    from config import DATA_DIR
    from simulator import create_simulators, start_simulators, stop_simulators


def _parse_interval(argv: list[str]) -> int:
    if len(argv) <= 1:
        return 3
    try:
        return int(argv[1])
    except ValueError:
        print("El intervalo debe ser un numero entero. Usando 3 segundos.")
        return 3


async def main(data_dir: Path = DATA_DIR):
    interval = _parse_interval(sys.argv)
    simulators = create_simulators(data_dir)

    start_simulators(simulators, interval)
    print(f"Simulador iniciado (intervalo: {interval}s, datos en: {data_dir})")
    print("Presiona Ctrl+C para detener")

    stop = asyncio.Event()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    stop_simulators(simulators)
    print("\nSimulador detenido")


if __name__ == "__main__":
    asyncio.run(main())
