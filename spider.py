from flask import Flask, request, redirect, render_template
from bs4 import BeautifulSoup
import requests # To scrape HTML from page


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def create_playlist():
    if request.method == "POST":
        songlist = []
        artistlist = []
        aplink = request.form.get('apple_music_playlist_url')
        source = requests.get(aplink).text
        soup = BeautifulSoup(source, 'html.parser')
        for title in soup.find_all('div', 'songs-list-row__song-name'):
            isotitles = (format(title.text)) #formats titles as text
            songlist.append(isotitles) # adds each song title to songlist
        for artist in soup.find_all('div', 'songs-list-row__by-line'):
            isoartist = (format(artist.text))
            artistlist.append(isoartist)
        if len(songlist) == len(artistlist):
            matched = list(zip(songlist, artistlist))
            return matched

    

    
    
    return render_template('index.html', link='apple_music_playlist_url')
    





if __name__ == "__main__":
    app.run()