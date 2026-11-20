# Datos abiertos de AyudasPilot: subvenciones públicas en España

Series **agregadas** de convocatorias y concesiones de subvenciones y ayudas públicas en España, elaboradas por [AyudasPilot](https://ayudaspilot.com) a partir de la **Base de Datos Nacional de Subvenciones (BDNS)**. Están pensadas para periodistas, investigadores y reutilizadores que necesiten cifras mensuales y anuales listas para usar, sin tener que descargar millones de registros.

- Se actualiza automáticamente el día 2 de cada mes. La fecha de corte de cada versión está en `datapackage.json` (campo `version`) y en `data/_meta/`. Las series mensuales terminan en el último mes completo.
- Formato: CSV UTF-8, separador coma, con cabecera. Descritos en [`datapackage.json`](datapackage.json) ([Frictionless Data](https://specs.frictionlessdata.io/)).
- Licencia: [CC BY 4.0](LICENSE).
- Más contexto: [ayudaspilot.com](https://ayudaspilot.com) · [Prensa](https://ayudaspilot.com/prensa) · [Metodología](https://ayudaspilot.com/metodologia) · [Observatorio](https://ayudaspilot.com/observatorio)

## Cómo citar

> Fuente: AyudasPilot (ayudaspilot.com), a partir de la Base de Datos Nacional de Subvenciones (BDNS)

Si es posible, enlaza a https://ayudaspilot.com/observatorio e indica la fecha de corte del conjunto (campo `version` de `datapackage.json`).

## Ficheros y cobertura medida

| Fichero | Contenido | Cobertura medida | Filas | Tamaño |
|---|---|---|---|---|
| [`data/convocatorias_por_mes.csv`](data/convocatorias_por_mes.csv) | Convocatorias por mes y ámbito | ene-2024 a oct-2026 (fechas de recepción del 02-01-2024 al 30-10-2026) | 136 | 5,0 KB |
| [`data/convocatorias_por_ccaa_mes.csv`](data/convocatorias_por_ccaa_mes.csv) | Convocatorias por mes y comunidad autónoma (NUTS2) | ene-2024 a oct-2026 | 646 | 29,4 KB |
| [`data/convocatorias_por_procedimiento_mes.csv`](data/convocatorias_por_procedimiento_mes.csv) | Convocatorias por mes y tipo de procedimiento | jul-2026 a oct-2026 (cobertura parcial, ver abajo) | 12 | 1,1 KB |
| [`data/concesiones_por_mes.csv`](data/concesiones_por_mes.csv) | Concesiones por mes e instrumento | abr-2025 a oct-2026 | 89 | 5,7 KB |
| [`data/top_organos_concedentes_anual.csv`](data/top_organos_concedentes_anual.csv) | Top 50 órganos concedentes por año | 2025 (18-03 a 31-12) y 2026 (01-01 a 31-10) | 100 | 8,2 KB |
| [`data/top_beneficiarios_personas_juridicas_anual.csv`](data/top_beneficiarios_personas_juridicas_anual.csv) | Top 100 beneficiarios **personas jurídicas** por año | 2025 (18-03 a 31-12) y 2026 (01-01 a 31-10) | 200 | 13,5 KB |

Volumen subyacente agregado: **195.292 convocatorias** (2024-2026) y **16,68 millones de concesiones** (18-03-2025 a 31-10-2026) por importe de **70.560 millones de euros**.

**Por qué empiezan ahí.** El histórico de convocatorias de AyudasPilot arranca el 18-12-2023; diciembre de 2023 está incompleto y se excluye. El histórico de concesiones arranca el 18-03-2025; marzo de 2025 se excluye de la serie mensual, pero se incluye en el ranking de 2025. Por eso **no hay datos anteriores a 2024** (convocatorias) **ni a 2025** (concesiones): no los publicamos porque no los tenemos completos. Los años 2025 y 2026 de los rankings **no son años completos**: compáralos con cautela.

## Metodología

1. **Fuente.** La BDNS es el registro oficial de las convocatorias y concesiones de subvenciones y ayudas públicas de todas las administraciones españolas (Estado, comunidades autónomas, entidades locales y otros organismos). La gestiona la Intervención General de la Administración del Estado (IGAE) y se publica en el [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es). AyudasPilot la importa a diario mediante su API pública.
2. **Agregación.** Las cifras se calculan con consultas SQL de solo lectura (`GROUP BY`) sobre la base de datos de AyudasPilot. Nunca se exportan registros individuales. Los scripts están en [`scripts/`](scripts/).
3. **Fechas.** En las convocatorias se usa la *fecha de recepción* en la BDNS (`fechaRecepcion`); en las concesiones, la *fecha de concesión*. Mes y año son naturales.
4. **Comunidades autónomas.** El ámbito geográfico de cada convocatoria lo da la BDNS como lista de regiones NUTS de distintos niveles (`ES61 - ANDALUCIA`, `ES511 - Barcelona`, `ES3 - COMUNIDAD DE MADRID`...). Se normaliza a NUTS2 así: los códigos de nivel 2 y 3 se reducen a sus 4 primeros caracteres; `ES3` pasa a `ES30` (Madrid) y `ES7` a `ES70` (Canarias), porque esas regiones NUTS1 contienen una sola comunidad. No se asignan a ninguna comunidad `ES` (toda España), las macrorregiones NUTS1 que abarcan varias comunidades (`ES1`, `ES2`, `ES5`, `ES6`), `ESZ` (extrarregional) ni los códigos de otros países. Cada convocatoria se cuenta **una vez por comunidad**.
5. **Rankings.** Se ordenan por importe concedido en el año natural. Los órganos son el texto del órgano concedente que publica la BDNS en cada concesión. Los beneficiarios se agrupan por NIF.

## Protección de datos: por qué no hay personas físicas

Este repositorio **no contiene datos de personas físicas**:

- Las series de convocatorias y concesiones son recuentos y sumas: no identifican a nadie.
- El ranking de beneficiarios incluye **solo** NIF con formato exacto de persona jurídica: una letra inicial de la lista blanca `A B C D F G N P Q R S U V W`, siete dígitos y un carácter de control (expresión regular `^[ABCDFGNPQRSUVW][0-9]{7}[0-9A-J]$`). Esto excluye:
  - los DNI (empiezan por dígito) y los NIE (`X`, `Y`, `Z`);
  - los NIF especiales de personas físicas (`K`, `L`, `M`);
  - los NIF que la BDNS publica enmascarados (`***1234**`), que son la mayoría de las personas físicas;
  - los identificadores extranjeros de otros formatos;
  - por prudencia, también `E` (comunidades de bienes y herencias yacentes), `J` (sociedades civiles) y `H` (comunidades de propietarios). Son entidades sin personalidad jurídica plena y su denominación suele contener nombres de personas.
- Se revisaron a mano las 200 denominaciones del ranking: son empresas, universidades, administraciones y organismos públicos, fundaciones, cooperativas, asociaciones, partidos políticos y organismos internacionales.

Una persona jurídica puede llevar el nombre de una persona física (por ejemplo, «Juan Pérez, S.L.»). Aun así sigue siendo una persona jurídica y su información de concesiones es pública conforme a la normativa de publicidad de subvenciones. Si detectas un error, abre una incidencia o escribe a través de [ayudaspilot.com/prensa](https://ayudaspilot.com/prensa).

## Limitaciones (léelas antes de publicar una cifra)

1. **El presupuesto solo es comparable desde julio de 2026.** El presupuesto total publicado procede del detalle de cada convocatoria en la BDNS. AyudasPilot solo lo tiene para una parte del histórico: el 0,4 % de las convocatorias de 2024, el 1,4 % de las de 2025 y el 50 % de las de 2026. Por mes, la cobertura pasa del 9 % en enero de 2026 al 84 % en julio y al 100 % desde agosto. Antes de julio de 2026, `presupuesto_total_eur` suma unas pocas convocatorias, sesgadas hacia las grandes: por ejemplo, los 19.190 M€ de 2024 salen de solo 298 convocatorias. **Usa siempre `n_con_presupuesto` como denominador y no compares presupuestos entre años.**
2. **Presupuestos plurianuales.** El presupuesto de una convocatoria es el total publicado, que puede cubrir varios ejercicios. Se imputa entero al mes de publicación, así que no equivale a gasto anual ni a lo efectivamente concedido.
3. **Cobertura parcial del tipo de procedimiento.** El campo `tipoConvocatoria` (concurrencia competitiva, concesión directa canónica o instrumental) solo está disponible en las convocatorias cuyo detalle se ha extraído: 29,6 % en jul-2026, 93,3 % en ago-2026, 98,7 % en sep-2026 y 16,3 % en oct-2026 (en proceso). Antes de julio de 2026 no hay dato y esos meses no aparecen. La columna `cobertura_tipo_pct` da la cobertura de cada mes. Los repartos son proporciones **dentro de las convocatorias con tipo**, no del total, y la muestra puede no ser aleatoria, porque se priorizó extraer las convocatorias candidatas a mostrarse en el buscador.
4. **Convocatorias en varias comunidades.** El 94,6 % de las convocatorias del periodo se asigna a una sola comunidad. Un pequeño grupo abarca varias (1.527 asignaciones con `n_multiccaa` > 0) y cuenta en cada una de ellas. El resto, en torno al 5 %, no se asigna a ninguna (ámbito estatal o extranjero). Por eso:
   - la **suma de convocatorias por comunidad** no supera el total mensual en ningún mes (comprobado en los 34), pero **no es** un total nacional;
   - la **suma de presupuesto por comunidad** puede superar el total nacional, porque el presupuesto completo de una convocatoria multirregional se cuenta en cada comunidad. Ocurre en 3 meses: abr-2025, mar-2026 y ago-2026. Para sumar comunidades sin doble cómputo, resta las convocatorias `n_multiccaa`.
5. **Registros con retraso.** Las administraciones registran en la BDNS con semanas o meses de retraso, sobre todo las concesiones. **Los últimos meses de cada serie están infrarrepresentados** y se revisarán al alza en próximas versiones. Las concesiones de jul-2026 a nov-2026 se completaron en AyudasPilot el 19-20 de noviembre de 2026.
6. **Recuentos de concesiones dominados por ayudas masivas.** Un registro de la BDNS es una concesión a un beneficiario. Algunas líneas generan millones de registros de importe pequeño. El caso principal es la subvención al transporte aéreo de residentes (Dirección General de Aviación Civil: unos 4,8 millones de concesiones en 2026). Para comparar meses, `importe_total_eur` es más estable que `n_concesiones`. Los picos de diciembre reflejan el cierre del ejercicio.
7. **Instrumentos.** El 99,7 % de las concesiones y el 91 % del importe (abr-2025 a oct-2026) son subvenciones. En préstamos y garantías, `importe_total_eur` es el nominal y `ayuda_equivalente_total_eur` el equivalente de subvención, cuando la BDNS lo informa.
8. **Órganos homónimos.** En cada concesión, la BDNS solo da el último nivel del órgano concedente. Nombres genéricos como «Dirección General de Política Agraria Comunitaria» o «Consejería de Educación» agrupan órganos de **distintas administraciones**. La columna `n_administraciones` lo señala (>1 = homónimos fusionados): afecta a 7 de las 100 filas del ranking de órganos.
9. **MRR / Next Generation.** `n_mrr` refleja la marca `mrr` que publica la BDNS en cada convocatoria. AyudasPilot no la verifica de forma independiente. Su caída en 2026 es coherente con el fin del Mecanismo de Recuperación y Resiliencia (agosto de 2026), pero no hemos comprobado que la marca esté igual de completa en todo el histórico.
10. **Ámbito «Otros».** Agrupa universidades, organismos y entidades que la BDNS no clasifica como estatales, autonómicos ni locales.

## Diccionario de campos

### `convocatorias_por_mes.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| `mes` | AAAA-MM | Mes de recepción de la convocatoria en la BDNS |
| `ambito` | texto | `Estatal`, `Autonómico`, `Local` u `Otros` |
| `n_convocatorias` | entero | Convocatorias registradas |
| `presupuesto_total_eur` | número (€) | Suma del presupuesto total publicado de las que lo informan |
| `n_con_presupuesto` | entero | Convocatorias con presupuesto informado (base de la suma) |
| `n_mrr` | entero | Convocatorias marcadas como financiadas por el MRR (Next Generation EU) |

### `convocatorias_por_ccaa_mes.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| `mes` | AAAA-MM | Mes de recepción |
| `nuts2` | texto | Código NUTS2 (NUTS 2021) de la comunidad o ciudad autónoma |
| `comunidad` | texto | Nombre de la comunidad o ciudad autónoma |
| `n_convocatorias` | entero | Convocatorias cuyo ámbito geográfico incluye la comunidad |
| `n_multiccaa` | entero | De ellas, las que abarcan además otras comunidades |
| `presupuesto_total_eur` | número (€) | Presupuesto total de esas convocatorias (las multirregionales cuentan entero en cada comunidad) |
| `n_con_presupuesto` | entero | Convocatorias con presupuesto informado |

### `convocatorias_por_procedimiento_mes.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| `mes` | AAAA-MM | Mes de recepción |
| `tipo_convocatoria` | texto | `Concurrencia competitiva - canónica`, `Concesión directa - canónica` o `Concesión directa - instrumental` (convenios, nominativas y concesiones a una entidad concreta, que no se pueden solicitar) |
| `n_convocatorias` | entero | Convocatorias de ese tipo |
| `presupuesto_total_eur` | número (€) | Suma del presupuesto publicado |
| `n_con_presupuesto` | entero | Convocatorias con presupuesto informado |
| `n_convocatorias_mes_con_tipo` | entero | Convocatorias del mes con tipo informado |
| `n_convocatorias_mes_total` | entero | Total de convocatorias del mes |
| `cobertura_tipo_pct` | número | % del mes con tipo informado |

### `concesiones_por_mes.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| `mes` | AAAA-MM | Mes de la fecha de concesión |
| `instrumento` | texto | Instrumento según la BDNS: subvención, préstamo, garantía, ventaja fiscal, aportación de financiación de riesgo u otros |
| `n_concesiones` | entero | Número de concesiones |
| `importe_total_eur` | número (€) | Importe concedido |
| `ayuda_equivalente_total_eur` | número (€) | Ayuda equivalente, cuando se informa |
| `dias_con_concesiones` | entero | Días del mes con al menos una concesión de ese instrumento (control de huecos) |

### `top_organos_concedentes_anual.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| `anio` | año | Año natural de concesión |
| `posicion` | entero | Puesto por importe (1 a 50) |
| `organo` | texto | Órgano concedente según la BDNS |
| `n_concesiones` | entero | Concesiones en el año |
| `importe_total_eur` | número (€) | Importe concedido en el año |
| `pct_importe_anio` | número | % sobre el importe total concedido ese año |
| `n_administraciones` | entero | Administraciones de primer nivel tras ese nombre (>1 = homónimos agregados) |

### `top_beneficiarios_personas_juridicas_anual.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| `anio` | año | Año natural de concesión |
| `posicion` | entero | Puesto por importe (1 a 100) |
| `nif` | texto | NIF de la persona jurídica |
| `beneficiario` | texto | Denominación en la BDNS (si un NIF tiene varias grafías, se muestra una) |
| `n_concesiones` | entero | Concesiones recibidas en el año |
| `importe_total_eur` | número (€) | Importe recibido en el año |
| `n_organos` | entero | Órganos concedentes distintos |

## Validaciones aplicadas

`scripts/validar.py` comprueba en cada regeneración:

- cabeceras exactas, sin filas vacías, columnas completas, numéricos no negativos y meses bien formados y contiguos;
- subtotales coherentes: `n_con_presupuesto` y `n_mrr` ≤ `n_convocatorias`; la suma por tipo de procedimiento = `n_convocatorias_mes_con_tipo`; y `n_convocatorias_mes_total` = total de `convocatorias_por_mes`;
- comunidades: las convocatorias asignadas a una sola comunidad nunca superan el total del mes;
- rankings: posiciones 1..N, orden decreciente, sin NIF duplicados, y suma del top ≤ importe total del año;
- beneficiarios: el 100 % de los NIF cumple el patrón de persona jurídica y ninguno empieza por letra o dígito de persona física ni está enmascarado.

## Regenerar los datos

```bash
AP_SSH_HOST=usuario@servidor AP_SSH_KEY=~/.ssh/clave ./scripts/regenerar.sh      # todo
./scripts/regenerar.sh convocatorias   # o solo una parte
```

Los extractores (`scripts/extraer_*.py`) se ejecutan dentro del contenedor de la API de AyudasPilot, en una transacción `READ ONLY`. Imprimen un JSON que `scripts/escribir_salida.py` vuelca en `data/`. Después se validan los CSV (`validar.py`) y se regenera `datapackage.json`. El repositorio no contiene credenciales. Los metadatos de cada extracción (fechas mín./máx. reales) quedan en `data/_meta/`.

## Licencia

Datos y documentación bajo [CC BY 4.0](LICENSE). Los datos de origen son de la BDNS (IGAE), reutilizables según la Ley 37/2007 de reutilización de la información del sector público citando la fuente.
