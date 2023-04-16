import requests
import re
from bs4 import BeautifulSoup
import pushover
import transmissionrpc
import datetime

# Define the URL of the webpage you want to scrape
url = 'https://pleasuredome.github.io/pleasuredome/mame/index.html'
client = pushover.PushoverClient("/etc/pushover.creds")
work_dir = "/opt/arcade_app_alerter"

now = datetime.datetime.now()
now_strws = now.strftime("%m-%d-%Y %H:%M")
now_str = now.strftime("%m-%d-%Y")
now_ts = now.strftime("%m-%d-%Y %H:%M:%S")

with open(f"{work_dir}/data/mame.ver", "r") as file:
    oldversion = file.readlines()[0].strip()

# Send a GET request to the URL and retrieve the content
response = requests.get(url)
content = response.content

# Create a BeautifulSoup object to parse the content
soup = BeautifulSoup(content, 'html.parser')
link_tags = soup.find_all('a', href=True)
links = [link['href'] for link in link_tags]
update_roms_link = links[3]
update_CHDs_link = links[5]
update_software_link = links[8]
update_extras_link = links[13]

# Find the specific text using the text attribute and print it
target_text = 'MAME - Update ROMs'
found_element = soup.find(string=target_text)
if found_element:
    # Get the parent element of the found text
    parent_element = found_element.find_parent()

    # Extract the whole line with the matching text
    whole_line = parent_element.text.strip()

    # Print the whole line
    split_line = whole_line.split('\n')
    pattern = r"v(\d+\.\d+)\s+to\s+v(\d+\.\d+)"
    match = re.search(pattern, split_line[1])

    if match:
        with open(f"{work_dir}/data/lastcheck", "w") as file:
            file.write(f"{now_strws}\n")
            file.write("MAME\n")
        version1 = match.group(1)
        version2 = match.group(2)

        if oldversion != version2:
            print(f"[{now_ts}] Existing MAME version {oldversion} is different then Pleasuredome version {version2}")

            with open(f"{work_dir}/data/mame.ver", "w") as file:
                file.write(f"{version2}\n")
                file.write(f"{now_str}\n")
            client.send_message(f"New MAME version update {version2} is ready for download", title="New MAME Version")
            #try:
                #tc = transmissionrpc.Client('192.168.1.1', port='9091')
                #tc.authenticate('user', 'pass')
                #tc.add_torrent(update_roms_link)
                #tc.add_torrent(update_CHDs_link)
                #tc.add_torrent(update_software_link)
                #tc.add_torrent(update_extras_link)
                #tc.close()
            #except:
                #client.send_message(f"Error sending version {version2} downloads to transmission server", title="MAME Download Error")
        else:
            print(f"[{now_ts}] MAME Version {oldversion} is current")
    else:
        print(f"[{now_ts}] MAME ERROR: No version numbers found in the input string.")
        client.send_message(f"MAME update check error! No version numbers found", title="MAME Check Error")
else:
    print(f"[{now_ts}] MAME ERROR: Text not found.")
    client.send_message(f"MAME update check error! Text not found", title="MAME Check Error")

