# Scraping Web Vacantes CDMX

Proyecto de scraping y generacion de reportes automatizados sobre vacantes de `data` en Ciudad de Mexico usando OCC Mexico como fuente principal.

El flujo del proyecto esta dividido en dos etapas:

1. `scrape_occ_cdmx.py` obtiene y filtra las vacantes.
2. `generate_occ_report.py` toma la corrida mas reciente y construye un reporte con graficas incrustadas.

## Objetivo

Monitorear vacantes de data en CDMX, filtrar oportunidades con mejor compensacion y generar reportes automaticos para seguimiento historico.

## Caracteristicas

- Scraping automatizado de OCC Mexico.
- Enfoque en vacantes de data en CDMX.
- Filtro salarial minimo de `17,000 MXN`.
- Guardado diario por fecha en formato `31May26`.
- Evita volver a procesar la misma fecha si ya existe una corrida guardada.
- Generacion de reportes HTML con graficas insertadas.
- Generacion de un resumen en texto con conclusiones.

## Estructura del proyecto

| Archivo o carpeta | Proposito |
|---|---|
| `scrape_occ_cdmx.py` | Script principal: scrapea, filtra, analiza y guarda salidas |
| `generate_occ_report.py` | Toma la corrida mas reciente y genera un reporte automatizado |
| `requirements.txt` | Dependencias del proyecto |
| `.gitignore` | Archivos y carpetas que no deben subirse al repositorio |
| `runs/` | Salidas diarias generadas por el scraper |
| `reports/` | Reportes automatizados con graficas y conclusiones |

## Flujo de trabajo

| Paso | Entrada | Salida |
|---|---|---|
| 1 | Pagina de OCC | Vacantes crudas de tecnologia en CDMX |
| 2 | Vacantes crudas | Vacantes con salario >= `17,000 MXN` |
| 3 | Vacantes filtradas | Vacantes de data con salario >= `17,000 MXN` |
| 4 | Ultima corrida guardada | Reporte HTML, graficas y resumen TXT |

## Inputs

| Input | Descripcion | Formato |
|---|---|---|
| URL base de OCC | Pagina de vacantes de tecnologia en CDMX | HTML |
| HTML de cada pagina | Contenido de las tarjetas de vacante | HTML |
| Campos extraidos | `title`, `company`, `location`, `salary_text`, `benefits`, `job_url` | Texto / CSV |
| Corrida mas reciente | Carpeta dentro de `runs/` | CSV |

## Outputs

| Output | Descripcion | Ubicacion |
|---|---|---|
| `occ_tech_cdmx_raw.json` | Vacantes completas scrapeadas | `runs/DDMonYY/` |
| `occ_tech_cdmx_raw.csv` | Tabla cruda de vacantes | `runs/DDMonYY/` |
| `occ_tech_cdmx_17000plus.csv` | Vacantes con salario >= `17,000 MXN` | `runs/DDMonYY/` |
| `occ_tech_cdmx_data_17000plus.csv` | Vacantes de data con salario >= `17,000 MXN` | `runs/DDMonYY/` |
| `occ_tech_cdmx_summary.txt` | Resumen de la corrida diaria | `runs/DDMonYY/` |
| `DONE.flag` | Marca de corrida ya ejecutada | `runs/DDMonYY/` |
| `DDMonYY_reporte.html` | Reporte automatizado con graficas incrustadas | `reports/DDMonYY/` |
| `DDMonYY_conclusiones.txt` | Conclusiones en texto | `reports/DDMonYY/` |
| `figures/*.png` | Graficas del reporte | `reports/DDMonYY/figures/` |

## Metodos

| Metodo | Uso |
|---|---|
| `requests` | Descarga del HTML de OCC |
| `BeautifulSoup` | Extraccion de tarjetas y campos de vacantes |
| `pandas` | Limpieza, filtrado, analisis y exportacion de CSV |
| `matplotlib` | Graficas de barras e histogramas |
| `seaborn` | Visualizacion de distribuciones salariales |
| `HTML + base64` | Insercion de graficas dentro del reporte |

## Instalacion

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

### Ejecutar el scraping

```powershell
python scrape_occ_cdmx.py
```

### Generar el reporte

```powershell
python generate_occ_report.py
```

El reporte se construye a partir de la corrida mas reciente dentro de `runs/` y se guarda en `reports/` con el mismo identificador de fecha.

## Criterios de filtrado

- Ubicacion: Ciudad de Mexico.
- Sector: data.
- Salario minimo: `17,000 MXN`.

## Reporte automatizado

El generador crea:

- un HTML con graficas incrustadas,
- un resumen textual con conclusiones,
- una tabla con las vacantes mejor posicionadas,
- y una carpeta de imagenes para inspeccion rapida.

## Preguntas que responde el reporte

1. Que empresas dominan el mercado?
2. Que tecnologias se repiten mas?
3. Cual es el rango salarial mas comun?
4. Que vacantes aparecen mejor posicionadas dentro del filtro aplicado?

## Comportamiento diario

- El scraper guarda una corrida por fecha.
- Si la corrida del dia ya existe, no se vuelve a ejecutar.
- El generador de reporte siempre toma la ultima corrida disponible.

## Uso, intenciones y limites

Este proyecto esta pensado para analisis personal, academico y de portafolio. Su proposito es observar vacantes publicas, generar reportes y comparar tendencias del mercado laboral en CDMX.

### Uso previsto

- Analizar vacantes publicas del sector `data` en Ciudad de Mexico.
- Generar reportes automaticos para seguimiento de empresas, salarios y tecnologias.
- Revisar la evolucion de vacantes guardadas por fecha.

### Limites del proyecto

- No almacenar ni redistribuir datos personales sensibles.
- No usar el proyecto para spam, reventa de datos o abuso de acceso.
- No presentarlo como un producto oficial ni afiliado a OCC.
- No intentar evadir restricciones tecnicas o de uso de la fuente original.
- No reutilizar contenido crudo como si fuera informacion propia sin revisar los terminos aplicables.

### Criterios de cumplimiento

- Trabaja solo con informacion publicamente visible.
- Mantiene filtros para reducir recoleccion innecesaria.
- Evita guardar informacion personal no necesaria para el analisis.
- Revisa los terminos del sitio origen antes de ampliar el alcance.

## Dependencias

| Paquete | Uso |
|---|---|
| `requests` | Descarga de paginas web |
| `pandas` | Manejo y analisis de datos |
| `numpy` | Soporte numerico |
| `python-dotenv` | Preparado para variables de entorno |
| `beautifulsoup4` | Parseo de HTML |
| `matplotlib` | Graficas para el reporte automatizado |
| `seaborn` | Visualizaciones estadisticas |

## Notas

- El proyecto esta pensado para seguimiento de vacantes de data en CDMX.
- Las salidas estan organizadas para facilitar analisis historico y publicacion en GitHub.
