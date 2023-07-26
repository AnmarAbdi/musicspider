from flask import Flask, request, redirect, render_template, session
from bs4 import BeautifulSoup
import requests # To scrape HTML from page
from dotenv import load_dotenv
import os
import json
import mysql.connector

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_APP_SECRET')

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

AUTH_URL = "https://accounts.spotify.com/authorize"

# The Spotify Accounts service's token URL
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Your application's redirect URI and the required scopes
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPES = "playlist-modify-public playlist-modify-private"


@app.route('/')
def index():
    print("TESTTT================")
    return render_template('index.html')

@app.route('/', methods=['POST'])
def parse_playlist():
    if request.method == "POST":
        print("Starting PARSE!!!!!!!!!!!!!!!!!!!!!110000")
        """songlist = []
        artistlist = []"""
        aplink = request.form.get('apple_music_playlist_url')
        source = requests.get(aplink).text
        soup = BeautifulSoup(source, 'html.parser')

        cnx = mysql.connector.connect(
            user=os.getenv('DB_USER'), 
            password=os.getenv('DB_PASS'), 
            host=os.getenv('DB_HOST'), 
            database=os.getenv('DB_NAME')
        )
    
        # Get a cursor
        cursor = cnx.cursor()

        # find all song divs
        song_divs = soup.find_all('div', {'class': 'songs-list__col songs-list__col--song svelte-17mxcgw'})
        print("SONG DIVS")
        for div in song_divs:
            # find song name
            song_name_div = div.find('div', {'class': 'songs-list-row__song-name svelte-17mxcgw'})
            if song_name_div:
                song_name = song_name_div.text.strip()

            # find first artist name
            artist_name_a = div.find('a', {'class': 'click-action svelte-1nh012k'})
            if artist_name_a:
                artist_name = artist_name_a.text.strip()

            add_song = ("INSERT INTO songs "
                        "(title, artist) "
                        "VALUES (%s, %s)")

            # Insert new song
            data_song = (song_name, artist_name)
            cursor.execute(add_song, data_song)

        # Make sure data is committed to the database
        cnx.commit()

        cursor.close()
        cnx.close()
        return ":D"
        
        

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    access_token = session.get('access_token')
    if not access_token:
        auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
        return redirect(auth_url)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_id = session.get('user_id')
    if not user_id:
        # The same logic as before...
        # Get the user_id and access_token

    if not user_id:
        return "User ID is missing."

    # Create a new playlist
    create_playlist_data = {
        "name": "it worked>:D",
        "public": True
    }
    response = requests.post(
        f"https://api.spotify.com/v1/users/{session.get('user_id')}/playlists", 
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        data=json.dumps(create_playlist_data)
    )
    response.raise_for_status()
    playlist_id = response.json()['id']

    # Now add songs to the playlist
    song_uris = []

    # Connect to the database
    cnx = mysql.connector.connect(
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASS'), 
        host=os.getenv('DB_HOST'), 
        database=os.getenv('DB_NAME')
    )

    # Fetch songs from the database
    with cnx.cursor() as cursor:
        cursor.execute("SELECT title, artist FROM songs")
        songs = cursor.fetchall()

    for song_title, artist in songs:
        response = requests.get(
            f"https://api.spotify.com/v1/search?q=track:{song_title}%20artist:{artist}&type=track&limit=1",
            headers=headers
        )
        response.raise_for_status()
        tracks = response.json()['tracks']['items']
        if tracks:
            song_uris.append(tracks[0]['uri'])

    # Then, add these songs to the playlist
    add_songs_data = {
        "uris": song_uris
    }
    response = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        data=json.dumps(add_songs_data)
    )
    response.raise_for_status()

    cnx.close()

    return render_template('index.html', link='apple_music_playlist_url')


if __name__ == "__main__":
    app.run()