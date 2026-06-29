from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / "migrations"


def _database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL no esta configurado. Revisa .env o .env.example.")
    return database_url


def _connect():
    import psycopg

    return psycopg.connect(_database_url())


def _ensure_migrations_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def _migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _applied_versions(conn) -> set[str]:
    _ensure_migrations_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def migrate():
    files = _migration_files()
    if not files:
        raise SystemExit("No hay migraciones en migrations/.")

    with _connect() as conn:
        applied = _applied_versions(conn)
        pending = [path for path in files if path.name not in applied]
        if not pending:
            print("Base de datos al dia. No hay migraciones pendientes.")
            return

        for path in pending:
            sql = path.read_text(encoding="utf-8")
            print(f"Aplicando migracion {path.name}...")
            with conn.transaction():
                conn.execute(sql)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
        print(f"Migraciones aplicadas: {len(pending)}")


def status():
    files = _migration_files()
    with _connect() as conn:
        applied = _applied_versions(conn)
    print("Estado de migraciones:")
    for path in files:
        marker = "aplicada" if path.name in applied else "pendiente"
        print(f"- {path.name}: {marker}")


def reset(force: bool):
    if not force:
        raise SystemExit("Reset requiere --yes para evitar borrar datos por accidente.")
    with _connect() as conn:
        with conn.transaction():
            conn.execute("DROP TABLE IF EXISTS trace_events CASCADE")
            conn.execute("DROP TABLE IF EXISTS conversation_messages CASCADE")
            conn.execute("DROP TABLE IF EXISTS conversations CASCADE")
            conn.execute("DROP TABLE IF EXISTS schema_migrations CASCADE")
    print("Base de datos reseteada.")


def main():
    parser = argparse.ArgumentParser(description="Gestion de base de datos MachineTwin")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("migrate", help="Aplica migraciones pendientes")
    subparsers.add_parser("status", help="Muestra migraciones aplicadas y pendientes")
    reset_parser = subparsers.add_parser("reset", help="Borra tablas de desarrollo")
    reset_parser.add_argument("--yes", action="store_true", help="Confirma el borrado de datos")
    args = parser.parse_args()

    if args.command == "migrate":
        migrate()
    elif args.command == "status":
        status()
    elif args.command == "reset":
        reset(force=args.yes)


if __name__ == "__main__":
    main()
