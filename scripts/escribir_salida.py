"""Lee de stdin el JSON {fichero: contenido} que imprime un extractor y lo escribe en el
directorio indicado (los ficheros que empiezan por "_" son metadatos -> data/_meta/)."""
import json, os, sys

dest = sys.argv[1] if len(sys.argv) > 1 else "data"
datos = json.loads(sys.stdin.read().strip().splitlines()[-1])
for nombre, contenido in datos.items():
    ruta = os.path.join(dest, "_meta", nombre[1:]) if nombre.startswith("_") else os.path.join(dest, nombre)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(contenido)
    print(f"escrito {ruta}", file=sys.stderr)
