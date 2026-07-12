import csv
import time
import requests
import sys
from config import LASTFM_API_KEY

class LastFMProgressSpinner:

    def __init__(self, total_songs):
        self.total_songs = total_songs
        self.current_song = 0
        self.dot_states = ["   ", ".  ", ".. ", "..."]
        self.idx = 0

    def spin(self, updated, failed):

        sys.stdout.write(
            f"\rUpdating{self.dot_states[self.idx]} "
            f"{self.current_song}/{self.total_songs} songs | "
            f"Updated: {updated} | "
            f"Failed: {failed}\033[K"
        )

        sys.stdout.flush()

        self.idx = (self.idx + 1) % len(self.dot_states)


    def update_count(self):
        self.current_song += 1


    def finish(self, updated, failed):

        sys.stdout.write(
            f"\rFinished! "
            f"Updated: {updated} | "
            f"Failed: {failed}\n"
        )

        sys.stdout.flush()

def get_lastfm_info(title, artist):

    url = "https://ws.audioscrobbler.com/2.0/"

    search_params = {
        "method": "track.search",
        "track": title,
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    try:
        response = requests.get(
            url,
            params=search_params,
            headers={
                "User-Agent": "InstagramMusicUpdater/1.0"
            }
        )

        data = response.json()

        track = data["results"]["trackmatches"]["track"][0]

        corrected_title = track["name"]
        corrected_artist = track["artist"]


        tag_params = {
            "method": "artist.gettoptags",
            "artist": corrected_artist,
            "api_key": LASTFM_API_KEY,
            "format": "json"
        }


        tag_response = requests.get(
            url,
            params=tag_params,
            headers={
                "User-Agent": "InstagramMusicUpdater/1.0"
            }
        )


        tag_data = tag_response.json()


        genres = []

        for tag in tag_data["toptags"]["tag"][:2]:
            genres.append(tag["name"])


        return {
            "title": corrected_title,
            "artist": corrected_artist,
            "genre": ", ".join(genres)
        }


    except Exception:

        return None



def update_csv():

    with open(
        "instagram_music.csv",
        "r",
        encoding="utf-8"
    ) as csv_file:

        songs = list(csv.DictReader(csv_file))


    total_songs = len(songs)
    spinner = LastFMProgressSpinner(total_songs)

    updated_count = 0
    failed_count = 0


    for index, song in enumerate(songs, start=1):

        result = get_lastfm_info(
            song["Title"],
            song["Artist"]
        )

        if result:

            song["Title"] = result["title"]
            song["Artist"] = result["artist"]
            song["Genre"] = result["genre"]

            updated_count += 1

        else:

            failed_count += 1

        spinner.update_count()

        for _ in range(3):
            spinner.spin(
                updated_count,
                failed_count
            )
            time.sleep(.5)



    spinner.finish(
        updated_count,
        failed_count
    )


    with open(
        "instagram_music.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:


        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "Title",
                "Artist",
                "Duration",
                "Genre"
            ]
        )


        writer.writeheader()

        writer.writerows(songs)



update_csv()