import asyncio
import signal
import sys
from config import DATA_DIR
from simulator import MachineSimulator


async def main():
    simulator = MachineSimulator(DATA_DIR)
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    simulator.start(interval)
    print(f"Simulador iniciado (intervalo: {interval}s, datos en: {DATA_DIR})")
    print("Presiona Ctrl+C para detener")

    stop = asyncio.Event()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    simulator.stop()
    print("\nSimulador detenido")


if __name__ == "__main__":
    asyncio.run(main())
