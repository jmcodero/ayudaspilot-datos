"""Extrae agregados de CONVOCATORIAS de AyudasPilot (tabla `subsidies`, origen BDNS).

Se ejecuta DENTRO del contenedor `api` de AyudasPilot (usa su conexión a la BD):
    docker compose -f docker-compose.prod.yml exec -T api python - < extraer_convocatorias.py

Solo lectura: abre la transacción en modo READ ONLY y únicamente lanza SELECT
agregados (GROUP BY en SQL). Imprime por stdout un JSON {nombre_fichero: csv}.
Parámetros por variables de entorno (opcionales): MES_DESDE (YYYY-MM), MES_HASTA (YYYY-MM).
Por defecto: primer mes completo con datos -> último mes completo anterior al de hoy.
"""
import csv, io, json, os, sys
from datetime import date
from sqlalchemy import text
from app.database import SessionLocal

hoy = date.today()
_ult = date(hoy.year, hoy.month, 1)
MES_HASTA = os.environ.get("MES_HASTA") or (
    f"{_ult.year - 1}-12" if _ult.month == 1 else f"{_ult.year}-{_ult.month - 1:02d}")
MES_DESDE = os.environ.get("MES_DESDE") or "2024-01"  # dic-2023 está incompleto (datos desde el 18-dic)

# Nombres oficiales NUTS2 (NUTS 2021) de las comunidades y ciudades autónomas.
NUTS2 = {
    "ES11": "Galicia", "ES12": "Principado de Asturias", "ES13": "Cantabria",
    "ES21": "País Vasco", "ES22": "Comunidad Foral de Navarra", "ES23": "La Rioja",
    "ES24": "Aragón", "ES30": "Comunidad de Madrid", "ES41": "Castilla y León",
    "ES42": "Castilla-La Mancha", "ES43": "Extremadura", "ES51": "Cataluña",
    "ES52": "Comunitat Valenciana", "ES53": "Illes Balears", "ES61": "Andalucía",
    "ES62": "Región de Murcia", "ES63": "Ciudad Autónoma de Ceuta",
    "ES64": "Ciudad Autónoma de Melilla", "ES70": "Canarias",
}

db = SessionLocal()
db.execute(text("SET TRANSACTION READ ONLY"))
P = {"desde": MES_DESDE + "-01", "hasta": MES_HASTA + "-01"}
RANGO = ("fecha_recepcion >= CAST(:desde AS date) "
         "AND fecha_recepcion < CAST(:hasta AS date) + INTERVAL '1 month'")


def q(sql):
    return db.execute(text(sql), P).fetchall()


def to_csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(["" if v is None else (round(v, 2) if isinstance(v, float) else v) for v in r])
    return buf.getvalue()


out = {}

# 1) Convocatorias por mes y ámbito.
rows = q(f"""
SELECT to_char(fecha_recepcion, 'YYYY-MM') AS mes, ambito,
       count(*) AS n_convocatorias,
       COALESCE(round(sum(presupuesto)::numeric, 2), 0) AS presupuesto_total_eur,
       count(presupuesto) AS n_con_presupuesto,
       count(*) FILTER (WHERE mrr) AS n_mrr
FROM subsidies WHERE {RANGO}
GROUP BY 1, 2 ORDER BY 1, 2""")
out["convocatorias_por_mes.csv"] = to_csv(
    ["mes", "ambito", "n_convocatorias", "presupuesto_total_eur", "n_con_presupuesto", "n_mrr"],
    [(r[0], r[1], r[2], float(r[3]), r[4], r[5]) for r in rows])

# 2) Por comunidad autónoma (NUTS2). Cada valor de `region` es "CÓDIGO - NOMBRE" con
# códigos NUTS de distinto nivel. Se normaliza a NUTS2: ESxx y ESxxx -> 4 primeros
# caracteres; ES3 (NUTS1 = solo Madrid) -> ES30; ES7 (NUTS1 = solo Canarias) -> ES70.
# ES (España), NUTS1 plurirregionales (ES1, ES2, ES5, ES6), ESZ y extranjeros no se asignan.
# Una convocatoria se cuenta una sola vez por comunidad (DISTINCT), pero puede
# contar en varias comunidades si su ámbito geográfico abarca más de una.
rows = q(f"""
WITH reg AS (
  SELECT DISTINCT s.id, to_char(s.fecha_recepcion, 'YYYY-MM') AS mes, s.presupuesto,
         CASE
           WHEN c ~ '^ES[1-7][0-9][0-9A-Z]?$' THEN substr(c, 1, 4)
           WHEN c = 'ES3' THEN 'ES30'
           WHEN c = 'ES7' THEN 'ES70'
         END AS nuts2
  FROM subsidies s,
       LATERAL (SELECT trim(split_part(r, ' - ', 1)) AS c
                FROM json_array_elements_text(s.region::json) r) x
  WHERE {RANGO.replace('fecha_recepcion', 's.fecha_recepcion')}
), ok AS (SELECT * FROM reg WHERE nuts2 IS NOT NULL),
multi AS (SELECT id FROM ok GROUP BY id HAVING count(*) > 1)
SELECT mes, nuts2, count(*) AS n_convocatorias,
       count(*) FILTER (WHERE id IN (SELECT id FROM multi)) AS n_multiccaa,
       COALESCE(round(sum(presupuesto)::numeric, 2), 0) AS presupuesto_total_eur,
       count(presupuesto) AS n_con_presupuesto
FROM ok GROUP BY 1, 2 ORDER BY 1, 2""")
desconocidos = sorted({r[1] for r in rows} - set(NUTS2))
if desconocidos:
    sys.exit(f"Códigos NUTS2 no reconocidos: {desconocidos}")
out["convocatorias_por_ccaa_mes.csv"] = to_csv(
    ["mes", "nuts2", "comunidad", "n_convocatorias", "n_multiccaa", "presupuesto_total_eur", "n_con_presupuesto"],
    [(r[0], r[1], NUTS2[r[1]], r[2], r[3], float(r[4]), r[5]) for r in rows])

# 3) Por tipo de procedimiento (tipo_convocatoria), solo meses con dato. Incluye la
# cobertura: convocatorias del mes con tipo informado / total del mes.
rows = q(f"""
WITH m AS (
  SELECT to_char(fecha_recepcion, 'YYYY-MM') AS mes, count(*) AS total,
         count(tipo_convocatoria) AS con_tipo
  FROM subsidies WHERE {RANGO} GROUP BY 1)
SELECT to_char(s.fecha_recepcion, 'YYYY-MM') AS mes, s.tipo_convocatoria,
       count(*) AS n_convocatorias,
       COALESCE(round(sum(s.presupuesto)::numeric, 2), 0) AS presupuesto_total_eur,
       count(s.presupuesto) AS n_con_presupuesto,
       m.con_tipo, m.total
FROM subsidies s JOIN m ON m.mes = to_char(s.fecha_recepcion, 'YYYY-MM')
WHERE {RANGO.replace('fecha_recepcion', 's.fecha_recepcion')} AND s.tipo_convocatoria IS NOT NULL
GROUP BY 1, 2, m.con_tipo, m.total ORDER BY 1, 2""")
out["convocatorias_por_procedimiento_mes.csv"] = to_csv(
    ["mes", "tipo_convocatoria", "n_convocatorias", "presupuesto_total_eur", "n_con_presupuesto",
     "n_convocatorias_mes_con_tipo", "n_convocatorias_mes_total", "cobertura_tipo_pct"],
    [(r[0], r[1], r[2], float(r[3]), r[4], r[5], r[6], round(100.0 * r[5] / r[6], 1)) for r in rows])

# Metadatos de cobertura (fechas mín./máx. reales dentro del rango).
mn, mx, n = q(f"SELECT min(fecha_recepcion), max(fecha_recepcion), count(*) FROM subsidies WHERE {RANGO}")[0]
mn_all, mx_all = q("SELECT min(fecha_recepcion), max(fecha_recepcion) FROM subsidies")[0]
mt = q(f"SELECT min(fecha_recepcion), max(fecha_recepcion) FROM subsidies WHERE {RANGO} AND tipo_convocatoria IS NOT NULL")[0]
out["_meta_convocatorias.json"] = json.dumps({
    "rango_meses": [MES_DESDE, MES_HASTA], "fecha_min": str(mn), "fecha_max": str(mx), "n": n,
    "fecha_min_tabla": str(mn_all), "fecha_max_tabla": str(mx_all),
    "tipo_fecha_min": str(mt[0]), "tipo_fecha_max": str(mt[1]),
    "extraido": str(hoy)}, ensure_ascii=False)
db.rollback()
print(json.dumps(out, ensure_ascii=False))
