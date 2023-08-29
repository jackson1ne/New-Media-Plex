# pip install plexapi
import json
from plexapi.server import PlexServer
import requests
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Resource used https://python-plexapi.readthedocs.io/en/latest/index.html
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#                                              --------------README--------------
# baseURL - This is the URL of your media server, it is typically just your ipv4 address with port 32400 ex: http://0.0.0.0:32400
# token - You need this to access your server, you can find this by clicking the three dots in the bottom right corner of any media
#           and select "Get Info". Next select "View XML" in the bottom left of the pop-up, and search through the url (of the new window)
#           until you find "Plex-Token=". This is your token.
# plex - create the connection to your server.
baseURL = ''
token = ''
plex = PlexServer(baseURL, token)

# These depend on the name of your libray
movies = plex.library.section('Movies')
shows = plex.library.section('TV Shows')
# To store newly added media
newMedia = []

# Search through the movie library for media added within the last 7 days
for movie in movies.search(filters={"addedAt>>": "7d"}):
    # Gather the details you want
    movieDetails = []
    movieTitle = movie.title
    movieDuration = movie.duration
    movieYear = movie.year

    # Since move.duration returns in milliseconds, I converted to minutes.
    total_seconds = movieDuration / 1000
    minutes = int(total_seconds // 60)
    movieDuration = str(minutes) + " minutes"

    # This is highly circumstantial, I required a single string for each instance to be used easily in a later step.
    movieTitle = movie.title + " - " + str(movieYear) + " (" + movieDuration + ")"

    # append the new media array
    newMedia.append(movieTitle)

# same as movie libray search, just for tv shows
for show in shows.search(filters={"addedAt>>": "7d"}):
    showDetails = []
    showTitle = show.title
    showSeasons = show.seasonCount

    newShow = showTitle + " - " + str(showSeasons) + " season(s)"

    newMedia.append(newShow)

# Convert media to json for HTTP request below
json_new = json.dumps(newMedia)
# URI to Send an HTTP post request to a Power Automate flow
flowURI = ""
# Headers
headers = {'Content-Type': 'application/json', 'Accept':'application/json'}
# send the request
r = requests.post(flowURI, data=json_new, headers=headers)

# Power Automate is a paid service so this is highly customizable to manipulate however needed.