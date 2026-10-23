"""Register real public snapshots in local Zetaris. No model requests."""
import argparse
from pathlib import Path
import subprocess
from catalogue import ROOT, Zetaris

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose-dir", type=Path, default=Path("C:/zetaris-platform"))
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    destination = "/home/zetaris/customer-data/shared/doublescheck-v1"
    # Writes only a dedicated new data folder, never changes Docker settings or existing datasets.
    subprocess.run(["docker", "compose", "exec", "-T", "driver", "mkdir", "-p", destination],
                   cwd=args.compose_dir, check=True, capture_output=True)
    subprocess.run(["docker", "compose", "cp", str(ROOT / "data/zetaris") + "/.", "driver:" + destination],
                   cwd=args.compose_dir, check=True, capture_output=True)
    api = Zetaris(args.env_file)
    statements = ["CREATE LIGHTNING DATABASE DOUBLES_CHECK DESCRIBE BY \"Public Pokemon and historical VGC data\" OPTIONS ()"]
    statements += [f'CREATE LIGHTNING FILESTORE TABLE {table} FROM DOUBLES_CHECK FORMAT csv '
                   f'OPTIONS (path "file://{destination}/{table}", header "true")'
                   for table in ("pokedex", "vgc_usage", "reference")]
    try:
        for statement in statements:
            try:
                api.query(statement)
                print("Registered:", statement.split(" OPTIONS")[0].split(" FORMAT")[0])
            except FileExistsError:
                print("Existing DoublesCheck registration retained.")
        print("Zetaris row counts:", api.query("SELECT COUNT(*) FROM DOUBLES_CHECK.pokedex"))
    finally:
        api.session.close()

if __name__ == "__main__":
    main()
