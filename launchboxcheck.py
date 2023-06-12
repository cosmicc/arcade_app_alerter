import requests
from bs4 import BeautifulSoup
import pushover
import datetime

# Define the URL of the webpage you want to scrape
url = 'https://pleasuredome.github.io/pleasuredome/mame/index.html'
client = pushover.PushoverClient("/etc/pushover.creds")
work_dir = "/opt/arcade_app_alerter"

now = datetime.datetime.now()
now_str = now.strftime("%m-%d-%Y")
now_ts = now.strftime("%m-%d-%Y %H:%M:%S")

with open(f"{work_dir}/data/launchbox.ver", "r") as file:
    oldversion = file.readlines()[0].strip()

# Send a GET request to the webpage
url = 'https://www.launchbox-app.com/about/changelog'
try:
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the elements containing version numbers
    version_elements = soup.find_all('h4')
    # Extract the version numbers
    version_numbers = []

    for element in version_elements:
        version_number = element.text.strip()
        version_numbers.append(version_number)

    v1split = version_numbers[0].split(" ")
    v2split = version_numbers[1].split(" ")

    if v1split[4] == "?":
        newversion = v2split[1]
        #print(f"Beta Version: {v1split[1]}")
        #print(f"Release Version: {v2split[1]}")
    else:
        newversion = v1split[1]
        #print(f"Release Version: {v1split[1]}")

    with open(f"{work_dir}/data/lastcheck", "w") as file:
        file.write(f"{now_ts}\n")
        file.write("Launchbox\n")

    if oldversion != newversion:
        print(f"[{now_ts}] Launchbox version {oldversion} is different then current version {newversion}")
        with open(f"{work_dir}/data/launchbox.ver", "w") as file:
            file.write(f"{newversion}\n")
            file.write(f"{now_str}\n")
        client.send_message(f"New Launchbox version {newversion} is ready for download", title="New Launchbox Version")
    else:
        print(f"[{now_ts}] Launchbox Version {oldversion} is current")
except:
    print(f"[{now_ts}] Launchbox Check Error! Cannot determine latest version")
    client.send_message("Launchbox Check Error! Cannot determine latest version", title="Launchbox Check Error")

