from bs4 import BeautifulSoup
from clint.textui import progress
import os
os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
import vlc
import subprocess
import requests
import json
import re

def run_script_in_node(js: str):
    proc = subprocess.check_output(['node', '-e', js])
    return proc.decode('utf-8')


# Path the vlc media  player executable
# VLC media player is required to stream videos 
PATH_TO_VLC = "C:/Program Files/VideoLan/VLC/vlc.exe"

# prompt user for a search term
term = input("Search animepahe: ")

# base url to search the animepahe api
baseSearchURL = 'https://animepahe.com/api?m=search&l=8&q='

# append user input search term to base url
searchURL = baseSearchURL + term

# issue a request with the constructed url
req = requests.get(searchURL)

data = req.json()

# if search term yielded any results, exists is set to true
exists = "data" in data

if exists:
    with open('searchResults.txt', 'w', encoding='utf-8') as file:
        file.write(str(json.dumps(data, indent=1)))
else:
    print("No results found")
    quit()


# print search results and some other relevant info
iteration = 1

for result in data["data"]:
    print(str(iteration) + '. ', result["title"], end="\n\t")
    print('Episodes: ', result["episodes"], end="   ")
    print('Year: ', result["year"], end="   ")
    print('Score: ', result["score"], end="   ")
    print('Type: ', result["type"], end="   ")
    print('Status: ', result["status"], end="\n\n")
    iteration += 1

# prompt user to select a series
selection = int(input("Make a selection (input serial number of series): "))

selectedSeries = data["data"][selection-1]

# id of the selected series
id = '&id=' + str(selectedSeries["id"])

# url for the selected series
seriesUrl = "https://animepahe.com/api?m=release" + id + "&sort=episode_asc"

req = requests.get(seriesUrl)

episodes = req.json()

if True:
    with open('episodeResults.txt', 'w', encoding='utf-8') as file:
        file.write(str(json.dumps(episodes, indent=1)))
else:
    print("No results found")
    quit()

# print episode results and some other relevant info
print('--------------------------------------------------------------------------------------------------------------------------')
print(selectedSeries["title"], end="\t\t")
print('Number of episodes: ', episodes["total"])
print('--------------------------------------------------------------------------------------------------------------------------')

iteration = 1
for result in episodes["data"]:
    print(str(iteration) + '. ', 'Episode - ' + str(result["episode"]), end="\t\t\t")
    print('Duration: ', result["duration"], end="\t")
    print('Disc: ', result["disc"], end="\n\n")
    iteration += 1


# prompt user to select an episode
epNumber = int(input("Enter episode number: "))

# object of the selected episode from the api
selectedEpisode = episodes["data"][epNumber-1]

# session of the selected episode
episodeSession = '&session=' + selectedEpisode["session"]

# id of the selected series
seriesID = '&id=' + str(selectedSeries["id"])

# player parameter
player = '&p=kwik'

#the url to watch the selected episode
selectedEpisodeWatchUrl = "https://animepahe.com/play/" + selectedSeries["session"] + "/" + selectedEpisode["session"]

print("\n\n\n", selectedEpisodeWatchUrl, end="\n\n\n")

# the url to the data of the selected episode
selectedEpisodeDataUrl = "https://animepahe.com/api?m=embed" + seriesID + episodeSession + player

req = requests.get(selectedEpisodeDataUrl)

episodeData = req.json()

if True:
    with open('episodeData.txt', 'w', encoding='utf-8') as file:
        file.write(str(json.dumps(episodeData, indent=1)))
else:
    print("No results found")
    quit()

keys = episodeData["data"].keys()

keylist = list(keys)

for key in keylist:
    nestedKeys = list(episodeData["data"][key].keys())
    for k in nestedKeys:
        print('--------------------------------------------------------------------------------------------------------------------------')
        print("Quality: ", k+"p", end=" ")
        print("Filesize: ", episodeData["data"][key][k]["filesize"], end=" ")
        print("Server: ", episodeData["data"][key][k]["server"], end=" ")
        print("URL: ", episodeData["data"][key][k]["url"])
        url = episodeData["data"][key][k]["url"]
        print('--------------------------------------------------------------------------------------------------------------------------')

# clear the terminal
os.system('cls||clear')

req  = requests.get(url, headers={'Referer': 'https://kwik.cx/'})

soup = BeautifulSoup(req.text, 'html.parser')

# this is the title of the episode file
episodeTitle = soup.title.text

with open ('soup.txt', 'w', encoding='utf-8') as file:
    file.write(soup.prettify())

# Regular Expressions to match the correct parameters
eval_script_regEx = re.compile(r'(eval.*\))')

parameters_regEx = re.compile(r'https:\/\/(.*?)\..*\/(\d+)\/(.*)\/.*token=(.*)&expires=([^\']+)')

# search the page for eval script matching the compiled re
script_to_evaluate = eval_script_regEx.search(req.text).group(1)

# evaluate the found eval script
evaluated_script = run_script_in_node('eval=console.log; ' + script_to_evaluate)

# search the evaluated script for multiple parameters using the compiled re
cdn = parameters_regEx.search(evaluated_script).group(1)
number = parameters_regEx.search(evaluated_script).group(2)
fileNumber = parameters_regEx.search(evaluated_script).group(3)
token = parameters_regEx.search(evaluated_script).group(4)
expires = parameters_regEx.search(evaluated_script).group(5)

# kwik video download url format: https://{cdn}.nextstream.org/get/{token}/{expires}/mp4/{number}/{fileNumber}/{title}
# building the download url with the extracted parameters
episodeDownloadUrl = 'https://' + cdn + '.nextstream.org/get/' + token + '/' + expires + '/mp4/' + number + '/' + fileNumber + '/' + episodeTitle 

'''
print("\n\n", cdn)
print("\n\n", number)
print("\n\n", fileNumber)
print("\n\n", token)
print("\n\n", expires)
print("\n\n", episodeTitle)
'''

# does user want to download or stream the selected episode?
action = input(("\n\nDownload or Stream?\n"))

if action == 'download':        
    # check if a downloads directory exists and if not, create one and cd into it
    downloads_dir = ("downloads")
    downloads_exists = os.path.isdir(downloads_dir)

    if downloads_exists:
        os.chdir(downloads_dir)
    else:
        os.makedirs(downloads_dir)
        print("downloads directory created... ", downloads_dir)
        os.chdir(downloads_dir)

    print("\n\nDownload from ", episodeDownloadUrl)

    req  = requests.get(episodeDownloadUrl, stream = True)

    with open( episodeTitle, 'wb') as file:

        total_length = int(req.headers.get('content-length'))

        for chunk in progress.bar(req.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
            if chunk:
                file.write(chunk)

if action == 'stream':
    # create a subprocess to open the episode url with vlc media player
    # PATH_TO_VLC is the path the vlc executable
    subprocess.Popen([PATH_TO_VLC, episodeDownloadUrl])
