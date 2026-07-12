from playwright.sync_api import sync_playwright
from config import instagram_username
import csv
import os
import sys
import time
import subprocess

""" 
Ig Music Sheets

1. This program will open instagram using playwright using
your most recent login session (it's best to login to instagram first).

2. Forward to the saved music page, record all of the saved music
entries

3. Save the music entries into a CSV file, parsing the artist name, title,
and genre

Instagram often changes its website and so selectors may need updating.
"""

class PlaywrightProgressSpinner:
    """Manages a terminal progress indicator with cycling dots (. .. ...) and a user-defined target count."""

    def __init__(self):
        self.songs_found = 0
        self.dot_states = ["   ", ".  ", ".. ", "..."]
        self.idx = 0

    def spin_once_song(self):
        """Advances the dots cycle by one frame and updates the current count."""
        sys.stdout.write(
            f"\rWorking{self.dot_states[self.idx]} {self.songs_found} songs found\033[K")
        sys.stdout.flush()
        self.idx = (self.idx + 1) % len(self.dot_states)

    def spin_one_navigation(self):
        sys.stdout.write(
            f"\rNavigating to audio page{self.dot_states[self.idx]}")

        sys.stdout.flush()
        self.idx = (self.idx + 1) % len(self.dot_states)


    def update_count(self, count):
        self.songs_found = count

    def stop_song_find(self):
        sys.stdout.write(f"\rFinished collecting! {self.songs_found} songs found.\n")
        sys.stdout.flush()

    def stop_search(self):
        sys.stdout.write(f"\rSaved audio page opened!")
        sys.stdout.flush()

def log_into_session():

    with sync_playwright() as p:

        # opens Chromium browsers/makes it visible
        browser = p.chromium.launch(headless=False)

        # creating a new browser session, and tap
        context = browser.new_context()
        page = context.new_page()

        # navigates to instagram login page
        page.goto("https://www.instagram.com/accounts/login/")

        print("Log into Instagram. Once logged in, window will close.")

        # when user successfully log in
        while True:
            # gets current url
            current_url = page.url
            # If we are no longer on the login page
            if "login" not in current_url:
                break

            page.wait_for_timeout(1000)

        # save login information into json file (cookies)
        context.storage_state(path="instagram_state.json")
        print("Login saved")

        browser.close()

def export_music():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="instagram_state.json")
        page = context.new_page()

        progress_spinner = PlaywrightProgressSpinner()

        progress_spinner.spin_one_navigation()
        page.goto(
            f"https://www.instagram.com/{instagram_username}/saved/audio/",
            wait_until="domcontentloaded")

        while page.url.endswith("/saved/audio/") and page.locator('a[href*="/reels/audio/"]').count() == 0:
            progress_spinner.spin_one_navigation()
            time.sleep(1)

        progress_spinner.stop_search()


        # waits until instagram is finished loading
        page.wait_for_load_state("networkidle")
        progress_spinner.stop_search()


        saved_songs = [] # stores every song recorded
        seen_urls = set()
        no_new_songs = 0

        while True:
            before_song_count_check = len(saved_songs)

            # finds all audio links
            song_links = page.locator('a[href*="/reels/audio/"]')
            song_link_count = song_links.count()

            # inspects every loaded song
            for song_number in range(song_link_count):

                # selects one song from the list
                song = song_links.nth(song_number)
                # obtains songs unique url to check for duplicates
                song_url = song.get_attribute("href")

                if song_url not in seen_urls:
                    seen_urls.add(song_url)
                    song_container = song.locator("xpath=..")
                    # makes sure all information is present (url,title,artist,duration)
                    song_information = song_container.inner_text().split("\n")


                    if len(song_information) >= 4:
                        saved_songs.append({
                            "url": song_url,
                            "title": song_information[0],
                            "artist": song_information[1],
                            "duration": song_information[3]
                        })

                        progress_spinner.update_count(len(saved_songs))

                progress_spinner.spin_once_song()
            after_song_count_check = len(saved_songs)

            # checks if new songs were added
            if after_song_count_check == before_song_count_check:
                no_new_songs += 1
            else:
                no_new_songs = 0

            if no_new_songs >= 3:
                break

            # scroll to find new songs
            page.mouse.wheel(0,1500)
            for _ in range(20):
                page.wait_for_timeout(500)
                progress_spinner.spin_once_song()

        progress_spinner.stop_song_find()


        total_songs = len(saved_songs)
        songs_to_print = (int(input(f"\nHow many do you want to print? ")))

        with open("instagram_music.csv", "w",
                  newline="",
                  encoding="utf-8"
                  ) as details:

            writer = csv.DictWriter(details, fieldnames=["Title",
                                                         "Artist",
                                                         "Duration",
                                                         "Genre"])
            writer.writeheader()

            for song in saved_songs[:songs_to_print]:
                writer.writerow({"Title": song["title"],
                                 "Artist": song["artist"],
                                 "Duration": song["duration"],
                                 "Genre": ""})

        print("CSV file made successfully!")
        subprocess.run(["python", "Instagram Music Sheet (updater).py"])

        browser.close()

# main program
if os.path.exists("instagram_state.json"):
    print("Login already saved, Moving forward!")
    export_music()
else:
    log_into_session()
    export_music()







