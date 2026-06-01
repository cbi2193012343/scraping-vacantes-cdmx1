from __future__ import annotations

import base64
import html
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = ROOT_DIR / "runs"
REPORTS_DIR = ROOT_DIR / "reports"
MIN_SALARY_MXN = 17000

TECH_KEYWORDS = [
    "python",
    "sql",
    "power bi",
    "tableau",
    "excel",
    "aws",
    "azure",
    "gcp",
    "databricks",
    "spark",
    "etl",
    "bi",
    "machine learning",
    "ml",
    "data science",
    "data engineer",
    "data analyst",
    "analytics",
    "statistics",
    "r",
    "docker",
    "kubernetes",
    "linux",
    "airflow",
    "dbt",
    "forecasting",
    "risk",
    "fraud",
]

MATH_PROFILE_KEYWORDS = [
    "data science",
    "data scientist",
    "machine learning",
    "data engineer",
    "data analyst",
    "business intelligence",
    "bi",
    "power bi",
    "analytics",
    "sql",
    "python",
    "statistics",
    "statistical",
    "forecasting",
    "risk",
    "fraud",
    "causal",
    "experiment",
    "a/b",
    "modeling",
    "optimization",
]


def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str, keywords: list[str]) -> list[str]:
    normalized = normalize_text(text)
    return [keyword for keyword in keywords if keyword in normalized]


def math_value_score(row: pd.Series) -> int:
    text = " ".join(
        [
            str(row.get("title", "")),
            str(row.get("company", "")),
            str(row.get("location", "")),
            str(row.get("benefits", "")),
        ]
    )
    text = normalize_text(text)
    score = 0

    for keyword in MATH_PROFILE_KEYWORDS:
        if keyword in text:
            score += 2

    salary_min = row.get("salary_min")
    if pd.notna(salary_min):
        if salary_min >= 30000:
            score += 3
        elif salary_min >= 20000:
            score += 2
        elif salary_min >= MIN_SALARY_MXN:
            score += 1

    if "senior" in text or "sr" in text:
        score += 2
    if "jr" in text or "junior" in text:
        score -= 1
    if "becario" in text or "trainee" in text or "practicante" in text:
        score -= 3

    return score


def latest_run_dir(runs_dir: Path) -> Path:
    if not runs_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de corridas: {runs_dir}")

    candidates = [item for item in runs_dir.iterdir() if item.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No hay carpetas de corrida dentro de: {runs_dir}")

    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0]


def load_run_data(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_path = run_dir / "occ_tech_cdmx_raw.csv"
    salary_path = run_dir / "occ_tech_cdmx_17000plus.csv"
    data_path = run_dir / "occ_tech_cdmx_data_17000plus.csv"

    for path in (raw_path, salary_path, data_path):
        if not path.exists():
            raise FileNotFoundError(f"Falta el archivo esperado: {path}")

    raw_df = pd.read_csv(raw_path)
    salary_df = pd.read_csv(salary_path)
    data_df = pd.read_csv(data_path)
    return raw_df, salary_df, data_df


def ensure_output_dirs(report_dir: Path) -> tuple[Path, Path]:
    figures_dir = report_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir, figures_dir


def add_analysis_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "title" in result.columns:
        result["title_norm"] = result["title"].apply(normalize_text)
        result["tech_keywords"] = result["title"].apply(lambda value: extract_keywords(str(value), TECH_KEYWORDS))
    else:
        result["title_norm"] = ""
        result["tech_keywords"] = [[] for _ in range(len(result))]

    if "benefits" in result.columns:
        result["benefits_norm"] = result["benefits"].apply(normalize_text)
    else:
        result["benefits_norm"] = ""

    result["math_score"] = result.apply(math_value_score, axis=1)
    return result


def save_plot(fig: plt.Figure, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_top_companies(data_df: pd.DataFrame, figures_dir: Path, date_tag: str) -> Path:
    top_companies = data_df["company"].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    top_companies.sort_values().plot(kind="barh", color="#2E86AB", ax=ax)
    ax.set_title("Top empresas en vacantes de data con salario >= 17k")
    ax.set_xlabel("Cantidad de vacantes")
    ax.set_ylabel("Empresa")
    return save_plot(fig, figures_dir / f"{date_tag}_top_empresas.png")


def plot_salary_distribution(salary_df: pd.DataFrame, figures_dir: Path, date_tag: str) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.histplot(salary_df["salary_min"], bins=20, kde=True, color="#C73E1D", ax=ax)
    ax.set_title("Distribucion de salario minimo")
    ax.set_xlabel("Salario minimo mensual")
    ax.set_ylabel("Vacantes")
    return save_plot(fig, figures_dir / f"{date_tag}_distribucion_salarios.png")


def plot_technologies(data_df: pd.DataFrame, figures_dir: Path, date_tag: str) -> tuple[Path | None, pd.Series]:
    all_techs: list[str] = []
    for tech_list in data_df.get("tech_keywords", []):
        if isinstance(tech_list, list):
            all_techs.extend(tech_list)

    tech_counts = pd.Series(all_techs).value_counts().head(15) if all_techs else pd.Series(dtype=int)
    if tech_counts.empty:
        return None, tech_counts

    fig, ax = plt.subplots(figsize=(12, 6))
    tech_counts.sort_values().plot(kind="barh", color="#3A7D44", ax=ax)
    ax.set_title("Tecnologias mas mencionadas en vacantes de data")
    ax.set_xlabel("Frecuencia")
    ax.set_ylabel("Tecnologia")
    path = save_plot(fig, figures_dir / f"{date_tag}_tecnologias.png")
    return path, tech_counts


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def format_currency(value) -> str:
    if pd.isna(value):
        return "N/D"
    return f"{value:,.0f} MXN"


def write_text_summary(
    txt_path: Path,
    date_tag: str,
    top_companies: pd.Series,
    tech_counts: pd.Series,
    salary_df: pd.DataFrame,
    best_for_math: pd.DataFrame,
) -> None:
    salary_min_median = salary_df["salary_min"].median() if "salary_min" in salary_df.columns else None
    salary_min_mean = salary_df["salary_min"].mean() if "salary_min" in salary_df.columns else None
    salary_max_median = salary_df["salary_max"].median() if "salary_max" in salary_df.columns else None

    with txt_path.open("w", encoding="utf-8") as f:
        f.write(f"Fecha de analisis: {date_tag}\n")
        f.write("=" * 60 + "\n\n")

        f.write("PREGUNTA 1: ¿Qué empresas dominan el mercado?\n")
        for company, count in top_companies.items():
            f.write(f"- {company}: {count} vacantes\n")
        f.write("\n")

        f.write("PREGUNTA 2: ¿Qué tecnologías se repiten más?\n")
        if not tech_counts.empty:
            for tech, count in tech_counts.items():
                f.write(f"- {tech}: {count}\n")
        else:
            f.write("- No se detectaron tecnologias claramente repetidas.\n")
        f.write("\n")

        f.write("PREGUNTA 3: ¿Cuál es el rango salarial más común?\n")
        if pd.notna(salary_min_median):
            f.write(f"- Mediana salario minimo: {format_currency(salary_min_median)}\n")
        if pd.notna(salary_min_mean):
            f.write(f"- Promedio salario minimo: {format_currency(salary_min_mean)}\n")
        if pd.notna(salary_max_median):
            f.write(f"- Mediana salario maximo: {format_currency(salary_max_median)}\n")
        f.write("\n")

        f.write("PREGUNTA 4: ¿Qué vacantes parecen más valiosas para un perfil matemático?\n")
        for _, row in best_for_math.iterrows():
            title = row.get("title", "")
            company = row.get("company", "")
            location = row.get("location", "")
            salary_text = row.get("salary_text", "")
            score = row.get("math_score", 0)
            f.write(f"- [{score}] {title} | {company} | {location} | {salary_text}\n")
        f.write("\n")

        f.write("CONCLUSION GENERAL\n")
        f.write(
            "El mercado de data en CDMX muestra mejor valor en roles como Data Scientist, Data Engineer, "
            "Business Intelligence, Analytics y puestos relacionados con Python, SQL, Power BI y Machine Learning. "
            "Los perfiles junior o de becario suelen quedar por debajo del umbral salarial objetivo.\n"
        )


def render_html_report(
    html_path: Path,
    report_title: str,
    source_run_dir: Path,
    raw_df: pd.DataFrame,
    salary_df: pd.DataFrame,
    data_df: pd.DataFrame,
    top_companies: pd.Series,
    tech_counts: pd.Series,
    salary_min_median: float | None,
    salary_min_mean: float | None,
    salary_max_median: float | None,
    best_for_math: pd.DataFrame,
    plot_paths: list[Path],
) -> None:
    plot_images = []
    for path in plot_paths:
        if path is None:
            continue
        plot_images.append(
            f"""
            <figure class="plot-card">
                <img src="data:image/png;base64,{image_to_base64(path)}" alt="{html.escape(path.stem)}">
                <figcaption>{html.escape(path.name)}</figcaption>
            </figure>
            """
        )

    top_companies_html = "".join(
        f"<li><strong>{html.escape(str(company))}</strong>: {count} vacantes</li>"
        for company, count in top_companies.items()
    )

    tech_counts_html = (
        "".join(
            f"<li><strong>{html.escape(str(tech))}</strong>: {count}</li>"
            for tech, count in tech_counts.items()
        )
        if not tech_counts.empty
        else "<li>No se detectaron tecnologias claramente repetidas.</li>"
    )

    best_jobs_html = "".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('title', '')))}</td>"
        f"<td>{html.escape(str(row.get('company', '')))}</td>"
        f"<td>{html.escape(str(row.get('location', '')))}</td>"
        f"<td>{html.escape(str(row.get('salary_text', '')))}</td>"
        f"<td>{int(row.get('math_score', 0))}</td>"
        "</tr>"
        for _, row in best_for_math.iterrows()
    )

    html_content = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(report_title)}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --panel-2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --accent: #38bdf8;
      --accent-2: #34d399;
      --border: #374151;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
      color: var(--text);
      line-height: 1.5;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      background: rgba(17, 24, 39, 0.88);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
      margin-bottom: 24px;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 2rem;
    }}
    .hero p {{
      margin: 6px 0;
      color: var(--muted);
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 18px 0 8px;
    }}
    .stat {{
      background: rgba(31, 41, 55, 0.96);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
    }}
    .stat .label {{
      display: block;
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 4px;
    }}
    .stat .value {{
      font-size: 1.35rem;
      font-weight: 700;
      color: #fff;
    }}
    .panel {{
      background: rgba(17, 24, 39, 0.94);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 22px;
      margin-bottom: 22px;
    }}
    h2 {{
      margin-top: 0;
      margin-bottom: 16px;
      font-size: 1.3rem;
      color: #fff;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin-bottom: 6px;
    }}
    .plot-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
    }}
    .plot-card {{
      margin: 0;
      background: rgba(31, 41, 55, 0.96);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px;
    }}
    .plot-card img {{
      width: 100%;
      height: auto;
      border-radius: 12px;
      display: block;
    }}
    .plot-card figcaption {{
      color: var(--muted);
      font-size: 0.88rem;
      margin-top: 8px;
      word-break: break-word;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 12px;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: var(--panel-2);
      color: #fff;
      position: sticky;
      top: 0;
    }}
    .small {{
      color: var(--muted);
      font-size: 0.95rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <section class="hero">
      <h1>{html.escape(report_title)}</h1>
      <p>Fuente de datos: <strong>{html.escape(str(source_run_dir))}</strong></p>
      <p class="small">Reporte automatizado de vacantes de data en CDMX con salario >= {MIN_SALARY_MXN:,} MXN.</p>
      <div class="stats">
        <div class="stat"><span class="label">Vacantes totales</span><span class="value">{len(raw_df)}</span></div>
        <div class="stat"><span class="label">Con salario >= 17k</span><span class="value">{len(salary_df)}</span></div>
        <div class="stat"><span class="label">Roles de data</span><span class="value">{len(data_df)}</span></div>
        <div class="stat"><span class="label">Salario mínimo mediana</span><span class="value">{html.escape(format_currency(salary_min_median))}</span></div>
      </div>
    </section>

    <section class="panel">
      <h2>Resumen ejecutivo</h2>
      <p class="small">
        Este reporte resume la corrida más reciente del scraper. Se enfoca en puestos de data en CDMX,
        descartando vacantes por debajo del umbral salarial y priorizando roles con mayor valor para un perfil matemático.
      </p>
    </section>

    <section class="panel">
      <h2>Preguntas clave</h2>
      <h3>1. ¿Qué empresas dominan el mercado?</h3>
      <ul>{top_companies_html}</ul>
      <h3>2. ¿Qué tecnologías se repiten más?</h3>
      <ul>{tech_counts_html}</ul>
      <h3>3. ¿Cuál es el rango salarial más común?</h3>
      <ul>
        <li><strong>Mediana salario mínimo:</strong> {html.escape(format_currency(salary_min_median))}</li>
        <li><strong>Promedio salario mínimo:</strong> {html.escape(format_currency(salary_min_mean))}</li>
        <li><strong>Mediana salario máximo:</strong> {html.escape(format_currency(salary_max_median))}</li>
      </ul>
    </section>

    <section class="panel">
      <h2>Gráficas</h2>
      <div class="plot-grid">
        {''.join(plot_images)}
      </div>
    </section>

    <section class="panel">
      <h2>Vacantes más valiosas para un perfil matemático</h2>
      <table>
        <thead>
          <tr>
            <th>Título</th>
            <th>Empresa</th>
            <th>Ubicación</th>
            <th>Salario</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {best_jobs_html}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")


def main() -> int:
    source_run_dir = latest_run_dir(RUNS_DIR)
    raw_df, salary_df, data_df = load_run_data(source_run_dir)

    report_tag = source_run_dir.name
    report_dir, figures_dir = ensure_output_dirs(REPORTS_DIR / report_tag)

    raw_df = add_analysis_columns(raw_df)
    salary_df = add_analysis_columns(salary_df)
    data_df = add_analysis_columns(data_df)

    top_companies = data_df["company"].value_counts().head(10) if "company" in data_df.columns else pd.Series(dtype=int)
    tech_plot_path, tech_counts = plot_technologies(data_df, figures_dir, report_tag)
    company_plot_path = plot_top_companies(data_df, figures_dir, report_tag)
    salary_plot_path = plot_salary_distribution(salary_df, figures_dir, report_tag)

    salary_min_median = salary_df["salary_min"].median() if "salary_min" in salary_df.columns else None
    salary_min_mean = salary_df["salary_min"].mean() if "salary_min" in salary_df.columns else None
    salary_max_median = salary_df["salary_max"].median() if "salary_max" in salary_df.columns else None

    best_for_math = data_df.sort_values(
        by=["math_score", "salary_min", "salary_max"],
        ascending=[False, False, False],
        na_position="last",
    ).head(10)

    txt_path = report_dir / f"{report_tag}_conclusiones.txt"
    html_path = report_dir / f"{report_tag}_reporte.html"

    write_text_summary(
        txt_path=txt_path,
        date_tag=report_tag,
        top_companies=top_companies,
        tech_counts=tech_counts,
        salary_df=salary_df,
        best_for_math=best_for_math,
    )

    render_html_report(
        html_path=html_path,
        report_title=f"Reporte automatizado OCC CDMX - {report_tag}",
        source_run_dir=source_run_dir,
        raw_df=raw_df,
        salary_df=salary_df,
        data_df=data_df,
        top_companies=top_companies,
        tech_counts=tech_counts,
        salary_min_median=salary_min_median,
        salary_min_mean=salary_min_mean,
        salary_max_median=salary_max_median,
        best_for_math=best_for_math,
        plot_paths=[company_plot_path, salary_plot_path, tech_plot_path],
    )

    print(f"Fuente: {source_run_dir}")
    print(f"Reporte HTML: {html_path}")
    print(f"Resumen TXT: {txt_path}")
    print(f"Graficas en: {figures_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
