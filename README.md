# music-archiver
[![CircleCI](https://circleci.com/gh/jaivalis/music-archiver.svg?style=shield)](https://circleci.com/gh/jaivalis/music-archiver)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c8dc1fb06fad400cb2e4ad0307b45a58)](https://www.codacy.com/manual/jaivalis/music-archiver?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=jaivalis/music-archiver&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/c8dc1fb06fad400cb2e4ad0307b45a58)](https://www.codacy.com/manual/jaivalis/music-archiver?utm_source=github.com&utm_medium=referral&utm_content=jaivalis/music-archiver&utm_campaign=Badge_Coverage)

Utility used to tag and archive downloaded **albums** to library.
Point to a downloads folder and to a sorted library target directory.
The downloads folder may contain multiple albums, it will be scanned as such and tag them in order of modification.

## Use
Two arguments need to be provided, the input and output directory:
``` console
pip install -r requirements.txt
python archive.py -i "${HOME}/Downloads/complete" -o ${HOME}/Music/Sorted
```

### Archive
The resulting structure will include a directory per artist and a directory under that per album following the following naming pattern: 

<artist_name> - <album_name> (<relase_date>)

(Audio file names are not altered.)

The resulting structure in the directory pointed to is as follows:
``` console
.
├── Kurt Vile
│   └── Kurt Vile - Bottle It In (2018)
│       ├── 01-Loading Zones.flac
│       ├── 02-Hysteria.flac
.       .
.       .
.       .
│       └── 13-(bottle back).flac
└── Kraftwerk
    └── Kraftwerk - The Man-Machine (1978)
        ├── 01-The Robots-Kraftwerk.mp3
        .
        .
        .
        └── 06-The Man Machine-Kraftwerk.mp3
```

Important to notice that the assumption is that albums and not single tracks are downloaded.
Determining of the target directory for each folder is done with this as a given.

### Tagging
Tagging needs to be validated manually per album and saved.
For each given album picard will be launched on that directory and the files need to be searched for, tagged and saved.
Once picard exits (simply close the program after saving changes) you will be prompted to save the resulting files in the archive.

## Requirements
You will need musicbranz's [picard](https://musicbrainz.org/doc/Picard_Linux_Install) in order to fetch tags

On ubuntu, it can be installed by running the following:

`sudo apt get install picard`

## Install
For ease of use you can save this script and an alias on the profile so it's usable without having to specify the args every time.

``` console
$ sudo cp src/archive.py /opt/bin/
$ echo  'alias archivm='python /opt/bin/archive.py -i "${HOME}/Downloads/complete" -o "${HOME}/Music/Sorted"'
' >> ~/.zshrc 
```