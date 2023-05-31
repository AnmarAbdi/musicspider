from flask import Flask, request, redirect, render_template, session
from bs4 import BeautifulSoup
import requests # To scrape HTML from page
from dotenv import load_dotenv
import os
import json

dotenv_path = os.path.join(os.path.dirname(__file__), '.gitignore', '.env')
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
        songlist = []
        artistlist = []
        aplink = request.form.get('apple_music_playlist_url')
        source = requests.get(aplink).text
        soup = BeautifulSoup(source, 'html.parser')
        
        for title in soup.find_all('div', 'songs-list-row__song-name'):
            isotitles = format(title.text)  # format titles as text
            songlist.append(isotitles)  # add each song title to songlist
        
        for artist in soup.find_all('div', 'songs-list-row__by-line'):
            isoartist = format(artist.text)
            
            # Handling multiple artists separated by comma
            artists = []
            current_artist = ""
            within_quotes = False
            for char in isoartist:
                if char == "," and not within_quotes:
                    artists.append(current_artist.strip())
                    current_artist = ""
                else:
                    if char == '"':
                        within_quotes = not within_quotes
                    current_artist += char
            artists.append(current_artist.strip())
            
            artistlist.append(artists)
        
        if len(songlist) == len(artistlist):
            matched = []
            for i in range(len(songlist)):
                artists = artistlist[i]
                for artist in artists:
                    matched.append((songlist[i], artist))
            session['songs'] = matched
            print(session['songs'])
            return redirect('/create_playlist')

    return render_template('index.html', link='apple_music_playlist_url')


@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    access_token = session.get('access_token')
    print("ACCESS TOKEN:")
    print(access_token)
    if not access_token:
        # If user not logged in, redirect to Spotify login page
        auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
        print(SCOPES)
        return redirect(auth_url)
    songs = session.get('songs')
    print("FIRST PLAYLIST CHECK")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    print("2nd C?HECK")
    user_id = session.get('user_id')
    print("TRYING TO GET THE USER ID!")
    if not user_id:
        user_info_response = requests.get(
            "https://api.spotify.com/v1/me",
            headers=headers
        )
        print("GOT THE USER ID")
        if user_info_response.status_code == 401:
            # Access token expired, refresh token
            refresh_token = session.get('refresh_token')
            if not refresh_token:
                return "Refresh token is missing."
            
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
            refresh_response = requests.post(TOKEN_URL, data=refresh_data)
            refresh_response.raise_for_status()
            refresh_token_info = refresh_response.json()
            access_token = refresh_token_info['access_token']
            session['access_token'] = access_token
            headers['Authorization'] = f"Bearer {access_token}"

            # Retry getting user info
            user_info_response = requests.get(
                "https://api.spotify.com/v1/me",
                headers=headers
            )

        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        user_id = user_info.get('id')
        session['user_id'] = user_id

    if not user_id:
        return "User ID is missing."
    print("TRYING TO CREATE PLAYLIST")
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
    response.raise_for_status()  # This will raise an exception if the request failed
    playlist_id = response.json()['id']
    print("CREATED PLAYLIST")
    # Now add songs to the playlist
    # First, find the Spotify URIs for each song
    song_uris = []
    print(songs)
    for song_title, artist in songs:
        response = requests.get(
            f"https://api.spotify.com/v1/search?q=track:{song_title}%20artist:{artist}&type=track&limit=1",
            headers=headers
        )
        response.raise_for_status()
        tracks = response.json()['tracks']['items']
        if tracks:
            # If a track was found, add its URI to the list
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
    # Your playlist creation code here.^
    print(response.json())
    return render_template('index.html', link='apple_music_playlist_url')


@app.route('/callback')
def callback():
    # The user is redirected back to your app with the authorization code
    code = request.args.get('code')

    # Request access and refresh tokens
    auth = (CLIENT_ID, CLIENT_SECRET)
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, auth=auth, data=data)
    token_info = response.json()
    access_token = token_info['access_token']
    refresh_token = token_info['refresh_token']

    # Store the access and refresh tokens in session
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token

    return redirect('/create_playlist')


if __name__ == "__main__":
    app.run()