import requests
import time
import re

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


def main():
    print(BANNER)

    while True:
        url = input("\nEnter TV series URL (or 'q' to quit): ").strip()

        if url.lower() in ("q", "quit"):
            break

        if not URL_PATTERN.match(url):
            print("Invalid todaytvseries domain.")
            continue

        try:
            resp = requests.get(url, timeout=10)
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
            print("  Enter 'all' to download ALL seasons")
            print("  Enter 'b' to go back (home)")
            print("  Enter 'q' to quit")

            choice = input("\nYour choice: ").strip().lower()

            if choice in ("q", "quit"):
                return

            if choice in ("b", "back"):
                break

            if choice == "all":
                selected_seasons = seasons
                filename = f"{title} - All Seasons.txt"

                with open(filename, "w", encoding="utf-8") as f:
                    for season in selected_seasons:
                        season_str = str(season).zfill(2)
                        f.write(f"{title} - Season {season_str}\n")

                        found = False
                        for ep, link in LINK_PATTERN.findall(html):
                            if ep.startswith(f"S{season_str}"):
                                f.write(link + "\n")
                                found = True

                        if not found:
                            f.write("No links found\n")
                        f.write("\n")

                print(f'Saved: "{filename}"')

            else:
                selected_seasons = choice.split()
                if not all(s in seasons for s in selected_seasons):
                    print("Invalid season selection.")
                    continue

                for season in selected_seasons:
                    season_str = str(season).zfill(2)
                    filename = f"{title} - Season {season_str}.txt"

                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"{title} - Season {season_str}\n\n")

                        found = False
                        for ep, link in LINK_PATTERN.findall(html):
                            if ep.startswith(f"S{season_str}"):
                                f.write(link + "\n")
                                found = True

                        if not found:
                            f.write("No links found\n")

                    print(f'Saved: "{filename}"')

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
