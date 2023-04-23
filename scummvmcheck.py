import requests
import re
from bs4 import BeautifulSoup
import pushover
import datetime

# Define the URL of the webpage you want to scrape
url = 'https://www.scummvm.org/downloads/'
client = pushover.PushoverClient("/etc/pushover.creds")
work_dir = "/opt/arcade_app_alerter"

now = datetime.datetime.now()
now_str = now.strftime("%m-%d-%Y %H:%M")
now_ts = now.strftime("%m-%d-%Y %H:%M:%S")

with open(f"{work_dir}/data/scummvm.ver", "r") as file:
    oldversion = file.readlines()[0].strip()

if (True):
    # Send a GET request to the URL and retrieve the content
    response = requests.get(url)
    content = response.content

    # Create a BeautifulSoup object to parse the content
    soup = BeautifulSoup(content, 'html.parser')
    #print(soup)
    # Find the specific text using the text attribute and print it
    version_elements = soup.find_all('li')
    for element in version_elements:
        print(element)    
    html_ver = str(version_elements[4])
    #html_ver = "<p>The current stable version is: 1.15.0</p>"
    vsoup = BeautifulSoup(html_ver, 'html.parser')
    newvertext = vsoup.text
    newversion = newvertext.split(" ")[5]

    with open(f"{work_dir}/data/lastcheck", "w") as file:
        file.write(f"{now_str}\n")
        file.write("ScummVM\n")

    if oldversion != newversion:
        print(f"[{now_ts}] ScummVM version {oldversion} is different then current version {newversion}")
        with open(f"{work_dir}/data/retroarch.ver", "w") as file:
            file.write(f"{newversion}\n")
            file.write(f"{now_str}\n")
        client.send_message(f"New ScummVM version update {newversion} is ready for download", title="New ScummVM Version")
    else:
        print(f"[{now_ts}] ScummVM Version {oldversion} is current")

#except:
 #   print(f"[{now_ts}] ScummVM Check Error! Cannot determine latest version")
  #  client.send_message(f"ScummVM Check Error! Cannot determine latest version", title="ScummVM Check Error")
