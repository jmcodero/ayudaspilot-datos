"""Extrae agregados de CONCESIONES de AyudasPilot (tabla `concesiones`, origen BDNS).

Se ejecuta DENTRO del contenedor `api` de AyudasPilot:
    docker compose -f docker-compose.prod.yml exec -T api python - < extraer_concesiones.py

Solo lectura (transacción READ ONLY, solo SELECT con GROUP BY en SQL; nunca se
traen filas individuales a Python). Imprime por stdout un JSON {nombre_fichero: csv}.

PROTECCIÓN DE DATOS: el ranking de beneficiarios incluye ÚNICAMENTE NIF de personas
jurídicas, validados con una lista blanca de letras iniciales y formato exacto de
CIF (letra + 7 dígitos + control). Se excluyen las letras de personas físicas
(K, L, M, X, Y, Z, y los DNI que empiezan por dígito), los NIF enmascarados por la
BDNS (***1234**), y por prudencia también E (comunidades de bienes, herencias
yacentes), J (sociedades civiles) y H (comunidades de propietarios), entidades sin
personalidad jurídica plena cuyo nombre puede contener el de personas físicas.
Variables opcionales: MES_DESDE, MES_HASTA (YYYY-MM).
"""
import csv, io, json, os
from datetime import date
from sqlalchemy import text
from app.database import SessionLocal

hoy = date.today()
_ult = date(hoy.year, hoy.month, 1)
MES_HASTA = os.environ.get("MES_HASTA") or (
    f"{_ult.year - 1}-12" if _ult.month == 1 else f"{_ult.year}-{_ult.month - 1:02d}")
# El histórico cargado empieza el 18-mar-2025: marzo de 2025 es parcial y se excluye
# de la serie mensual; sí cuenta en el año 2025 de los rankings (con su fecha_desde).
MES_DESDE = os.environ.get("MES_DESDE") or "2025-04"
CIF_PJ = r"^[ABCDFGNPQRSUVW][0-9]{7}[0-9A-J]$"

db = SessionLocal()
db.execute(text("SET TRANSACTION READ ONLY"))
db.execute(text("SET LOCAL statement_timeout = '30min'"))
P = {"desde": MES_DESDE + "-01", "hasta": MES_HASTA + "-01", "cif": CIF_PJ}
FIN = "CAST(:hasta AS date) + INTERVAL '1 month'"


def q(sql):
    return db.execute(text(sql), P).fetchall()


def to_csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(["" if v is None else (round(float(v), 2) if hasattr(v, "as_integer_ratio") and not isinstance(v, int) else v) for v in r])
    return buf.getvalue()


out = {}

# 1) Concesiones por mes e instrumento.
rows = q(f"""
SELECT to_char(fecha_concesion, 'YYYY-MM') AS mes,
       COALESCE(NULLIF(trim(instrumento), ''), 'SIN INFORMAR') AS instrumento,
       count(*) AS n_concesiones,
       round(COALESCE(sum(importe), 0)::numeric, 2) AS importe_total_eur,
       round(COALESCE(sum(ayuda_equivalente), 0)::numeric, 2) AS ayuda_equivalente_total_eur,
       count(DISTINCT fecha_concesion) AS dias_con_concesiones
FROM concesiones
WHERE fecha_concesion >= CAST(:desde AS date) AND fecha_concesion < {FIN}
GROUP BY 1, 2 ORDER BY 1, 2""")
out["concesiones_por_mes.csv"] = to_csv(
    ["mes", "instrumento", "n_concesiones", "importe_total_eur", "ayuda_equivalente_total_eur", "dias_con_concesiones"], rows)

# Rango anual de los rankings: desde el primer dato cargado hasta el fin de MES_HASTA.
mn_all, mx_all, n_all = q("SELECT min(fecha_concesion), max(fecha_concesion), count(*) FROM concesiones")[0]
P["ini"] = str(mn_all)

# 2) Top 50 órganos concedentes por año natural. La BDNS da en la concesión solo el
# último nivel del órgano: nombres genéricos («DIRECCIÓN GENERAL DE DESARROLLO RURAL»)
# agrupan órganos homónimos de varias administraciones. `n_administraciones` (de la
# tabla organo_stats de AyudasPilot) indica cuántas administraciones de 1.er nivel se
# han detectado tras ese nombre cruzando con las convocatorias; >1 = homónimos fusionados.
rows = q(f"""
WITH a AS (
  SELECT extract(year FROM fecha_concesion)::int AS anio, organo,
         count(*) AS n, COALESCE(sum(importe), 0) AS imp
  FROM concesiones
  WHERE fecha_concesion >= CAST(:ini AS date) AND fecha_concesion < {FIN} AND organo IS NOT NULL
  GROUP BY 1, 2),
r AS (SELECT *, row_number() OVER (PARTITION BY anio ORDER BY imp DESC, organo) AS pos FROM a),
t AS (SELECT anio, sum(imp) AS imp_anio, sum(n) AS n_anio FROM a GROUP BY 1)
SELECT r.anio, r.pos, trim(r.organo), r.n, round(r.imp::numeric, 2),
       round((100 * r.imp / NULLIF(t.imp_anio, 0))::numeric, 2),
       os.n_administraciones
FROM r JOIN t USING (anio)
LEFT JOIN organo_stats os ON os.organo = r.organo
WHERE r.pos <= 50 ORDER BY r.anio, r.pos""")
out["top_organos_concedentes_anual.csv"] = to_csv(
    ["anio", "posicion", "organo", "n_concesiones", "importe_total_eur", "pct_importe_anio", "n_administraciones"], rows)

# 3) Top 100 beneficiarios PERSONAS JURÍDICAS por año natural (ver docstring).
rows = q(f"""
WITH b AS (
  SELECT extract(year FROM fecha_concesion)::int AS anio,
         split_part(beneficiario, ' ', 1) AS nif,
         substr(beneficiario, length(split_part(beneficiario, ' ', 1)) + 2) AS nombre,
         importe, organo
  FROM concesiones
  WHERE fecha_concesion >= CAST(:ini AS date) AND fecha_concesion < {FIN}
    AND split_part(beneficiario, ' ', 1) ~ :cif),
a AS (
  SELECT anio, nif, max(nombre) AS nombre, count(*) AS n,
         COALESCE(sum(importe), 0) AS imp, count(DISTINCT organo) AS n_org
  FROM b GROUP BY 1, 2),
r AS (SELECT *, row_number() OVER (PARTITION BY anio ORDER BY imp DESC, nif) AS pos FROM a)
SELECT anio, pos, nif, trim(nombre), n, round(imp::numeric, 2), n_org
FROM r WHERE pos <= 100 ORDER BY anio, pos""")
out["top_beneficiarios_personas_juridicas_anual.csv"] = to_csv(
    ["anio", "posicion", "nif", "beneficiario", "n_concesiones", "importe_total_eur", "n_organos"], rows)

# Metadatos: rangos y totales anuales para validar los rankings.
anual = q(f"""
SELECT extract(year FROM fecha_concesion)::int, min(fecha_concesion), max(fecha_concesion),
       count(*), round(COALESCE(sum(importe), 0)::numeric, 2)
FROM concesiones WHERE fecha_concesion >= CAST(:ini AS date) AND fecha_concesion < {FIN}
GROUP BY 1 ORDER BY 1""")
out["_meta_concesiones.json"] = json.dumps({
    "rango_meses_serie": [MES_DESDE, MES_HASTA],
    "fecha_min_tabla": str(mn_all), "fecha_max_tabla": str(mx_all), "n_tabla": n_all,
    "anual": [{"anio": a, "fecha_min": str(f1), "fecha_max": str(f2), "n": n, "importe": float(i)}
              for a, f1, f2, n, i in anual],
    "regex_cif_personas_juridicas": CIF_PJ, "extraido": str(hoy)}, ensure_ascii=False)
db.rollback()
print(json.dumps(out, ensure_ascii=False))
