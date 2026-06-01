from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = ROOT_DIR / "runs"
REPORTS_DIR = ROOT_DIR / "reports"


def current_date_tag(now: datetime | None = None) -> str:
    now = now or datetime.now()
    month_map = {
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
    return f"{now.day:02d}{month_map[now.month]}{str(now.year)[2:]}"


def report_paths_for_today() -> tuple[Path, Path]:
    tag = current_date_tag()
    report_dir = REPORTS_DIR / tag
    html_path = report_dir / f"{tag}_reporte.html"
    txt_path = report_dir / f"{tag}_conclusiones.txt"
    return html_path, txt_path


def run_script(script_name: str) -> None:
    script_path = ROOT_DIR / script_name
    subprocess.run([sys.executable, str(script_path)], check=True)


def main() -> int:
    html_path, txt_path = report_paths_for_today()
    report_tag = current_date_tag()

    if html_path.exists() and txt_path.exists():
        print(f"Ya existe el reporte de hoy ({report_tag}). No se vuelve a generar.")
        print(f"Reporte HTML: {html_path}")
        print(f"Resumen TXT: {txt_path}")
        return 0

    print("Ejecutando scraping diario...")
    run_script("scrape_occ_cdmx.py")

    print("Generando reporte diario...")
    run_script("generate_occ_report.py")

    print("Pipeline diario completado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
