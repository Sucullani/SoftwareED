# -*- coding: utf-8 -*-
"""
armar_narracion.py -- junta la narración de todos los grupos en narracion_final4.json.

Cada grupo de láminas deja su narración en herramientas/narracion/<grupo>.json:
    [ {"id": "caja-negra", "narracion": ["texto del paso 0", "texto del paso 1", ...]}, ... ]
Este guion la ordena como las láminas de la presentación (laminas/NN_*.html), comprueba que
cada lámina principal tenga exactamente un texto por paso (pasos + 1, según el motor, vía
listar.mjs) y escribe herramientas/narracion_final4.json, que lee sintetizar_voz.py.
Las láminas de respaldo no se narran.

Uso (desde la raíz del repositorio):
    .venv\\Scripts\\python.exe tesis\\presentacion\\final4\\herramientas\\armar_narracion.py [--html=Defensa_EduFEM.html]
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(AQUI)
SALIDA = os.path.join(AQUI, "narracion_final4.json")
HTML = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--html=")), "Defensa_EduFEM.html")

CABECERA = {
    "voz": "es-BO-MarceloNeural",
    "rate": "+0%",
    "pausa_s": 1.0,
    "nota": ("Un texto por paso de cada lámina (paso 0, 1, 2...). Se escribe con ortografía normal: "
             "sintetizar_voz.py lo convierte para la voz (cifras en palabras, Q4 -> Q cuatro, σx -> sigma "
             "equis). El mismo texto alimenta las notas del orador y los subtítulos. No se edita a mano: "
             "sale de herramientas/narracion/*.json con armar_narracion.py."),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    textos = {}
    for f in sorted(glob.glob(os.path.join(AQUI, "narracion", "*.json"))):
        with open(f, encoding="utf-8") as fh:
            for item in json.load(fh):
                if item["id"] in textos:
                    raise SystemExit(f"{os.path.basename(f)}: la lámina {item['id']} ya tiene narración en otro archivo")
                textos[item["id"]] = item["narracion"]
    salida = subprocess.run(["node", os.path.join(AQUI, "listar.mjs"), "--json", f"--html={HTML}"],
                            capture_output=True, text=True, encoding="utf-8", cwd=FINAL)
    if salida.returncode != 0:
        raise SystemExit(salida.stderr)
    laminas = json.loads(salida.stdout.strip().splitlines()[-1])
    errores, orden = [], []
    for L in laminas:
        if L["respaldo"]:
            continue
        t = textos.get(L["id"])
        if t is None:
            errores.append(f"{L['id']}: sin narración")
            continue
        if len(t) != L["pasos"] + 1:
            errores.append(f"{L['id']}: {len(t)} textos para {L['pasos'] + 1} pasos")
        if any(not s.strip() for s in t):
            errores.append(f"{L['id']}: hay un paso con texto vacío")
        orden.append({"id": L["id"], "pasos": t})
    sobran = set(textos) - {L["id"] for L in laminas if not L["respaldo"]}
    sobran = {s for s in sobran if textos[s]}
    if sobran:
        errores.append(f"narración de láminas que no están en el recorrido: {sorted(sobran)}")
    if errores:
        print("\n".join("  [!] " + e for e in errores))
        raise SystemExit(1)
    with open(SALIDA, "w", encoding="utf-8") as fh:
        json.dump({**CABECERA, "laminas": orden}, fh, ensure_ascii=False, indent=1)
    palabras = sum(len(s.split()) for l in orden for s in l["pasos"])
    pasos = sum(len(l["pasos"]) for l in orden)
    print(f"[OK] {os.path.relpath(SALIDA, FINAL)} · {len(orden)} láminas · {pasos} pasos · {palabras} palabras")


if __name__ == "__main__":
    main()
