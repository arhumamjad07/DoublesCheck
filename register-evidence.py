"""Register separate queryable Evidence Lens tables; never replace Demo 3's tables."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from catalogue import ROOT, Zetaris
from zetaris_schema import DATABASE, DESTINATION, FIELDS


def register(compose_dir, env_file):
    manifest = json.loads((ROOT / "data/zetaris-lens/manifest.json").read_text(encoding="utf-8"))
    for table in FIELDS:
        file = ROOT / "data/zetaris-lens" / table / "data.csv"
        if hashlib.sha256(file.read_bytes()).hexdigest() != manifest["tables"][table]["sha256"]:
            raise RuntimeError("Normalised source file hash mismatch; registration stopped.")
    subprocess.run(["docker","compose","exec","-T","driver","mkdir","-p",DESTINATION],cwd=compose_dir,check=True,capture_output=True)
    # Copy only the five reviewed public table folders, never settings or run history.
    for table in FIELDS:
        subprocess.run(["docker","compose","cp",str(ROOT / "data/zetaris-lens" / table),"driver:"+DESTINATION+"/"],
                       cwd=compose_dir,check=True,capture_output=True)
    api = Zetaris(env_file)
    statements = [f'CREATE LIGHTNING DATABASE {DATABASE} DESCRIBE BY "DoublesCheck pinned historical evidence v1" OPTIONS ()']
    statements += [f'CREATE LIGHTNING FILESTORE TABLE {table} FROM {DATABASE} FORMAT csv '
                   f'OPTIONS (path "file://{DESTINATION}/{table}", header "true")' for table in FIELDS]
    try:
        for sql in statements:
            try: api.query(sql)
            except FileExistsError: pass
        from zetaris_partners import verify_tables
        verify_tables(api, [], manifest)
        print("Evidence tables registered and row counts verified; Demo 3 tables retained.")
    finally: api.session.close()


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--compose-dir",type=Path,default=Path("C:/zetaris-platform"))
    p.add_argument("--env-file",type=Path,default=ROOT/".env")
    args=p.parse_args();register(args.compose_dir,args.env_file)
