import json
import re
import time
import unicodedata
from datetime import datetime
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup


urllib3.disable_warnings()


BASE_URL = "https://www.occ.com.mx/empleos/trabajo-en-tecnologias-de-la-informacion-sistemas/en-ciudad-de-mexico/permanente/"
MAX_PAGES = 10
SLEEP_SECONDS = 1.0
MIN_SALARY_MXN = 17000

MONTH_MAP = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

RUNS_DIR = Path("runs")

DATA_ROLE_KEYWORDS = [
    "data science",
    "data scientist",
    "data analyst",
    "analista de datos",
    "ciencia de datos",
    "machine learning",
    "data engineer",
    "bi engineer",
    "business intelligence",
    "power bi",
    "tableau",
    "etl",
    "analytics",
    "dashboards",
    "reporting",
    "sql",
    "python",
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


@dataclass
class OccVacancy:
    job_id: str
    title: str
    company: str
    location: str
    salary_text: str
    benefits: str
    company_url: str
    job_url: str
    job_url_source: str
    page: int
    position_on_page: int
    is_featured: bool
    is_confidential: bool
    source_url: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_ok: bool = False
    is_data_role: bool = False


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower())
    return ascii_text.strip("-")


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def normalize_occ_url(url: str) -> str:
    return url.replace("https://www.occ.com.mx//", "https://www.occ.com.mx/")


def build_page_url(page: int) -> str:
    if page <= 1:
        return BASE_URL
    return f"{BASE_URL}?page={page}"


def fetch_html(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=30, verify=False)
    response.raise_for_status()
    return response.text


def extract_job_url_map(soup: BeautifulSoup) -> Dict[str, str]:
    job_url_map: Dict[str, str] = {}
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(script.get_text(strip=True))
        except Exception:
            continue

        graph = payload.get("@graph") if isinstance(payload, dict) else None
        if not isinstance(graph, list):
            continue

        for node in graph:
            if not isinstance(node, dict) or node.get("@type") != "ItemList":
                continue
            for item in node.get("itemListElement", []):
                if not isinstance(item, dict):
                    continue
                url = item.get("url") or ""
                match = re.search(r"/empleo/oferta/(\d+)-", url)
                if match:
                    job_url_map[match.group(1)] = normalize_occ_url(url.split("?")[0])
    return job_url_map


def parse_salary_text(card: BeautifulSoup) -> str:
    salary_tag = card.select_one("span.mr-2.text-grey-900")
    if salary_tag:
        text = salary_tag.get_text(" ", strip=True)
        if text and text not in {"Recomendada", "Hoy"}:
            return text

    for span in card.find_all("span"):
        text = span.get_text(" ", strip=True)
        if not text:
            continue
        normalized = normalize_text(text)
        if "$" in text or "sueldo" in normalized or "mensual" in normalized:
            if normalized not in {"recomendada", "hoy"}:
                return text
    return ""


def parse_company_name(card: BeautifulSoup) -> str:
    link = card.select_one('a[href*="/empleos/bolsa-de-trabajo-"]')
    if link:
        return link.get_text(" ", strip=True)
    return "Empresa confidencial"


def parse_company_url(card: BeautifulSoup) -> str:
    link = card.select_one('a[href*="/empleos/bolsa-de-trabajo-"]')
    return normalize_occ_url(link.get("href", "")) if link else ""


def parse_location(card: BeautifulSoup) -> str:
    location_tag = card.select_one(".no-alter-loc-text p")
    if location_tag:
        return location_tag.get_text(" ", strip=True)
    return ""


def parse_benefits(card: BeautifulSoup) -> str:
    benefits = [li.get_text(" ", strip=True) for li in card.select("ul li")]
    return " | ".join([item for item in benefits if item])


def build_job_url(job_id: str, title: str, job_url_map: Dict[str, str]) -> Tuple[str, str]:
    if job_id in job_url_map:
        return job_url_map[job_id], "jsonld"
    fallback = f"https://www.occ.com.mx/empleo/oferta/{job_id}-{slugify(title)}"
    return normalize_occ_url(fallback), "fallback"


def salary_to_range(salary_text: str) -> Tuple[Optional[int], Optional[int]]:
    if not salary_text:
        return None, None

    normalized = normalize_text(salary_text)
    if "no mostrado" in normalized:
        return None, None

    cleaned = salary_text.replace(",", "").replace("MXN", "")
    numbers = [int(n) for n in re.findall(r"(\d+)", cleaned)]
    if not numbers:
        return None, None

    if len(numbers) >= 2:
        low, high = numbers[0], numbers[1]
        if low < 100 and high < 100:
            return low * 1000, high * 1000
        if low < 100 and high >= 100:
            return low * 1000, high
        return low, high

    value = numbers[0]
    if value < 100:
        value *= 1000
    return value, value


def is_data_role(title: str, benefits: str) -> bool:
    text = f"{normalize_text(title)} {normalize_text(benefits)}"
    return any(keyword in text for keyword in DATA_ROLE_KEYWORDS)


def parse_cards(page_html: str, page: int, page_url: str, seen_ids: set[str]) -> List[OccVacancy]:
    soup = BeautifulSoup(page_html, "html.parser")
    job_url_map = extract_job_url_map(soup)
    cards = soup.select("div.card-job-offer[data-id]")

    vacancies: List[OccVacancy] = []
    for position, card in enumerate(cards, start=1):
        job_id = card.get("data-id", "").strip()
        if not job_id or job_id in seen_ids:
            continue

        title_tag = card.select_one("h2")
        if not title_tag:
            continue

        title = title_tag.get_text(" ", strip=True)
        company = parse_company_name(card)
        location = parse_location(card)
        salary_text = parse_salary_text(card)
        benefits = parse_benefits(card)
        company_url = parse_company_url(card)
        job_url, job_url_source = build_job_url(job_id, title, job_url_map)

        vacancies.append(
            OccVacancy(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                salary_text=salary_text,
                benefits=benefits,
                company_url=company_url,
                job_url=job_url,
                job_url_source=job_url_source,
                page=page,
                position_on_page=position,
                is_featured="is-highlighted" in card.get("class", []),
                is_confidential=company == "Empresa confidencial",
                source_url=page_url,
            )
        )
        seen_ids.add(job_id)

    return vacancies


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

    for kw in MATH_PROFILE_KEYWORDS:
        if kw in text:
            score += 2

    salary_min = row.get("salary_min")
    if pd.notna(salary_min):
        if salary_min >= 30000:
            score += 3
        elif salary_min >= 20000:
            score += 2
        elif salary_min >= 17000:
            score += 1

    if "senior" in text or "sr" in text:
        score += 2
    if "jr" in text or "junior" in text:
        score -= 1
    if "becario" in text or "trainee" in text or "practicante" in text:
        score -= 3

    return score


def current_date_tag(now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    return f"{now.day:02d}{MONTH_MAP[now.month]}{str(now.year)[2:]}"


def get_run_dir() -> Path:
    return RUNS_DIR / current_date_tag()


def get_output_paths(run_dir: Path) -> dict[str, Path]:
    return {
        "raw_json": run_dir / "occ_tech_cdmx_raw.json",
        "raw_csv": run_dir / "occ_tech_cdmx_raw.csv",
        "salary_csv": run_dir / "occ_tech_cdmx_17000plus.csv",
        "data_csv": run_dir / "occ_tech_cdmx_data_17000plus.csv",
        "summary_txt": run_dir / "occ_tech_cdmx_summary.txt",
        "done_flag": run_dir / "DONE.flag",
    }


def build_summary_text(run_tag: str, df: pd.DataFrame, salary_filtered: pd.DataFrame, data_filtered: pd.DataFrame) -> str:
    top_companies = data_filtered["company"].value_counts().head(10) if not data_filtered.empty else pd.Series(dtype=int)
    top_tech = pd.Series(dtype=int)
    if not data_filtered.empty:
        all_techs: list[str] = []
        for text in data_filtered["title"].tolist():
            normalized = normalize_text(text)
            for keyword in DATA_ROLE_KEYWORDS:
                if keyword in normalized:
                    all_techs.append(keyword)
        if all_techs:
            top_tech = pd.Series(all_techs).value_counts().head(15)

    salary_min_median = salary_filtered["salary_min"].median() if not salary_filtered.empty else None
    salary_min_mean = salary_filtered["salary_min"].mean() if not salary_filtered.empty else None
    salary_max_median = salary_filtered["salary_max"].median() if not salary_filtered.empty else None

    best_for_math = data_filtered.sort_values(
        by=["math_score", "salary_min", "salary_max"],
        ascending=[False, False, False],
        na_position="last",
    ).head(10)

    lines = []
    lines.append(f"Fecha de analisis: {run_tag}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("PREGUNTA 1: ¿Qué empresas dominan el mercado?")
    if not top_companies.empty:
        for company, count in top_companies.items():
            lines.append(f"- {company}: {count} vacantes")
    else:
        lines.append("- No hay datos suficientes.")
    lines.append("")
    lines.append("PREGUNTA 2: ¿Qué tecnologías se repiten más?")
    if not top_tech.empty:
        for tech, count in top_tech.items():
            lines.append(f"- {tech}: {count}")
    else:
        lines.append("- No se detectaron tecnologias claramente repetidas.")
    lines.append("")
    lines.append("PREGUNTA 3: ¿Cuál es el rango salarial más común?")
    if salary_min_median is not None and pd.notna(salary_min_median):
        lines.append(f"- Mediana salario minimo: {salary_min_median:,.0f} MXN")
    if salary_min_mean is not None and pd.notna(salary_min_mean):
        lines.append(f"- Promedio salario minimo: {salary_min_mean:,.0f} MXN")
    if salary_max_median is not None and pd.notna(salary_max_median):
        lines.append(f"- Mediana salario maximo: {salary_max_median:,.0f} MXN")
    lines.append("")
    lines.append("PREGUNTA 4: ¿Qué vacantes parecen más valiosas para un perfil matemático?")
    for _, row in best_for_math.iterrows():
        lines.append(
            f"- [{row.get('math_score', 0)}] {row.get('title', '')} | "
            f"{row.get('company', '')} | {row.get('location', '')} | {row.get('salary_text', '')}"
        )
    lines.append("")
    lines.append("CONCLUSION GENERAL")
    lines.append(
        "El mercado de data en CDMX muestra mejor valor en roles como Data Scientist, Data Engineer, "
        "Business Intelligence, Analytics y puestos relacionados con Python, SQL, Power BI y Machine Learning. "
        "Los perfiles junior o de becario suelen quedar por debajo del umbral salarial objetivo."
    )
    lines.append("")
    lines.append(f"Total vacantes scrapeadas: {len(df)}")
    lines.append(f"Vacantes con salario >= ${MIN_SALARY_MXN}: {len(salary_filtered)}")
    lines.append(f"Vacantes data + salario >= ${MIN_SALARY_MXN}: {len(data_filtered)}")
    return "\n".join(lines)


def main() -> None:
    run_tag = current_date_tag()
    run_dir = get_run_dir()
    paths = get_output_paths(run_dir)

    if paths["done_flag"].exists():
        print(f"Ya se ejecuto hoy ({run_tag}). No se vuelve a scrapear.")
        print(f"Resultados disponibles en: {run_dir}")
        return

    run_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Referer": "https://www.occ.com.mx/",
        }
    )

    # Seed cookies like a browser session.
    session.get(BASE_URL, timeout=30, verify=False)

    all_vacancies: List[OccVacancy] = []
    seen_ids: set[str] = set()

    for page in range(1, MAX_PAGES + 1):
        page_url = build_page_url(page)
        print(f"Scraping page {page}: {page_url}")
        html_text = fetch_html(session, page_url)
        page_vacancies = parse_cards(html_text, page, page_url, seen_ids)
        print(f"  found {len(page_vacancies)} new vacantes")
        if not page_vacancies:
            break
        all_vacancies.extend(page_vacancies)
        time.sleep(SLEEP_SECONDS)

    records = [asdict(vacancy) for vacancy in all_vacancies]
    for record in records:
        salary_min, salary_max = salary_to_range(record["salary_text"])
        record["salary_min"] = salary_min
        record["salary_max"] = salary_max
        record["salary_ok"] = salary_min is not None and salary_min >= MIN_SALARY_MXN
        record["is_data_role"] = is_data_role(record["title"], record["benefits"])

    df = pd.DataFrame(records)
    df["math_score"] = df.apply(math_value_score, axis=1)

    salary_filtered = df[df["salary_ok"]].copy()
    salary_filtered["math_score"] = salary_filtered.apply(math_value_score, axis=1)
    salary_filtered = salary_filtered.sort_values(
        by=["salary_min", "salary_max", "title"],
        ascending=[False, False, True],
        na_position="last",
    )

    data_filtered = salary_filtered[salary_filtered["is_data_role"]].copy()
    data_filtered["math_score"] = data_filtered.apply(math_value_score, axis=1)

    summary_text = build_summary_text(run_tag, df, salary_filtered, data_filtered)
    paths["raw_json"].write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    df.to_csv(paths["raw_csv"], index=False, encoding="utf-8")
    salary_filtered.to_csv(paths["salary_csv"], index=False, encoding="utf-8")
    data_filtered.to_csv(paths["data_csv"], index=False, encoding="utf-8")
    paths["summary_txt"].write_text(summary_text, encoding="utf-8")
    paths["done_flag"].write_text(run_tag, encoding="utf-8")

    print("\nResumen")
    print(f"Total vacantes scrapeadas: {len(df)}")
    print(f"Vacantes con salario >= ${MIN_SALARY_MXN}: {len(salary_filtered)}")
    print(f"Vacantes data + salario >= ${MIN_SALARY_MXN}: {len(data_filtered)}")
    print(f"Carpeta de salida: {run_dir}")
    print(f"Raw JSON: {paths['raw_json']}")
    print(f"Raw CSV: {paths['raw_csv']}")
    print(f"Filtered CSV: {paths['salary_csv']}")
    print(f"Data CSV: {paths['data_csv']}")
    print(f"Summary TXT: {paths['summary_txt']}")

    preview_cols = ["title", "company", "location", "salary_text", "job_url"]
    print("\nPrimeras vacantes filtradas:")
    print(salary_filtered[preview_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
