#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import spotipy
import spotipy.util as util
import pprint
import MySQLdb

# WORK PLAN
# - Get 100000 artists and parse the data -> Populate Artist, ArtistGenre, ArtistAlbum(Missing in doc)
# - Get Album data from those artists -> Populate Album, AlbumTrack
# - Get Track data from those albums -> Populate Track, TrackArtist
# - Get Playlist by searching by Category, e.g., Party -> Populate Playlist, User, Track, PlaylistTrack(Missing in doc)

# TODO
# - Use argparse
# - Create README
# - OPTIONAL: Add followers number for every entity
# - Create try except to treat "The access token expired"
# - Find a way to get more users

#==============================OUTPUT SETUP===============================#

if len(sys.argv) > 6 and sys.argv[6] == "-v":  # Print if verbose flag was set
	def vprint(*args):
		for arg in args:
			print arg,
		print
else:   
	vprint = lambda *a: None  # Do-nothing function

pp = pprint.PrettyPrinter(indent=1)  # PrettyPrinter setup for better JSON visualization

#================================DB SETUP=================================#

db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="spotify")
cursor = db.cursor()

db.autocommit(True)  # Autocommit INSERTs to spotify DB
db.set_character_set('utf8')
cursor.execute('SET NAMES utf8;')
cursor.execute('SET CHARACTER SET utf8;')
cursor.execute('SET character_set_connection=utf8;')

#===============================SQL QUERIES===============================#

check_artist = ("SELECT COUNT(1) "
				"FROM Artist "
				"WHERE id = %s")

check_album = ("SELECT COUNT(1) "
				"FROM Album "
				"WHERE name = %s")

check_track = ("SELECT COUNT(1) "
				"FROM Track "
				"WHERE id = %s")

check_playlist = ("SELECT COUNT(1) "
				"FROM Playlist "
				"WHERE id = %s")

check_user = ("SELECT COUNT(1) "
				"FROM User "
				"WHERE id = %s")

insert_artist = ("INSERT INTO Artist "
				"(id, name, followers, popularity) "
				"VALUES (%s, %s, %s, %s)")

insert_artist_genre = ("INSERT INTO ArtistGenre "
						"(artist_id, genre) "
						"VALUES (%s, %s)")

insert_artist_album = ("INSERT INTO ArtistAlbum "
						"(artist_id, album_id) "
						"VALUES (%s, %s)")

insert_album = ("INSERT INTO Album "
				"(id, name, album_type, release_date, popularity) " 
				"VALUES (%s, %s, %s, %s, %s)")

insert_album_track = ("INSERT INTO AlbumTrack "
						"(album_id, track_id, disc_number, track_number) "
						"VALUES (%s, %s, %s, %s)")

insert_track = ("INSERT INTO Track "
				"(id, name, duration_ms, explicit, popularity) " 
				"VALUES (%s, %s, %s, %s, %s)")

insert_track_artist = ("INSERT INTO TrackArtist "
						"(track_id, artist_id) "
						"VALUES (%s, %s)")

insert_playlist = ("INSERT INTO Playlist "
				"(id, name, owner, description, followers, collaborative, public) " 
				"VALUES (%s, %s, %s, %s, %s, %s, %s)")

insert_playlist_track = ("INSERT INTO PlaylistTrack "
						"(playlist_id, track_id) " 
						"VALUES (%s, %s)")

insert_user = ("INSERT INTO User "
				"(id, display_name, followers) " 
				"VALUES (%s, %s, %s)")

#=================================METHODS=================================#

def exists_artist(artist):
	cursor.execute(check_artist, [artist['id']])
	return list(cursor)[0][0]

def exists_album(album):
	cursor.execute(check_album, [album['name']])  # Searches by name because duplicates have different ids
	return list(cursor)[0][0]

def exists_track(track):
	cursor.execute(check_track, [track['id']])
	return list(cursor)[0][0]

def exists_playlist(playlist):
	cursor.execute(check_playlist, [playlist['id']])
	return list(cursor)[0][0]

def exists_user(user):
	cursor.execute(check_user, [user['id']])
	return list(cursor)[0][0]

def get_artist(id):
	return sp.artist(id)

def get_album(id):
	return sp.album(id)

def get_track(id):
	return sp.track(id)

def get_playlist(user_id, playlist_id):
	return sp.user_playlist(user=user_id, playlist_id=playlist_id)

def get_user(id):
	return sp.user(id)

def save_artist(artist):
	vprint("[INSERT][ARTIST]", artist['name'])
	cursor.execute(insert_artist, (artist['id'], artist['name'], artist['followers']['total'], artist['popularity']))

def save_artist_genre(artist): 
	for genre in artist['genres']:
		vprint("[INSERT][ARTIST_GENRE]", artist['name'], ",", genre)
		cursor.execute(insert_artist_genre, (artist['id'], genre))

def save_artist_album(artist, album):
	vprint("[INSERT][ARTIST_ALBUM]", artist['name'], ",", album['name'])
	cursor.execute(insert_artist_album, (artist['id'], album['id']))

def save_album(album):
	vprint("[INSERT][ALBUM]", album['name'])
	cursor.execute(insert_album, (album['id'], album['name'], album['album_type'], album['release_date'], album['popularity']))

def save_album_track(album, track):
	vprint("[INSERT][ALBUM_TRACK]", album['name'], ",", track['name'])
	cursor.execute(insert_album_track, (album['id'], track['id'], track['disc_number'], track['track_number']))

def save_track(track):
	vprint("[INSERT][TRACK]", track['name'])
	cursor.execute(insert_track, (track['id'], track['name'], track['duration_ms'], int(track['explicit'] == True), track['popularity']))

def save_track_artist(track, artist):
	vprint("[INSERT][TRACK_ARTIST]", track['name'], ",", artist['name'])
	cursor.execute(insert_track_artist, (track['id'], artist['id']))

def save_playlist(playlist):
	vprint("[INSERT][PLAYLIST]", playlist['name'])
	if not exists_user(playlist['owner']):
		user = get_user(playlist['owner']['id'])
		save_user(user)
	cursor.execute(insert_playlist, (playlist['id'], playlist['name'], playlist['owner']['id'], playlist['description'], playlist['followers']['total'], int(playlist['collaborative'] == True), int(playlist['public'] == True)))

def save_playlist_track(playlist, track):
	vprint("[INSERT][PLAYLIST_TRACK]", playlist['name'], ",", track['name'])
	cursor.execute(insert_playlist_track, (playlist['id'], track['id']))

def save_user(user):
	vprint("[INSERT][USER]", user['display_name'])
	cursor.execute(insert_user, (user['id'], user['display_name'], user['followers']['total']))

def save_artist_albums(artist):
	albums = sp.artist_albums(artist['id'], limit=50)['items']  # Retrieves 50 simple album objects at most
	albums.sort(key=lambda album:album['name'].lower())  # Sort albums in alphabetical order
	seen = set()  # Avoid duplicates(There are lots in Spotify)
	for album in albums:
		if album['name'] not in seen and not exists_album(album):
			album = get_album(album['id'])  # Retrieves full album object
			save_entire_album(album)
			for artist in album['artists']:
				if not exists_artist(artist):
					artist = get_artist(artist['id'])
					save_entire_artist(artist)
				save_artist_album(artist, album)
			seen.add(album['name'])

def save_album_tracks(album):
	tracks = album['tracks']['items']
	for track in tracks:
		if not exists_track(track):  # Prevents unnecessary requests
			track = get_track(track['id'])  # Retrieves full track object
			save_entire_track(track)
			save_album_track(album, track)

def save_playlist_tracks(playlist):
	for track in playlist['tracks']['items']:
		track = track['track']
		if not exists_track(track):  
			save_entire_track(track)
		save_playlist_track(playlist, track)

# Saves artist and all of it's relations
def save_entire_artist(artist, save_albums=False): 
	if not exists_artist(artist):  # Only check for those two because maybe not all albums from an artist are saved
		save_artist(artist)
		save_artist_genre(artist)
	if save_albums: save_artist_albums(artist)  # If this is set in inner calls, starts artists recursion

def save_entire_album(album):
	save_album(album)
	save_album_tracks(album)

def save_entire_track(track):
	save_track(track)

	if not exists_album(track['album']): # Retrieves entire album for that track
		album = get_album(track['album']['id'])
		save_entire_album(album)  

	for artist in track['artists']:
		if not exists_artist(artist):
			artist = get_artist(artist['id'])
			save_entire_artist(artist)
		save_track_artist(track, artist)

def save_entire_playlist(playlist):
	save_playlist(playlist)
	save_playlist_tracks(playlist)

def retrieve_all_artists(limit, starting_offset):
	offset = starting_offset
	for i in range(limit / 50):  # Retrieves 50 at a time(API Endpoint Max Limit/Request)
		artists = sp.search(q='year:0000-9999', type='artist', market='US', limit=50, offset=offset)['artists']['items']
		for artist in artists:
			save_entire_artist(artist, save_albums=True)
		offset += 50
	remainder = limit % 50
	if remainder > 0:
		artists = sp.search(q='year:0000-9999', type='artist', market='US', limit=remainder, offset=offset)['artists']['items']
		for artist in artists:
			save_entire_artist(artist, save_albums=True)

def retrieve_all_playlists(limit, starting_offset, category_id, country):
	offset = starting_offset
	for i in range(limit / 50):  # Retrieves 50 at a time(API Endpoint Max Limit/Request)
		playlists = sp.category_playlists(category_id=category_id, country=country, limit=50, offset=offset)['playlists']['items']
		for playlist in playlists:
			if not exists_playlist(playlist):  # Prevents requesting if unnecessary
				playlist = get_playlist(playlist['owner']['id'], playlist['id'])  # Simplified object doesn't contain all the info we need
				save_entire_playlist(playlist)
		offset += 50
	remainder = limit % 50
	if remainder > 0:
		playlists = sp.category_playlists(category_id=category_id, country=country, limit=remainder, offset=offset)['playlists']['items']
		for playlist in playlists:
			if not exists_playlist(playlist):
				playlist = get_playlist(playlist['owner']['id'], playlist['id'])
				save_entire_playlist(playlist)

#===================================MAIN==================================#

if len(sys.argv) >= 6:
	username = sys.argv[1]
	artist_limit = int(sys.argv[2])
	artist_offset = int(sys.argv[3])
	playlist_limit = int(sys.argv[4])
	playlist_offset = int(sys.argv[5])
else:
	print "usage: %s username artist_limit artist_offset playlist_limit playlist_offset [-v]" % (sys.argv[0],)
	sys.exit()

scope = 'user-library-read'
token = util.prompt_for_user_token(username, scope, client_id = "791f489dbfac46009b49332c0897001c", client_secret = "39bfe9b8132441ab870b0157dc92bd52", redirect_uri = "https://example.com/callback/")

if token:
	sp = spotipy.Spotify(auth=token)

	if artist_limit > 100000:
		print "[ERROR] Maximum allowed limit is 100000. Limit has been resized."
		artist_limit = 100000

	retrieve_all_artists(artist_limit, artist_offset)
	retrieve_all_playlists(playlist_limit, playlist_offset, category_id='decades', country='BR')
else:
	print "Can't get token for", username

cursor.close()
db.close()