# SpotifyCollector
This project consists of a Spotify data collector that uses the Spotify API Wrapper written in Python named [Spotipy](https://github.com/plamere/spotipy).

## Installation and environment setup
To run this code locally you need MySQL installed in your machine. The installation of Python dependencies are as follows:
```
$ pip install spotipy
$ pip install MySQL-python
```

After everything is good to go we are still missing the database structure. Solve this by running the following in your MySQL command line:
```
mysql> source $PATH_TO_PROJECT/create_db.sql
```

## Usage
Program call:
```
$ python collector.py artist_limit,artist_offset playlist_limit,playlist_offset [-v]
```

Clear data stored on tables:
```
mysql> source $PATH_TO_PROJECT/clear_db.sql
```

Delete database:
```
mysql> source $PATH_TO_PROJECT/delete_db.sql
```