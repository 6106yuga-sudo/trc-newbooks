import re
import json
import zipfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from html.parser import HTMLParser

PAGE = "https://www.trc.co.jp/trc_opendata/"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")

    def handle_data(self, data):
        if self.href and data.strip():
            self.links.append((data.strip(), self.href))

    def handle_endtag(self, tag):
        if tag == "a":
            self.href = None

def download(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()

def main():
    html = download(PAGE).decode("utf-8", errors="replace")
    parser = Links()
    parser.feed(html)

    candidates = []
    for label, href in parser.links:
        if ".zip" in href.lower():
            candidates.append(urljoin(PAGE, href))

    if not candidates:
        raise RuntimeError("ZIP download link not found")

    url = candidates[0]
    data = download(url)
    target = Path("data")
    target.mkdir(exist_ok=True)
    archive_path = target / "latest.zip"
    archive_path.write_bytes(data)

    if not zipfile.is_zipfile(archive_path):
        raise RuntimeError("Downloaded file is not a valid ZIP")

    with zipfile.ZipFile(archive_path) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            if Path(item.filename).suffix.lower() in (".tsv", ".csv", ".txt"):
                destination = target / Path(item.filename).name
                destination.write_bytes(archive.read(item))

    (target / "source.json").write_text(
        json.dumps({"source": url}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("TRC download completed:", url)

if __name__ == "__main__":
    main()
