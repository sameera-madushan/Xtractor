#!/usr/bin/env python3
import requests
import time
import re
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from tqdm import tqdm

BANNER = r'''
____  ___ __                        __
\   \/  //  |_____________    _____/  |_  ___________
 \     /\   __\_  __ \__  \ _/ ___\   __\/  _ \_  __ \
 /     \ |  |  |  | \// __ \\  \___|  | (  <_> )  | \/
 /___/\  \|__|  |__|  (____  /\___  >__|  \____/|__|
      \_/                 \/     \/
                                [@Sameera Madushan]
'''

URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?(?:[^/]+\.)*todaytvseries\d+\.com'
)

TITLE_PATTERN = re.compile(
    r'uk-article-title uk-badge1">(.*?)<span',
    re.S
)

SEASON_PATTERN = re.compile(
    r'Download Season (\d+)'
)

LINK_PATTERN = re.compile(
    r'(S\d{2}E\d+)</div>'
    r'<div class="cell\d">\d+ Mb</div>'
    r'<div class="cell\d"><a href=[\'"]([^\'"]+)',
    re.S
)


def clean_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()


def get_filename_from_cd(resp, url):
    # Try Content-Disposition
    cd = resp.headers.get('content-disposition')
    if cd:
        m = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)', cd)
        if m:
            return clean_filename(unquote(m.group(1)))
    # Fallback to URL path
    path = urlparse(url).path
    name = os.path.basename(path) or "download"
    return clean_filename(unquote(name))


def download_file(session, url, dest_path, retries=2, timeout=15):
    for attempt in range(retries + 1):
        try:
            with session.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length') or 0)
                filename = get_filename_from_cd(r, url)
                out_file = dest_path / filename
                # If filename exists, append a counter
                if out_file.exists():
                    base, ext = os.path.splitext(filename)
                    i = 1
                    while (dest_path / f"{base}_{i}{ext}").exists():
                        i += 1
                    out_file = dest_path / f"{base}_{i}{ext}"

                chunk_size = 1024
                with open(out_file, 'wb') as f, tqdm(
                    total=total, unit='B', unit_scale=True, unit_divisor=1024,
                    desc=filename, leave=False
                ) as bar:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
                return out_file
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(1 + attempt)
                continue
            raise e


def extract_links(html, season_str):
    links = []
    for ep, link in LINK_PATTERN.findall(html):
        if ep.startswith(f"S{season_str}"):
            links.append(link)
    return links


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def main():
    print(BANNER)

    session = requests.Session()
    while True:
        url = input("\nEnter TV series URL (or 'q' to quit): ").strip()

        if url.lower() in ("q", "quit"):
            break

        if not URL_PATTERN.match(url):
            print("Invalid todaytvseries domain.")
            continue

        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            continue

        title_match = TITLE_PATTERN.search(html)
        if not title_match:
            print("Could not extract series title.")
            continue

        title = clean_filename(title_match.group(1))
        seasons = sorted(set(SEASON_PATTERN.findall(html)), key=int)

        while True:
            print(f"\nAvailable seasons for: {title}")
            for s in seasons:
                print(f"Season {s}")

            print("\nOptions:")
            print("  Enter season numbers (e.g. 1 or 1 2 3)")
            print("  Enter 'all' to process ALL seasons")
            print("  Enter 'b' to go back (home)")
            print("  Enter 'q' to quit")

            choice = input("\nYour choice: ").strip().lower()

            if choice in ("q", "quit"):
                return

            if choice in ("b", "back"):
                break

            if choice == "all":
                selected_seasons = seasons
            else:
                selected_seasons = choice.split()
                if not all(s in seasons for s in selected_seasons):
                    print("Invalid season selection.")
                    continue

            # Ask what to do: save links, download, or create wget script
            print("\nActions:")
            print("  1 → Save links to text files (default)")
            print("  2 → Download all extracted files now")
            print("  3 → Create a wget shell script with download commands")
            action = input("\nChoose action [1/2/3]: ").strip() or "1"

            base_dir = Path(clean_filename(title))
            ensure_dir(base_dir)

            all_links = []
            for season in selected_seasons:
                season_str = str(season).zfill(2)
                season_dir = base_dir / f"Season_{season_str}"
                ensure_dir(season_dir)

                links = extract_links(html, season_str)
                all_links.extend([(season_str, l) for l in links])

                txt_file = base_dir / f"{title} - Season {season_str}.txt"
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(f"{title} - Season {season_str}\n\n")
                    if links:
                        for l in links:
                            f.write(l + "\n")
                    else:
                        f.write("No links found\n")
                print(f'Saved: "{txt_file}"')

            if action == "1":
                print("Links saved. No downloads performed.")
            elif action == "3":
                # Create wget script
                script_path = base_dir / f"{title}_download.sh"
                with open(script_path, "w", encoding="utf-8") as sh:
                    sh.write("#!/usr/bin/env bash\n\n")
                    sh.write("set -euo pipefail\n\n")
                    for season_str, link in all_links:
                        season_dir = f"Season_{season_str}"
                        sh.write(f'mkdir -p "{season_dir}"\n')
                        sh.write(f'cd "{season_dir}"\n')
                        sh.write(f'wget -c "{link}"\n')
                        sh.write("cd - >/dev/null\n\n")
                os.chmod(script_path, 0o755)
                print(f'Wrote wget script: "{script_path}"')
            elif action == "2":
                # Download with progress bars
                if not all_links:
                    print("No links found to download.")
                else:
                    print(f"Starting downloads into folder: {base_dir}")
                    errors = []
                    # Overall progress: number of files
                    with tqdm(total=len(all_links), desc="Files", unit="file") as overall:
                        for season_str, link in all_links:
                            season_dir = base_dir / f"Season_{season_str}"
                            ensure_dir(season_dir)
                            try:
                                download_file(session, link, season_dir)
                            except Exception as e:
                                errors.append((link, str(e)))
                            overall.update(1)

                    if errors:
                        err_file = base_dir / "download_errors.txt"
                        with open(err_file, "w", encoding="utf-8") as ef:
                            for link, err in errors:
                                ef.write(f"{link} -> {err}\n")
                        print(f"Completed with {len(errors)} errors. See {err_file}")
                    else:
                        print("All downloads completed successfully.")
            else:
                print("Unknown action. Returning to menu.")

            print("\nWhat next?")
            print("  1 → Get more links from THIS series")
            print("  2 → Go home (new TV series URL)")
            print("  q → Quit")

            next_action = input("\nChoose: ").strip().lower()

            if next_action == "1":
                continue
            elif next_action == "2":
                break
            elif next_action in ("q", "quit"):
                return
            else:
                print("Invalid choice. Returning to series menu.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgramme Interrupted")
        time.sleep(1)
