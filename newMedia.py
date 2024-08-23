from plexapi.server import PlexServer
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from io import BytesIO
import xmltodict

# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Resource used https://python-plexapi.readthedocs.io/en/latest/index.html
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# baseURL - This is the URL of your media server, it is typically just your ipv4 address with port 32400 ex: http://0.0.0.0:32400
# token - You need this to access your server, you can find this by clicking the three dots in the bottom right corner of any media
#           and select "Get Info". Next select "View XML" in the bottom left of the pop-up, and search through the url (of the new window)
#           until you find "Plex-Token=". This is your token.
# plex - create the connection to your server.
baseURL = 'http://localhost:32400'
token = ''
plex = PlexServer(baseURL, token)

# These depend on the name of your libray
movies = plex.library.section('Movies')
shows = plex.library.section('TV Shows')
# To store newly added media
newMedia = []

html = f"""
    <html>
        <body>
            <h1>New Movies</h1>
    """

smtp_s = "smtp.gmail.com"
# smtp email and password (Gmail App Password if 2FA is enabled)
smtp_e = ""
smtp_p = ""

port = 587

# From email, FYI gmail doesn't let you set the from email, it will use the smtp one.
from_e = ""
# recipients 
bcc_emails = []
subject = "New to Plex this week!"

message = MIMEMultipart('alternative')
message["Subject"] = subject
message["From"] = from_e
# required for bcc to work, can be a dummy email
message["To"] = from_e

# Search through the movie library for media added within the last 7 days
for movie in movies.search(filters={"addedAt>>": "7d"}):
    print(movie.key)
    if movie is not None:
        # Gather the details you want
        movieDetails = []
        movieTitle = movie.title
        moviePoster = baseURL + movie.thumb
        
        # Get the url of the movie poster
        response = requests.get(moviePoster, headers={'X-Plex-Token': token})
        # Get Movie XML response for dictionary to find tvdb ID
        response2 = requests.get(baseURL + movie.key, headers={'X-Plex-Token': token})

        # NOTE
        # I used two approaches here for my own sanity. Outlook and Gmail behave differently when it comes to displaying embedded images.
        # I had trouble getting the images stored on the plex server to display in Outlook using the CID method, no matter what they would not show. If you can figure this out be my guest.
        # In the end I am using two methods, first checking if the image can be found on the tvdb artworks website and second using the image found on plex.
        # The reason for this is because for older movies tvdb has a consistant format for storing artwork like so: https://artworks.thetvdb.com/banners/movies/1254/posters/1254.jpg (Twister)
        # As you can see the id "1254" is used in the image name. For newer movies they for some reason broke this consistancy like below:
        # https://artworks.thetvdb.com/banners/v4/movie/345738/posters/66709088879e1.jpg (Twisters). You can see that the id does not match the image name, making it impossible to identify.
        # Since it was only Outlook that was having issues, I decided to use both methods so that at least some of the movie posters would display in Outlook and all would show in Gmail.
        # Either work fine for the iOS native mail app.

        if response.status_code == 200:
            # dictionary of response2's xml return
            d = xmltodict.parse(response2.content)
            # Location of the tvdb ID e.g tvdb://339957
            tvdb_id = d["MediaContainer"]["Video"]["Guid"][2]["@id"].split("/")[-1]

            # tvdb stores all of the artworks(posters) here.
            tvdb_url = f"https://artworks.thetvdb.com/banners/movies/{tvdb_id}/posters/{tvdb_id}.jpg"

            # Check if the response is image/jpeg and not application/xml. The later would be if the tvdb artwork ID and image name do not match.
            response3 = requests.get(tvdb_url)
            content_type = response3.headers.get('Content-Type', '')

            if content_type != "image/jpeg":
                # Convert plex data to a useable image.
                poster_data = BytesIO(response.content)
                img = MIMEImage(response.content)
                # Crucial as CID's can not have spaces
                cid = movieTitle.replace(' ', '_')
                img.add_header('Content-ID', f'<{cid}>')
                # So the images don't show as attachments in Gmail
                img.add_header('Content-Disposition', 'inline')
                message.attach(img)

                html += f"""
                            <table align="center" style="margin: 0 auto;">
                                <tr>
                                    <td style="text-align:center;">   
                                        <h2>{movieTitle}</h2>
                                        <img src="cid:{cid}" alt="{movieTitle}" style="width:200px;">
                                    </td>
                                </tr>
                            </table> 
                            <br>            
                            """

            else:
                html += f"""
                            <table align="center" style="margin: 0 auto;">
                                <tr>
                                    <td style="text-align:center;">   
                                        <h2>{movieTitle}</h2>
                                        <img src="https://artworks.thetvdb.com/banners/movies/{tvdb_id}/posters/{tvdb_id}.jpg" alt="{movieTitle}" style="width:200px;">
                                    </td>
                                </tr>
                            </table> 
                            <br>            
                            """
        else:
            print(f"Failed to retrieve image for {movieTitle}")


html += f"""
    </body></html>
"""


html_body = MIMEText(html, "html")
message.attach(html_body)

try:
    with smtplib.SMTP(smtp_s, port) as server:
        server.starttls()
        server.login(smtp_e, smtp_p)
        server.sendmail(from_e, bcc_emails, message.as_string())
    print("Email sent")
except Exception as e:
    print(f"Error: {e}")

exit()