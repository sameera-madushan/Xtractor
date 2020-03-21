import msvcrt as m
import requests
import time
import re

banner = r'''

____  ___ __                        __
\   \/  //  |_____________    _____/  |_  ___________
 \     /\   __\_  __ \__  \ _/ ___\   __\/  _ \_  __ \
 /     \ |  |  |  | \// __ \\  \___|  | (  <_> )  | \/
/___/\  \|__|  |__|  (____  /\___  >__|  \____/|__|
      \_/                 \/     \/
                                [@Sameera Madushan]

'''
print(banner)

url = input("Enter the URL of tv series: ")
x = re.match(r'^(http:|)[/][/]www.([^/]+[.])*todaytvseries2.com', url)

try:
    if x:
    
        req = requests.get(url).content.decode('utf-8')
        seasons = re.findall(r'Download Season ([0-9]{1,})', req)
        seasons.sort()
        get_title = re.search(r'uk-article-title uk-badge1">(.*)</h1>', req).group(1)

        print("\nAvailable seasons to download in" + get_title)
        for i in seasons:
            print(get_title + "season"+ " " + i)

        user_input1 = input("\nEnter the season number that you want to download: ").zfill(2)
        if user_input1 == str("1") or str("01"):
            g = str(int(user_input1))
        else:
            g = str(int(user_input1) - 1)
        if g in seasons:
            a = re.findall(r'<div class="cell2">(S'+user_input1+'E[0-9]{1,})', req)
            print("\nAvailable episodes in " + user_input1 + "\n")
            print(a)

            links = []

            for i in a:
                if i in req:
                    t = re.findall(r''+i+'</div><div class="cell[0-9]">[0-9]{1,} Mb</div><div class="cell[0-9]"><a href=[\'"]?([^\'" >]+)" class="hvr-icon-sink-away" target="_blank">.*</a></div>', req)[0]
                    links.append(t)
                else:
                    print("Unknown Error")

            link_file = open("links.txt", "w")
            for i in links:
                link_file.write(i + "\n")
            link_file.close()
            print("\nDownload links saved to \"links.txt\" successfully")

        else:
            print("Season " + user_input1 + " not available")

    else:
        print("\nURL not related with todaytvseries2.com domain.")

except KeyboardInterrupt:
    print('\nProgramme Interrupted')
  
print("\nPress any key to exit")
m.getch()
print("Exiting...")
time.sleep(1)
  
            

