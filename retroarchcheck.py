import requests
import re
from bs4 import BeautifulSoup
import pushover
import datetime

# Define the URL of the webpage you want to scrape
url = 'https://www.retroarch.com/?page=platforms'
client = pushover.PushoverClient("/etc/pushover.creds")

now = datetime.datetime.now()
now_str = now.strftime("%m-%d-%Y %H:%M")

with open("./data/retroarch.ver", "r") as file:
    oldversion = file.readlines()[0].strip()
print(f"Existing Retroarch version is: {oldversion}")

# Send a GET request to the URL and retrieve the content
response = requests.get(url)
content = response.content

# Create a BeautifulSoup object to parse the content
soup = BeautifulSoup(content, 'html.parser')
#print(soup)
# Find the specific text using the text attribute and print it
version_elements = soup.find_all('p')
html_ver = str(version_elements[4])
#html_ver = "<p>The current stable version is: 1.15.0</p>"
vsoup = BeautifulSoup(html_ver, 'html.parser')
newvertext = vsoup.text
newversion = newvertext.split(" ")[5]
print(f"Retroarch current version is: {newversion}")

with open("./data/lastcheck", "w") as file:
    file.write(f"{now_str}\n")
    file.write("Retroarch\n")

if oldversion != newversion:
    print(f"Existing Retroarch version {oldversion} is different then current version {newversion}")
    with open("./data/retroarch.ver", "w") as file:
        file.write(f"{newversion}\n")
        file.write(f"{now_str}\n")
    client.send_message(f"New Retroarch version update {newversion} is ready for download", title="New Retroarch Version")
else:
    print(f"Version {oldversion} is current, nothing to do")
