"""Genera datapackage.json (Frictionless Data Package v1) a partir de los CSV de data/."""
import json, os, hashlib, csv

R = os.path.join(os.path.dirname(__file__), "..")
S = lambda n, t, d, **k: {"name": n, "type": t, "description": d, **k}
MES = S("mes", "yearmonth", "Mes natural (AAAA-MM) de la fecha de referencia del registro.")
N = lambda n, d: S(n, "integer", d, constraints={"minimum": 0})
EUR = lambda n, d: S(n, "number", d, constraints={"minimum": 0})
REC = {
 "convocatorias_por_mes": ("Convocatorias publicadas en la BDNS por mes de recepción y ámbito de la administración convocante.", [
   MES, S("ambito", "string", "Nivel de la administración convocante: Estatal, Autonómico, Local u Otros (universidades, organismos y otros entes).",
          constraints={"enum": ["Autonómico", "Estatal", "Local", "Otros"]}),
   N("n_convocatorias", "Número de convocatorias registradas."),
   EUR("presupuesto_total_eur", "Suma del presupuesto total publicado (€) de las convocatorias que lo informan. Ver limitaciones de cobertura."),
   N("n_con_presupuesto", "Convocatorias con presupuesto informado (base de la suma anterior)."),
   N("n_mrr", "Convocatorias marcadas en la BDNS como financiadas por el Mecanismo de Recuperación y Resiliencia (Next Generation EU).")], ["mes", "ambito"]),
 "convocatorias_por_ccaa_mes": ("Convocatorias por mes y comunidad o ciudad autónoma (NUTS2) de su ámbito geográfico.", [
   MES, S("nuts2", "string", "Código NUTS2 (NUTS 2021) de la comunidad o ciudad autónoma.", constraints={"pattern": "ES[1-7][0-9]"}),
   S("comunidad", "string", "Nombre de la comunidad o ciudad autónoma."),
   N("n_convocatorias", "Convocatorias cuyo ámbito geográfico incluye la comunidad (una vez por comunidad)."),
   N("n_multiccaa", "De ellas, cuántas abarcan además otras comunidades (se cuentan también en esas)."),
   EUR("presupuesto_total_eur", "Suma del presupuesto total de esas convocatorias. Las multi-CCAA suman su presupuesto completo en cada comunidad."),
   N("n_con_presupuesto", "Convocatorias con presupuesto informado.")], ["mes", "nuts2"]),
 "convocatorias_por_procedimiento_mes": ("Convocatorias por mes y tipo de procedimiento BDNS (tipoConvocatoria). Cobertura parcial: solo meses con dato.", [
   MES, S("tipo_convocatoria", "string", "Tipo de convocatoria según la BDNS."),
   N("n_convocatorias", "Convocatorias de ese tipo."), EUR("presupuesto_total_eur", "Suma del presupuesto total publicado (€)."),
   N("n_con_presupuesto", "Convocatorias con presupuesto informado."),
   N("n_convocatorias_mes_con_tipo", "Convocatorias del mes con el tipo informado (denominador de la cobertura)."),
   N("n_convocatorias_mes_total", "Total de convocatorias del mes (igual que la suma de convocatorias_por_mes)."),
   S("cobertura_tipo_pct", "number", "Porcentaje de convocatorias del mes con tipo informado.")], ["mes", "tipo_convocatoria"]),
 "concesiones_por_mes": ("Concesiones de ayudas registradas en la BDNS por mes de concesión e instrumento.", [
   MES, S("instrumento", "string", "Instrumento de ayuda según la BDNS (subvención, préstamo, garantía, ventaja fiscal...)."),
   N("n_concesiones", "Número de concesiones."), EUR("importe_total_eur", "Suma del importe concedido (€)."),
   EUR("ayuda_equivalente_total_eur", "Suma de la ayuda equivalente (€) cuando la BDNS la informa (relevante en préstamos y garantías)."),
   N("dias_con_concesiones", "Días naturales distintos del mes con al menos una concesión de ese instrumento.")], ["mes", "instrumento"]),
 "top_organos_concedentes_anual": ("50 órganos que más importe han concedido en cada año natural.", [
   S("anio", "year", "Año natural de la fecha de concesión."), N("posicion", "Puesto en el ranking anual por importe."),
   S("organo", "string", "Órgano concedente tal como lo publica la BDNS (niveles 2 y 3 concatenados)."),
   N("n_concesiones", "Número de concesiones del órgano en el año."), EUR("importe_total_eur", "Importe total concedido (€)."),
   S("pct_importe_anio", "number", "Porcentaje del importe total concedido ese año."),
   N("n_administraciones", "Administraciones de primer nivel detectadas tras ese nombre de órgano; >1 indica homónimos de distintas administraciones agregados bajo el mismo nombre.")], ["anio", "posicion"]),
 "top_beneficiarios_personas_juridicas_anual": ("100 personas jurídicas que más importe han recibido en cada año natural. Excluye cualquier persona física.", [
   S("anio", "year", "Año natural de la fecha de concesión."), N("posicion", "Puesto en el ranking anual por importe."),
   S("nif", "string", "NIF de la persona jurídica (formato CIF).", constraints={"pattern": "[ABCDFGNPQRSUVW][0-9]{7}[0-9A-J]"}),
   S("beneficiario", "string", "Denominación del beneficiario tal como figura en la BDNS."),
   N("n_concesiones", "Número de concesiones recibidas en el año."), EUR("importe_total_eur", "Importe total recibido (€)."),
   N("n_organos", "Órganos concedentes distintos.")], ["anio", "posicion"]),
}
res = []
for nombre, (desc, campos, pk) in REC.items():
    ruta = f"data/{nombre}.csv"
    p = os.path.join(R, ruta)
    if not os.path.exists(p):
        continue
    b = open(p, "rb").read()
    res.append({"name": nombre.replace("_", "-"), "path": ruta, "title": nombre.replace("_", " ").capitalize(),
                "description": desc, "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
                "bytes": len(b), "hash": "sha256:" + hashlib.sha256(b).hexdigest(),
                "dialect": {"delimiter": ",", "header": True},
                "schema": {"fields": campos, "primaryKey": pk}})
pkg = {
 "profile": "tabular-data-package", "name": "ayudaspilot-datos-subvenciones",
 "title": "Datos abiertos de AyudasPilot: subvenciones y ayudas públicas en España (agregados de la BDNS)",
 "description": "Series agregadas de convocatorias y concesiones de subvenciones publicadas en la Base de Datos Nacional de Subvenciones (BDNS), elaboradas por AyudasPilot. Solo agregados; sin datos de personas físicas.",
 "homepage": "https://ayudaspilot.com/observatorio", "version": open(os.path.join(R, "data/_meta/VERSION")).read().strip(),
 "created": "2026-11-20T00:00:00Z", "language": "es",
 "keywords": ["subvenciones", "ayudas públicas", "BDNS", "España", "datos abiertos", "Next Generation", "transparencia"],
 "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/", "title": "Creative Commons Attribution 4.0"}],
 "sources": [{"title": "Base de Datos Nacional de Subvenciones (BDNS) - Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas, IGAE",
              "path": "https://www.infosubvenciones.es/bdnstrans/GE/es/inicio"}],
 "contributors": [{"title": "AyudasPilot", "path": "https://ayudaspilot.com", "role": "author"}],
 "resources": res}
json.dump(pkg, open(os.path.join(R, "datapackage.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"datapackage.json con {len(res)} recursos")
