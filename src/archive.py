import getopt
import os
import pathlib
import shutil
import subprocess
import sys
import re

import mutagen
from tqdm import tqdm

ALBUM_FORMAT = '${artist} - ${album} (${date})'

METADATA_TRACK_TITLE = 'TIT2'
TITLE_KEY = 'title'
ALBUM_KEY = 'album'
GENRE_KEY = 'genre'
YEAR_KEY = 'ORIGINALYEAR'
TRACK_NUM_KEY = 'track.num'
ARTIST_KEY = 'artist'


def format_album(artist: str, album: str, date: str) -> str:
    ret = ALBUM_FORMAT.replace('${artist}', artist.replace("/", "-").replace(":", "-"))
    ret = ret.replace('${album}', album.replace("/", "-").replace(":", "-"))
    ret = ret.replace('${date}', date)
    return ret


def extract_album_title_formatted_mp3(uri: str) -> str:
    f = mutagen.File(uri)
    return format_album(str(f['TPE1']), str(f.tags['TALB']), str(f.tags['TDRC']))


def extract_album_title_formatted_flac(uri: str) -> str:
    f = mutagen.File(uri)
    
    try:
        year = f.tags[YEAR_KEY][0]
    except KeyError:
        try:
            year = f.tags['originaldate'][0]
        except KeyError:
            year = f.tags['date'][0]
    return format_album(f.tags[ARTIST_KEY][0], f.tags[ALBUM_KEY][0], year)


def extract_album_title_formatted_m4a(uri: str) -> str:
    f = mutagen.File(uri)
    return format_album(f.tags['©ART'][0], f.tags['©alb'][0], f.tags['©day'][0])


SUPPORTED_FORMATS = ['.flac', '.mp3', '.m4a', '.ogg']
ALBUM_TITLE_STRATEGY = {
    '.flac': extract_album_title_formatted_flac,
    '.m4a': extract_album_title_formatted_m4a,
    '.mp3': extract_album_title_formatted_mp3,
    '.ogg': extract_album_title_formatted_flac
}


def extract_album_title_formatted(uri: str) -> str:
    _, extension = os.path.splitext(uri)
    return ALBUM_TITLE_STRATEGY[extension](uri)


def fingerprint_album(album_path: str) -> bool:
    random_track_path = get_random_track_path(album_path)
    last_modified = os.path.getmtime(random_track_path)
    
    devnull = open(os.devnull, 'w')
    process = subprocess.Popen("picard '" + album_path + "'", shell=True, stdout=devnull, stderr=subprocess.STDOUT)
    process.wait()
    return last_modified != os.path.getmtime(random_track_path)


def type_filter(path: str, types):
    return pathlib.Path(path).suffix.lower() in types


def get_album_dirs(path: str) -> list:
    album_dirs = []
    for path, _ in get_all_files(path):
        if path not in album_dirs:
            album_dirs.append(path)
    
    album_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return album_dirs


def get_all_files(path: str) -> dict:
    print('Scanning folder \'%s\' for files of type(s) \'%s\'' % (path, SUPPORTED_FORMATS))

    for (path, _, files) in os.walk(path):

        for file in files:
            if not type_filter(file, SUPPORTED_FORMATS):
                continue

            full_path = os.path.join(path, file)
            yield path, os.path.getmtime(full_path)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def get_random_track_path(path: str, suffix_filter: list = SUPPORTED_FORMATS) -> str:
    for (path, dirs, files) in os.walk(path):

        for file in files:
            if not type_filter(file, suffix_filter):
                continue
            return os.path.join(path, file)


def move_and_create_dir(album_source_path: str, sorted_path, artist, suggested_album_title: str) -> None:
    album_destination_path = os.path.join(sorted_path, artist, suggested_album_title)
    if query_yes_no("Would you like to move %s to %s? " % (album_source_path, album_destination_path)):
        if not os.path.isdir(album_destination_path):
            os.makedirs(album_destination_path)

        clear_existing_tracks(sorted_path, artist, suggested_album_title)

        for file in tqdm(os.listdir(album_source_path)):
            full_file_name = os.path.join(album_source_path, file)
            shutil.move(full_file_name, album_destination_path)


def clear_existing_tracks(sorted_path: str, artist: str, suggested_album_title: str) -> None:
    existing_album_paths = get_existing_library_album_paths(sorted_path, artist, suggested_album_title)

    for existing_album_path in existing_album_paths:
        music_files = []
        populated = False
        for file in os.listdir(existing_album_path):
            if pathlib.Path(file).suffix.lower() not in SUPPORTED_FORMATS:
                continue
            populated = True
            to_delete = os.path.join(existing_album_path, file)
            music_files.append(to_delete)
            print("\t" + to_delete)
        
        if populated and query_yes_no("Delete found existing files first?"):
            for music_file in tqdm(music_files):
                remove_file(music_file)


def get_existing_library_album_paths(sorted_path: str, artist: str, suggested_album_title: str) -> list:
    """
    Looks for possible existing albums in the library
    :param sorted_path:
    :param artist:
    :param suggested_album_title:
    :return:
    """
    ret = []
    artist_path = os.path.join(sorted_path, artist)
    album_no_artist = suggested_album_title.split(artist + ' - ')[1].strip()
    album_no_artist_no_date = re.sub(r"\(.*\)", "", album_no_artist).strip()

    for existing_album_dir in os.listdir(artist_path):
        album_no_artist = re.sub(artist, "", existing_album_dir, flags=re.IGNORECASE).strip(' -_')
        existing_album_no_artist_no_date = re.sub(r"\(.*\)", "", album_no_artist).strip()
        
        print(existing_album_no_artist_no_date + ' <-- ' + existing_album_dir)
        if existing_album_no_artist_no_date == album_no_artist_no_date:
            ret.append(os.path.join(artist_path, existing_album_dir))

    return ret


def remove_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
    else:
        print("The file does not exist")


def parse_args(argv):
    input_file = ''
    output_file = ''
    try:
        opts, _ = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg
    return input_file, output_file


def main(argv):
    input_path, sorted_path = parse_args(sys.argv[1:])
    
    for album_dir in get_album_dirs(input_path):
        if not query_yes_no("Archive album directory '%s'?" % album_dir):
            if query_yes_no("Delete album directory? '%s'?" % album_dir):
                shutil.rmtree(album_dir, ignore_errors=True)
            continue
        
        print("processing %s" % album_dir)
        if fingerprint_album(album_dir):
            print("Files modified.")
        else:
            print("Files not modified.")
        
        suggested_album_title = extract_album_title_formatted(get_random_track_path(album_dir))
        artist = suggested_album_title.split(' - ')[0]

        # album_destination_path = os.path.join(sorted_path, artist, suggested_album_title)
        input_path = os.path.join(input_path, album_dir)
        move_and_create_dir(input_path, sorted_path, artist, suggested_album_title)


if __name__ == "__main__":
    main(sys.argv[1:])