# Scraping Web Vacantes CDMX

Proyecto para monitorear en tiempo real el sector `data` en Ciudad de Mexico usando web scraping sobre OCC Mexico.

El objetivo es identificar vacantes relevantes para un perfil matematico, con foco en:

- salarios de al menos `17,000 MXN`
- puestos de `data` y analitica
- seguimiento de empresas, tecnologias y tendencias salariales
- guardado diario de resultados sin sobrescribir ejecuciones del mismo dia

## Caracteristicas

- Scraping automatico de vacantes en OCC Mexico
- Filtro salarial minimo de `17,000 MXN`
- Deteccion de vacantes orientadas a `data`
- Analisis de empresas, salarios y tecnologias
- Generacion de salidas diarias en una carpeta con fecha
- Bloqueo de re-ejecucion dentro del mismo dia
- Compatible con ejecucion manual o programada al iniciar Windows

## Estructura del Proyecto

| Archivo / Carpeta | Proposito |
|---|---|
| `scrape_occ_cdmx.py` | Script principal: scrapea, filtra, analiza y guarda salidas |
| `requirements.txt` | Dependencias del proyecto |
| `.gitignore` | Archivos y carpetas que no deben subirse al repositorio |
| `runs/` | Salidas diarias generadas por el scraper |

## Flujo

| Etapa | Descripcion |
|---|---|
| 1 | Se consulta OCC Mexico para tecnologia en Ciudad de Mexico |
| 2 | Se extraen vacantes pagina por pagina |
| 3 | Se normalizan salarios, empresas y ubicaciones |
| 4 | Se filtra por salario minimo y por roles de `data` |
| 5 | Se genera un resumen y se guarda todo en una carpeta con fecha |

## Inputs

| Input | Tipo | Descripcion |
|---|---|---|
| OCC Mexico | Fuente web | Listado publico de vacantes de tecnologia en CDMX |
| `BASE_URL` | Configuracion | URL base del scraping |
| `MAX_PAGES` | Configuracion | Numero maximo de paginas a recorrer |
| `MIN_SALARY_MXN` | Configuracion | Piso salarial para filtrar vacantes |
| `DATA_ROLE_KEYWORDS` | Configuracion | Palabras clave para detectar roles de data |

## Outputs

| Output | Formato | Descripcion |
|---|---|---|
| `runs/DDMonYY/occ_tech_cdmx_raw.json` | JSON | Datos crudos del scraping |
| `runs/DDMonYY/occ_tech_cdmx_raw.csv` | CSV | Tabla completa de vacantes |
| `runs/DDMonYY/occ_tech_cdmx_17000plus.csv` | CSV | Vacantes con salario >= 17k |
| `runs/DDMonYY/occ_tech_cdmx_data_17000plus.csv` | CSV | Vacantes de data con salario >= 17k |
| `runs/DDMonYY/occ_tech_cdmx_summary.txt` | TXT | Conclusiones del analisis diario |
| `runs/DDMonYY/DONE.flag` | Flag | Marca para evitar re-ejecucion el mismo dia |

## Metodos

| Metodo | Funcion |
|---|---|
| `fetch_html()` | Descarga el HTML de una pagina de OCC |
| `extract_job_url_map()` | Lee el JSON-LD para obtener URLs reales de vacantes |
| `parse_cards()` | Extrae datos de cada tarjeta de vacante |
| `salary_to_range()` | Convierte salario textual a valores numericos |
| `is_data_role()` | Detecta si una vacante corresponde al sector data |
| `math_value_score()` | Prioriza vacantes con mejor encaje para perfil matematico |
| `build_summary_text()` | Genera el texto de conclusiones del dia |
| `main()` | Ejecuta todo el flujo y guarda las salidas |

## Requisitos

- Python 3.8+
- Conexion a internet

## Instalacion

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion

```powershell
python scrape_occ_cdmx.py
```

## Comportamiento diario

El script crea una carpeta con la fecha actual, por ejemplo:

```text
runs\31May26
```

Si el script ya se ejecuto ese dia, no vuelve a scrapear y termina con un mensaje indicando la carpeta disponible.

## Dependencias

| Paquete | Uso |
|---|---|
| `requests` | Descarga de paginas web |
| `pandas` | Manejo y analisis de datos |
| `numpy` | Soporte numerico |
| `python-dotenv` | Preparado para variables de entorno |
| `beautifulsoup4` | Parseo de HTML |

## Nota

Este proyecto no esta enfocado en TI general. Esta enfocado en el submercado `data` en CDMX, con interes especial en puestos mejor pagados y mas cercanos a un perfil matematico.
