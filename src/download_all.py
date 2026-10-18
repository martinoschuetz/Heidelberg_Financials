import urllib.request
import urllib.parse
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT_DIR / "input" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

base_url = 'https://www.heidelberg.de'
pages = [
    '/HD/Rathaus/Doppelhaushalt+2013_2014.html',
    '/HD/Rathaus/doppelhaushalt+2015_2016.html',
    '/HD/Rathaus/doppelhaushalt+2017_2018.html',
    '/HD/Rathaus/doppelhaushalt+2019_2020.html',
    '/HD/Rathaus/doppelhaushalt+2021_2022.html',
    '/HD/Rathaus/doppelhaushalt+2023_2024.html',
    '/HD/Rathaus/doppelhaushalt+2025_2026.html'
]

pdf_links = []

for page in pages:
    url = base_url + page
    try:
        html = urllib.request.urlopen(url).read().decode('utf-8')
        links = set(re.findall(r'href=[\x22\x27]([^\x22\x27]+\.pdf)', html, re.I))
        for link in links:
            if 'haushalt' in link.lower() and 'nachtrag' not in link.lower() and 'reden' not in link.lower():
                pdf_links.append(link)
    except Exception as e:
        print(f"Error fetching {url}: {e}")

pdf_links = sorted(set(pdf_links))
print("Found PDFs to download:")
for l in pdf_links:
    print(l)

for link in pdf_links:
    download_url = link if link.startswith('http') else base_url + link
    filename = urllib.parse.unquote(link.split('/')[-1])
    dest_path = PDF_DIR / filename
    if dest_path.exists():
        print(f"Already downloaded: {dest_path}")
        continue
    print(f"Downloading {filename} -> {dest_path}...")
    try:
        urllib.request.urlretrieve(download_url, dest_path)
        print(f"Downloaded {dest_path}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
