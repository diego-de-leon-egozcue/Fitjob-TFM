"""
_pdf_worker.py — Se ejecuta como subproceso aislado para evitar conflictos
entre Playwright y el event loop de asyncio en Windows.
Uso: python _pdf_worker.py <html_file> <pdf_file>
"""
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("Uso: _pdf_worker.py <html_file> <pdf_file>", file=sys.stderr)
        sys.exit(1)

    html_path = Path(sys.argv[1])
    pdf_path  = Path(sys.argv[2])

    html_content = html_path.read_text(encoding="utf-8")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page()
        page.emulate_media(media="print")
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
        )
        browser.close()


if __name__ == "__main__":
    main()
