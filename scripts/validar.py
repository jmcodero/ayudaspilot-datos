"""Valida los CSV de data/: cabeceras, filas vacías, tipos, coherencia de totales y
ausencia de personas físicas en el ranking de beneficiarios. Sale con código 1 si
algún control BLOQUEANTE falla; los avisos (coherencia esperada) se imprimen."""
import csv, json, os, re, sys
from collections import defaultdict

D = os.path.join(os.path.dirname(__file__), "..", "data")
CAB = {
    "convocatorias_por_mes.csv": ["mes", "ambito", "n_convocatorias", "presupuesto_total_eur", "n_con_presupuesto", "n_mrr"],
    "convocatorias_por_ccaa_mes.csv": ["mes", "nuts2", "comunidad", "n_convocatorias", "n_multiccaa", "presupuesto_total_eur", "n_con_presupuesto"],
    "convocatorias_por_procedimiento_mes.csv": ["mes", "tipo_convocatoria", "n_convocatorias", "presupuesto_total_eur", "n_con_presupuesto",
                                                "n_convocatorias_mes_con_tipo", "n_convocatorias_mes_total", "cobertura_tipo_pct"],
    "concesiones_por_mes.csv": ["mes", "instrumento", "n_concesiones", "importe_total_eur", "ayuda_equivalente_total_eur", "dias_con_concesiones"],
    "top_organos_concedentes_anual.csv": ["anio", "posicion", "organo", "n_concesiones", "importe_total_eur", "pct_importe_anio", "n_administraciones"],
    "top_beneficiarios_personas_juridicas_anual.csv": ["anio", "posicion", "nif", "beneficiario", "n_concesiones", "importe_total_eur", "n_organos"],
}
NUM = {"n_convocatorias", "presupuesto_total_eur", "n_con_presupuesto", "n_mrr", "n_multiccaa", "n_concesiones",
       "importe_total_eur", "ayuda_equivalente_total_eur", "dias_con_concesiones", "posicion", "anio", "n_organos",
       "n_convocatorias_mes_con_tipo", "n_convocatorias_mes_total", "cobertura_tipo_pct", "pct_importe_anio", "n_administraciones"}
errores, avisos, ok = [], [], []


def leer(nombre):
    ruta = os.path.join(D, nombre)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8", newline="") as f:
        lineas = f.read().split("\n")
    if lineas and lineas[-1] == "":
        lineas = lineas[:-1]
    vacias = [i + 1 for i, l in enumerate(lineas) if not l.strip() or not l.strip(",")]
    if vacias:
        errores.append(f"{nombre}: filas vacías en líneas {vacias[:10]}")
    filas = list(csv.DictReader(lineas))
    cab = lineas[0].split(",")
    if cab != CAB[nombre]:
        errores.append(f"{nombre}: cabecera {cab} != esperada {CAB[nombre]}")
    for i, f in enumerate(filas, 2):
        if None in f or any(v is None for v in f.values()):
            errores.append(f"{nombre}:{i} nº de columnas incorrecto")
            continue
        for k, v in f.items():
            if k in NUM and not (k == "n_administraciones" and v == ""):
                try:
                    x = float(v)
                    if x < 0:
                        errores.append(f"{nombre}:{i} {k} negativo")
                except ValueError:
                    errores.append(f"{nombre}:{i} {k}='{v}' no numérico")
            elif k != "tipo_convocatoria" and not v.strip() and k != "n_administraciones":
                errores.append(f"{nombre}:{i} {k} vacío")
        if "mes" in f and not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", f["mes"]):
            errores.append(f"{nombre}:{i} mes mal formado {f['mes']}")
    ok.append(f"{nombre}: {len(filas)} filas, cabecera OK, sin filas vacías" if not any(e.startswith(nombre) for e in errores) else f"{nombre}: ERRORES")
    return filas


def meses_contiguos(nombre, meses):
    ms = sorted(set(meses))
    y, m = map(int, ms[0].split("-"))
    esperado = []
    while f"{y}-{m:02d}" <= ms[-1]:
        esperado.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    faltan = sorted(set(esperado) - set(ms))
    (errores if faltan else ok).append(f"{nombre}: meses {ms[0]}..{ms[-1]}" + (f" FALTAN {faltan}" if faltan else " contiguos"))


cm = leer("convocatorias_por_mes.csv")
if cm:
    meses_contiguos("convocatorias_por_mes.csv", [f["mes"] for f in cm])
    tot = defaultdict(lambda: [0, 0.0])
    for f in cm:
        tot[f["mes"]][0] += int(f["n_convocatorias"]); tot[f["mes"]][1] += float(f["presupuesto_total_eur"])
        if int(f["n_con_presupuesto"]) > int(f["n_convocatorias"]) or int(f["n_mrr"]) > int(f["n_convocatorias"]):
            errores.append(f"convocatorias_por_mes: {f['mes']} {f['ambito']} subtotal > total")
        if int(f["n_con_presupuesto"]) == 0 and float(f["presupuesto_total_eur"]) != 0:
            errores.append(f"convocatorias_por_mes: {f['mes']} presupuesto sin convocatorias con presupuesto")

    cc = leer("convocatorias_por_ccaa_mes.csv")
    if cc:
        meses_contiguos("convocatorias_por_ccaa_mes.csv", [f["mes"] for f in cc])
        s = defaultdict(lambda: [0, 0, 0.0])
        for f in cc:
            s[f["mes"]][0] += int(f["n_convocatorias"]); s[f["mes"]][1] += int(f["n_multiccaa"]); s[f["mes"]][2] += float(f["presupuesto_total_eur"])
            if int(f["n_multiccaa"]) > int(f["n_convocatorias"]):
                errores.append(f"ccaa: {f['mes']} {f['nuts2']} n_multiccaa > n_convocatorias")
        exceden = [m for m in s if s[m][0] > tot[m][0]]
        # Sin las multi-CCAA, la suma por comunidad (convocatorias únicas monorregión) nunca puede exceder el total.
        imposibles = [m for m in s if s[m][0] - s[m][1] > tot[m][0]]
        if imposibles:
            errores.append(f"ccaa: convocatorias monorregión > total del mes en {imposibles}")
        else:
            ok.append("ccaa: en todos los meses, convocatorias asignadas a una sola CCAA <= total del mes")
        ok.append(f"ccaa: meses en que la suma por CCAA (con multirregión) supera el total: {len(exceden)} de {len(s)}")
        pres_exc = [m for m in s if s[m][2] > tot[m][1] + 0.01]
        avisos.append(f"ccaa: meses en que la suma de presupuesto por CCAA supera el total nacional (doble cómputo multi-CCAA): {len(pres_exc)} {pres_exc[:6]}")
        ratio = sum(s[m][0] - s[m][1] for m in s) / sum(tot[m][0] for m in s)
        ok.append(f"ccaa: {ratio:.1%} de las convocatorias del periodo se asignan a una única CCAA")

    cp = leer("convocatorias_por_procedimiento_mes.csv")
    if cp:
        porm = defaultdict(int)
        for f in cp:
            porm[f["mes"]] += int(f["n_convocatorias"])
            if int(f["n_convocatorias_mes_total"]) != tot[f["mes"]][0]:
                errores.append(f"procedimiento: {f['mes']} total del mes {f['n_convocatorias_mes_total']} != convocatorias_por_mes {tot[f['mes']][0]}")
        for f in cp:
            if porm[f["mes"]] != int(f["n_convocatorias_mes_con_tipo"]):
                errores.append(f"procedimiento: {f['mes']} suma por tipo != n con tipo")
        ok.append(f"procedimiento: suma por tipo == nº con tipo y total == convocatorias_por_mes en {len(porm)} meses ({min(porm)}..{max(porm)})")

meta = {}
mp = os.path.join(D, "_meta", "meta_concesiones.json")
if os.path.exists(mp):
    meta = {a["anio"]: a for a in json.load(open(mp))["anual"]}

co = leer("concesiones_por_mes.csv")
if co:
    meses_contiguos("concesiones_por_mes.csv", [f["mes"] for f in co])
    dias = defaultdict(int)
    for f in co:
        dias[f["mes"]] = max(dias[f["mes"]], int(f["dias_con_concesiones"]))
    pocos = {m: d for m, d in dias.items() if d < 15}
    (avisos if pocos else ok).append(f"concesiones: meses con <15 días con concesiones: {pocos}")
    anio_tot = defaultdict(float)
    for f in co:
        anio_tot[int(f["mes"][:4])] += float(f["importe_total_eur"])

to = leer("top_organos_concedentes_anual.csv")
if to:
    por = defaultdict(list)
    for f in to:
        por[int(f["anio"])].append(f)
    for a, fs in por.items():
        if len(fs) > 50 or [int(f["posicion"]) for f in fs] != list(range(1, len(fs) + 1)):
            errores.append(f"organos {a}: posiciones no 1..N<=50")
        imps = [float(f["importe_total_eur"]) for f in fs]
        if imps != sorted(imps, reverse=True):
            errores.append(f"organos {a}: no ordenado por importe")
        if a in meta and sum(imps) > meta[a]["importe"] + 0.01:
            errores.append(f"organos {a}: suma top50 > total anual")
        elif a in meta:
            ok.append(f"organos {a}: top {len(fs)} suma {sum(imps)/1e9:.2f} mil M€ <= total año {meta[a]['importe']/1e9:.2f} mil M€ ({100*sum(imps)/meta[a]['importe']:.1f}%)")

tb = leer("top_beneficiarios_personas_juridicas_anual.csv")
if tb:
    patron = re.compile(r"^[ABCDFGNPQRSUVW][0-9]{7}[0-9A-J]$")
    malos = [f["nif"] for f in tb if not patron.fullmatch(f["nif"])]
    fisicas = [f["nif"] for f in tb if f["nif"][:1] in "KLMXYZ0123456789" or "*" in f["nif"]]
    (errores if malos or fisicas else ok).append(
        f"beneficiarios: {len(tb)} filas; NIF fuera de patrón CIF persona jurídica: {len(malos)}; con letra/forma de persona física o enmascarados: {len(fisicas)}")
    por = defaultdict(list)
    for f in tb:
        por[int(f["anio"])].append(f)
    for a, fs in por.items():
        if len(fs) > 100 or len({f['nif'] for f in fs}) != len(fs):
            errores.append(f"beneficiarios {a}: >100 filas o NIF duplicados")
        s = sum(float(f["importe_total_eur"]) for f in fs)
        if a in meta and s > meta[a]["importe"] + 0.01:
            errores.append(f"beneficiarios {a}: suma > total anual")
        elif a in meta:
            ok.append(f"beneficiarios {a}: top {len(fs)} suma {s/1e9:.2f} mil M€ ({100*s/meta[a]['importe']:.1f}% del importe del año)")

for t, l in (("OK", ok), ("AVISO", avisos), ("ERROR", errores)):
    for x in l:
        print(f"[{t}] {x}")
sys.exit(1 if errores else 0)
