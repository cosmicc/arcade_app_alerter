import requests
import re
from bs4 import BeautifulSoup
import pushover
import transmissionrpc
import datetime

# Define the URL of the webpage you want to scrape
url = 'http://www.ledblinky.net/Download.htm'
client = pushover.PushoverClient("/etc/pushover.creds")
work_dir = "/opt/arcade_app_alerter"

now = datetime.datetime.now()
now_str = now.strftime("%m-%d-%Y %H:%M")
now_ts = now.strftime("%m-%d-%Y %H:%M:%S")

with open(f"{work_dir}/data/ledblinky.ver", "r") as file:
    oldversion = file.readlines()[0].strip()

try:
    # Send a GET request to the URL and retrieve the content
    response = requests.get(url)
    content = response.content

    # Create a BeautifulSoup object to parse the content
    soup = BeautifulSoup(content, 'html.parser')
    link_tags = soup.find_all('a', href=True)
    links = [link['href'] for link in link_tags]
    versions = links[0].split('_')
    maj_ver = versions[1]
    min_ver = versions[2]
    pat_ver = versions[3]
    newversion = f'{maj_ver}.{min_ver}.{pat_ver}'

    with open(f"{work_dir}/data/lastcheck", "w") as file:
        file.write(f"{now_str}\n")
        file.write("LedBlinky\n")

    if oldversion != newversion:
        print(f"[{now_ts}] LEDBlinky version {oldversion} is different then current version {newversion}")
        with open(f"{work_dir}/data/ledblinky.ver", "w") as file:
            file.write(f"{newversion}\n")
            file.write(f"{now_str}\n")
            client.send_message(f"New LEDBlinky version update {newversion} is ready for download", title="New LEDBlinky Version")
            #try:
            #    tc = transmissionrpc.Client('192.168.199.8', port='9091')
            #    tc.authenticate('ip', 'Ifa6wasa9')
                #tc.add_torrent(update_roms_link)
            #    tc.close()
            #except:
            #    client.send_message(f"Error sending version {version2} downloads to transmission server", title="LEDBlinky Download Error")
    else:
        print(f"[{now_ts}] LEDBlinky Version {oldversion} is current")
except:
    print(f"[{now_ts}] LedBlinky Check Error! Cannot determine latest version")
    client.send_message(f"LedBlinky Check Error! Cannot determine latest version", title="LedBlinky Check Error")
