import urllib.request
import urllib.parse
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT_DIR / "input" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

base_url = "https://www.heidelberg.de"
# Note: heidelberg.de paths are case-sensitive (/HD/Rathaus/...)
pages = [
    "/HD/Rathaus/Haushalt+_+Finanzen.html",
    "/HD/Rathaus/doppelhaushalt+2025_2026.html",
    "/HD/Rathaus/informationen+zur+haushaltserstellung+2025_26.html",
    "/HD/Rathaus/doppelhaushalt+2023_2024.html",
    "/HD/Rathaus/doppelhaushalt+2021_2022.html",
    "/HD/Rathaus/doppelhaushalt+2019_2020.html",
    "/HD/Rathaus/doppelhaushalt+2017_2018.html",
    "/HD/Rathaus/doppelhaushalt+2015_2016.html",
    "/HD/Rathaus/Doppelhaushalt+2013_2014.html",
    "/HD/Rathaus/FAQ+zum+Haushalt.html",
    "/HD/Rathaus/Staedtische+Unternehmen.html",
]


def discover_pdf_links():
    pdf_links = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for page in pages:
        url = base_url + page
        try:
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
            links = set(re.findall(r'href=[\x22\x27]([^\x22\x27]+\.pdf)', html, re.I))
            for link in links:
                low = link.lower()
                if (
                    "haushalt" in low
                    or "jahresabschluss" in low
                    or "nachtrag" in low
                    or "beteiligungsbericht" in low
                    or "aenderungsantraege" in low
                ) and "reden" not in low:
                    pdf_links.append(link)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return sorted(set(pdf_links))


def main():
    pdf_links = discover_pdf_links()
    print(f"Found {len(pdf_links)} official PDFs on heidelberg.de:")
    for l in pdf_links:
        print(f"  - {l}")

    for link in pdf_links:
        download_url = link if link.startswith("http") else base_url + link
        filename = urllib.parse.unquote(link.split("/")[-1])
        dest_path = PDF_DIR / filename
        if dest_path.exists():
            print(f"Already downloaded: {dest_path.name}")
            continue
        print(f"Downloading {filename} -> {dest_path}...")
        try:
            urllib.request.urlretrieve(download_url, dest_path)
            print(f"Downloaded {dest_path.name}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")


if __name__ == "__main__":
    main()
