import logging
import os
import pathlib
import tempfile
import uuid

import eyed3
from flask import Flask, request, send_file
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s",  datefmt='%Y-%m-%dT%H:%M:%S')

app = Flask(__name__)
CORS(app)


uploaded_files = {}


@app.post("/api/file")
def post_file():
    """Receive an mp3 file and return a UUID. Caller can use the UUID to make additional updates to the file before downloading it again."""
    file = request.files['file']
    file_location = os.path.join(tempfile.gettempdir(), 'uploads', f'{str(uuid.uuid4())}.mp3')
    pathlib.Path(file_location).parent.mkdir(parents=True, exist_ok=True)
    file.save(file_location)
    file_id = str(uuid.uuid4())
    uploaded_files[file_id] = file_location
    _initialize_tags(file_location)
    logging.info(f'Created file: {file_id}')
    return {'id': file_id}, 201


def _initialize_tags(file_location):
    """Remove all tags from the MP3 file except album, album artist, artist, title, disc number, and track number."""
    audio_file = eyed3.load(file_location)
    album, album_artist = audio_file.tag.album, audio_file.tag.album_artist
    artist, title = audio_file.tag.artist, audio_file.tag.title
    disc_number, track_number = audio_file.tag.disc_num[0], audio_file.tag.track_num[0]
    audio_file.tag.clear()
    audio_file.tag.album, audio_file.tag.album_artist = album, album_artist
    audio_file.tag.artist, audio_file.tag.title = artist, title
    audio_file.tag.disc_num, audio_file.tag.track_num = disc_number, track_number
    audio_file.tag.save()


@app.get("/api/file/<file_id>")
def get_file(file_id):
    """Download the specified file."""
    if file_id not in uploaded_files:
        return '', 404
    upload_location = uploaded_files[file_id]
    return send_file(upload_location)


@app.delete("/api/file/<file_id>")
def delete_file(file_id):
    """Delete the specified file. Once deleted, the file cannot be updated or downloaded."""
    if file_id not in uploaded_files:
        return '', 404
    os.remove(uploaded_files[file_id])
    del uploaded_files[file_id]
    return '', 204


@app.get("/api/file/<file_id>/tags")
def get_tags(file_id):
    """Get the tags currently assigned to the MP3 file."""
    if file_id not in uploaded_files:
        return '', 404
    file_location = uploaded_files[file_id]
    audio_file = eyed3.load(file_location)
    result = {
        'album': audio_file.tag.album,
        'album_artist': audio_file.tag.album_artist,
        'title': audio_file.tag.title,
        'artist': audio_file.tag.artist,
        'disc_num': audio_file.tag.disc_num[0],
        'track_num': audio_file.tag.track_num[0],
    }
    return result, 200


@app.patch("/api/file/<file_id>/tags")
def patch_tags(file_id):
    """Update a tag on the MP3 file."""
    if file_id not in uploaded_files:
        return '', 404
    upload_location = uploaded_files[file_id]
    audio_file = eyed3.load(upload_location)
    payload = request.get_json()
    tag, value = payload['tag'], payload['value']
    if tag == 'album':
        audio_file.tag.album = value
    elif tag == 'album_artist':
        audio_file.tag.album_artist = value
    elif tag == 'disc_num':
        audio_file.tag.disc_num = value
    elif tag == 'track_num':
        audio_file.tag.track_num = value
    elif tag == 'title':
        audio_file.tag.title = value
    elif tag == 'artist':
        audio_file.tag.aritst = value
    else:
        return f'Invalid tag: {tag}', 400
    audio_file.tag.save()
    return '', 200


@app.get("/api/file/<file_id>/comments")
def get_comments(file_id):
    """Get the comments currently assigned to the MP3 file."""
    if file_id not in uploaded_files:
        return '', 404
    upload_location = uploaded_files[file_id]
    audio_file = eyed3.load(upload_location)
    result = {}
    for comment in audio_file.tag.comments:
        result[comment.description] = comment.text
    return result, 200


@app.patch("/api/file/<file_id>/comments")
def patch_comments(file_id):
    """Add a comment to the MP3 file."""
    if file_id not in uploaded_files:
        return '', 404
    upload_location = uploaded_files[file_id]
    audio_file = eyed3.load(upload_location)
    payload = request.get_json()
    description, text = payload['description'], payload['text']
    audio_file.tag.comments.set(text, description)
    audio_file.tag.save()
    return '', 204


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080, use_reloader=False)
