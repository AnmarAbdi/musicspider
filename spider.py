from flask import Flask, request, redirect, render_template

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def create_playlist():
    if request.method == "POST":
        aplink = request.form.get('apple_music_playlist_url')
        return "Your name is " + aplink
    return render_template('index.html', link='apple_music_playlist_url')
    


if __name__ == "__main__":
    app.run()