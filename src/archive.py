import getopt
import os
import pathlib
import shutil
import subprocess
import sys

import mutagen


SUPPORTED_FORMATS = ['.flac', '.mp3', '.m4a', '.ogg']

METADATA_TRACK_TITLE = 'TIT2'
TITLE_KEY = 'title'
ALBUM_KEY = 'album'
GENRE_KEY = 'genre'
YEAR_KEY = 'ORIGINALYEAR'
TRACK_NUM_KEY = 'track.num'
ARTIST_KEY = 'artist'


def extract_album_title_formatted(uri: str) -> str:
    _, extension = os.path.splitext(uri)
    return extract_album_title_formatted_mp3(uri) if extension == ".mp3" else extract_album_title_formatted_flac(uri)

    
def extract_album_title_formatted_mp3(uri: str) -> str:
    f = mutagen.File(uri)
    return '{} - {} ({})'.format(str(f['TPE1']), str(f.tags['TALB']), str(f.tags['TDRC']))


def extract_album_title_formatted_flac(uri: str) -> str:
    f = mutagen.File(uri)
    
    try:
        year = f.tags[YEAR_KEY][0]
    except KeyError:
        year = f.tags['originaldate'][0]
    return '{} - {} ({})'.format(f.tags[ARTIST_KEY][0], f.tags[ALBUM_KEY][0], year)


def fingerprint_album(album_path: str) -> bool:
    random_track_path = get_random_track_path(album_path)
    last_modified = os.path.getmtime(random_track_path)
    
    devnull = open(os.devnull, 'w')
    process = subprocess.Popen("picard '" + album_path + "'", shell=True, stdout=devnull, stderr=subprocess.STDOUT)
    process.wait()
    return last_modified != os.path.getmtime(random_track_path)


def type_filter(path: str, types):
    return pathlib.Path(path).suffix.lower() in types


def get_album_dirs(path: str, suffix_filter: list = SUPPORTED_FORMATS) -> list:
    album_dirs = []
    for path, timestamp in get_all_files(path, suffix_filter):
        if path not in album_dirs:
            album_dirs.append(path)
    
    album_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return album_dirs


def get_all_files(path: str, suffix_filter: list = SUPPORTED_FORMATS) -> dict:
    print('Scanning folder \'%s\' for files of type(s) \'%s\'' % (path, suffix_filter))

    for (path, dirs, files) in os.walk(path):

        for file in files:
            if not type_filter(file, suffix_filter):
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


def move_and_create_dir(source_path, target_dir) -> None:
    if query_yes_no("Would you like to move %s to %s? " % (source_path, target_dir)):
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        for file in os.listdir(source_path):
            full_file_name = os.path.join(source_path, file)
            shutil.move(full_file_name, target_dir)


def parse_args(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=","ofile="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    return inputfile, outputfile


def main(argv):
    input_path, sorted_path = parse_args(sys.argv[1:])
    
    for album_dir in get_album_dirs(input_path):
        if not query_yes_no("Would you like to archive album directory '%s'?" % album_dir):
            if query_yes_no("Would you like to stop? "):
                break
            continue
        
        print("processing %s" % album_dir)
        if fingerprint_album(album_dir):
            print("Files modified.")
        else:
            print("Files not modified.")
        
        suggested_name = extract_album_title_formatted(get_random_track_path(album_dir))
        artist = suggested_name.split(' - ')[0]
        
        suggested_path = os.path.join(sorted_path, artist, suggested_name)
        input_path = os.path.join(input_path, album_dir)
        move_and_create_dir(input_path, suggested_path)


if __name__ == "__main__":
    main(sys.argv[1:])