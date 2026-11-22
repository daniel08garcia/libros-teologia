# Copia plan.json (de watson-preparar.py) al manifiesto.json que crea "sermones.js dividir".
# No toca "titulo" si ya tiene valor. Uso: python temp/trabajo/watson-manifiesto.py
import io, json
W = "temp/trabajo/watson"
plan = json.load(io.open(f"{W}/plan.json", encoding="utf-8"))
m = json.load(io.open(f"{W}/manifiesto.json", encoding="utf-8"))
assert len(plan) == len(m["sermones"]), (len(plan), len(m["sermones"]))
m["comun"]["autor"] = "Thomas Watson"
for p, s in zip(plan, m["sermones"]):
    assert s["encabezado_en"][:40] == p["inicio"][:40], (s["clave"], s["encabezado_en"][:40], p["inicio"][:40])
    s["autor"] = "Thomas Watson"
    s["destino"], s["fecha"], s["id"] = p["destino"], p["fecha"], p["id"]
    s["saltar_parrafos"] = p["saltar"]
    s["versiculo"] = p["versiculo"]
    s["titulo_original"] = p["titulo_original"]
io.open(f"{W}/manifiesto.json", "w", encoding="utf-8", newline="\n").write(json.dumps(m, ensure_ascii=False, indent=1) + "\n")
print("manifiesto actualizado:", len(plan), "sermones")
