import os
import subprocess
import threading
import pypresence
import time
import pyimgur
import cv2
import json
import uuid
import dotenv


def skip_music():
    kill_ffplay = "taskkill /im ffplay.exe /f" if os.name == "nt" else "killall ffplay"
    while True:
        if input() == "":
            subprocess.call(kill_ffplay, stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
            break


def clear_terminal():
    os.system("cls || clear")


def get_low_res_cover_folder():
    covers = os.listdir("covers_low_res")
    for cover in covers:
        if not cover.endswith(".jpg"):
            covers.remove(cover)
    return covers


def get_cover_folder():
    covers = os.listdir("covers")
    for cover in covers:
        if not cover.endswith(".jpg"):
            covers.remove(cover)
    return covers


def upload_image():
    try:
        uploaded_image = IM.upload_image(
            f"covers/{song_name}.jpg", title=uuid.uuid4())
        uploaded_image = uploaded_image.link
        return uploaded_image
    except Exception as e:
        print(f"An error occurred while uploading the image to imgur:\n{e}")
        return "player"


def set_RPC(image="player", info_song="Unknown", info_artist="Unknown", info_album="Unknown", info_year="Unknown"):
    timer = time.time()
    RPC.update(details=f"Playing: {info_song} {info_year} from {info_artist}",
               start=timer, state=f"Album: {info_album}", large_image=image, large_text=info_song)


clear_terminal()

dotenv.load_dotenv()

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
IM = pyimgur.Imgur(IMGUR_CLIENT_ID)
CLIENT_ID = os.getenv("CLIENT_ID")
RPC = pypresence.Presence(CLIENT_ID)
RPC.connect()

playlist = os.listdir("music")

for song in playlist:
    if not song.endswith(".flac"):
        playlist.remove(song)

print("Press enter to skip")

for song in playlist:
    song_name = song.replace(".flac", "")
    print("Playing", song_name)

    covers = get_cover_folder()
    covers_low_res = get_low_res_cover_folder()

    if f"{song_name}.jpg" not in covers_low_res:
        get_music_cover = f'ffmpeg -i "music/{song}" -map 0:v -map -0:V -c copy "covers_low_res/{song_name}.jpg"'
        subprocess.call(get_music_cover, stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT)

    covers_low_res = get_low_res_cover_folder()

    if f"{song_name}.jpg" not in covers and f"{song_name}.jpg" in covers_low_res:
        image_low_res = cv2.imread(f"covers_low_res/{song_name}.jpg")
        image = cv2.resize(image_low_res, (1024, 1024),
                           interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite(f"covers/{song_name}.jpg", image)

    covers = get_cover_folder()

    if f"{song_name}.jpg" in covers:
        uploaded_image = upload_image()
    else:
        uploaded_image = "player"

    get_music_info = f'ffprobe -v quiet -print_format json -show_format "music/{song}"'
    output = subprocess.run(get_music_info, capture_output=True)
    data = json.loads(output.stdout)

    info_song = data['format']['tags'].get("TITLE", "Unknown").split(";", 1)[0]
    info_artist = data['format']['tags'].get(
        "ARTIST", "Unknown").split(";", 1)[0]
    info_album = data['format']['tags'].get("ALBUM", "Unknown")
    info_year = data['format']['tags'].get("YEAR", None)

    if not info_year:
        info_year = data['format']['tags'].get("DATE", "Unknown")

    t = threading.Thread(target=skip_music)
    t.start()

    set_RPC(uploaded_image, info_song, info_artist, info_album, info_year)

    play_music = f'ffplay -autoexit -nodisp "music/{song}"'
    ffplay = subprocess.call(play_music, stdout=subprocess.DEVNULL,
                             stderr=subprocess.STDOUT)
    clear_terminal()

clear_terminal()
print("Finished playing!")
RPC.close()
exit()
