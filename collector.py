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
# - Check if the API will accept all those requests. If not, simplify DB by using simplified object types.
# - Recheck pass on exceptions for relationship table insertions
# - Use argparse
# - Create README
# - Add followers number for every entity
# - Rearrange functions
# - Substitute Exceptions with Table Checks

#==============================OUTPUT SETUP===============================#

if len(sys.argv) > 4 and sys.argv[4] == "-v":  # Print if verbose flag was set
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

insert_artist = ("INSERT INTO Artist "
				"(id, name, popularity) "
				"VALUES (%s, %s, %s)")

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
				"(id, name, owner, description, collaborative, public) " 
				"VALUES (%s, %s, %s, %s, %s, %s)")

insert_playlist_track = ("INSERT INTO PlaylistTrack "
						"(playlist_id, track_id) " 
						"VALUES (%s, %s)")

insert_user = ("INSERT INTO User "
				"(id, display_name) " 
				"VALUES (%s, %s)")

#================================FUNCTIONS================================#

def retrieve_all_artists(limit):
	offset = 0
	for i in range(limit / 50):  # Retrieves 50 at a time(API Endpoint Max Limit/Request)
		artists = sp.search(q='year:0000-9999', type='artist', market='US', limit=50, offset=offset)['artists']['items']
		for artist in artists:
			save_entire_artist(artist, album_flag=True)
		offset += 50
	remainder = limit % 50
	if remainder > 0:
		artists = sp.search(q='year:0000-9999', type='artist', market='US', limit=remainder, offset=offset)['artists']['items']
		for artist in artists:
			save_entire_artist(artist, album_flag=True)

def retrieve_all_playlists(limit, category_id, country):
	offset = 0
	for i in range(limit / 50):  # Retrieves 50 at a time(API Endpoint Max Limit/Request)
		playlists = sp.category_playlists(category_id=category_id, country=country, limit=50, offset=offset)['playlists']['items']
		for playlist in playlists:
			save_entire_playlist(playlist)
		offset += 50
	remainder = limit % 50
	if remainder > 0:
		playlists = sp.category_playlists(category_id=category_id, country=country, limit=remainder, offset=offset)['playlists']['items']
		for playlist in playlists:
			playlist = get_playlist(playlist['owner']['id'], playlist['id'])
			save_entire_playlist(playlist)

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

# Saves artist and all of it's relations
def save_entire_artist(artist, album_flag=False): 
	save_artist(artist)
	save_artist_genre(artist)
	if album_flag: save_artist_albums(artist)  # Adds artists albums. If this is set in inner calls, starts recursion.

def save_artist(artist):
	vprint("[INSERT][ARTIST]", artist['name'])
	try:
		cursor.execute(insert_artist, (artist['id'], artist['name'], artist['popularity']))
	except MySQLdb.IntegrityError:  # Impeeds duplicate tuple error from stopping execution
		pass

def save_artist_genre(artist): 
	for genre in artist['genres']:
		vprint("[INSERT][ARTIST_GENRE]", artist['name'], ",", genre)
		try:
			cursor.execute(insert_artist_genre, (artist['id'], genre))
		except MySQLdb.IntegrityError:
			pass

def save_artist_albums(artist):
	albums = sp.artist_albums(artist['id'], limit=50)['items']  # Retrieves 50 albums at most
	albums.sort(key=lambda album:album['name'].lower())
	seen = set()  # Avoid duplicates(There are lots in Spotify)
	for album in albums:
		if album['name'] not in seen:
			album = get_album(album['id'])  # Retrieves full album object
			save_entire_album(album)

			for artist in album['artists']:
				try:
					save_artist_album(artist, album)
				except MySQLdb.IntegrityError as err: 
					if err[0] == 1452:  # Artist not in DB yet(FK Error - Code 1452)
						vprint("[ERROR]["+ str(err[0]) +"]", err[1])
						artist = get_artist(artist['id'])
						save_entire_artist(artist)
						save_artist_album(artist, album)
			seen.add(album['name'])

def save_artist_album(artist, album):
	vprint("[INSERT][ARTIST_ALBUM]", artist['name'], ",", album['name'])
	cursor.execute(insert_artist_album, (artist['id'], album['id']))

def save_entire_album(album):
	save_album(album)
	save_album_tracks(album)

def save_album(album):
	vprint("[INSERT][ALBUM]", album['name'])
	try:
		cursor.execute(insert_album, (album['id'], album['name'], album['album_type'], album['release_date'], album['popularity']))
	except MySQLdb.IntegrityError:  
		pass

def save_album_tracks(album):
	tracks = album['tracks']['items']
	for track in tracks:
		track = get_track(track['id'])  # Retrieves full track object
		save_entire_track(track)
		save_album_track(album, track)

def save_album_track(album, track):
	vprint("[INSERT][ALBUM_TRACK]", album['name'], ",", track['name'])
	try:
		cursor.execute(insert_album_track, (album['id'], track['id'], track['disc_number'], track['track_number']))
	except MySQLdb.IntegrityError:  
		pass

def save_entire_track(track, album_flag=False):
	save_track(track)

	#if album_flag:  # Save album for that track

	for artist in track['artists']:
		try:
			save_track_artist(track, artist)
		except MySQLdb.IntegrityError as err: 
			if err[0] == 1452:  # Artist not in DB yet(FK Error - Code 1452)
				vprint("[ERROR]["+ str(err[0]) +"]", err[1])
				artist = get_artist(artist['id'])
				save_entire_artist(artist)
				save_track_artist(track, artist)

def save_track(track):
	vprint("[INSERT][TRACK]", track['name'])
	try:
		cursor.execute(insert_track, (track['id'], track['name'], track['duration_ms'], int(track['explicit'] == True), track['popularity']))
	except MySQLdb.IntegrityError:  
		pass	

def save_track_artist(track, artist):
	vprint("[INSERT][TRACK_ARTIST]", track['name'], ",", artist['name'])
	cursor.execute(insert_track_artist, (track['id'], artist['id']))

def save_entire_playlist(playlist):
	save_playlist(playlist)
	save_playlist_tracks(playlist)

def save_playlist(playlist):
	vprint("[INSERT][PLAYLIST]", playlist['name'])
	try:
		cursor.execute(insert_playlist, (playlist['id'], playlist['name'], playlist['owner']['id'], playlist['description'], int(playlist['collaborative'] == True), int(playlist['public'] == True)))
	except MySQLdb.IntegrityError as err: 
			if err[0] == 1452:  # User not in DB yet(FK Error - Code 1452):
				vprint("[ERROR]["+ str(err[0]) +"]", err[1])
				user = get_user(playlist['owner']['id'])
				save_user(user)
				cursor.execute(insert_playlist, (playlist['id'], playlist['name'], playlist['owner']['id'], playlist['description'], int(playlist['collaborative'] == True), int(playlist['public'] == True)))

def save_user(user):
	vprint("[INSERT][USER]", user['display_name'])
	try:
		cursor.execute(insert_user, (user['id'], user['display_name']))
	except MySQLdb.IntegrityError:
		pass

def save_playlist_tracks(playlist):
	for track in playlist['tracks']['items']:
		track = track['track']
		save_entire_track(track)
		save_playlist_track(playlist, track)

def save_playlist_track(playlist, track):
	vprint("[INSERT][PLAYLIST_TRACK]", playlist['name'], ",", track['name'])
	try:
		cursor.execute(insert_playlist_track, (playlist['id'], track['id']))
	except MySQLdb.IntegrityError:  
		pass

#===================================MAIN==================================#

if len(sys.argv) >= 4:
	username = sys.argv[1]
	artist_limit = int(sys.argv[2])
	playlist_limit = int(sys.argv[3])
else:
	print "usage: %s username artist_limit playlist_limit [-v]" % (sys.argv[0],)
	sys.exit()

scope = 'user-library-read'
token = util.prompt_for_user_token(username, scope, client_id = "791f489dbfac46009b49332c0897001c", client_secret = "39bfe9b8132441ab870b0157dc92bd52", redirect_uri = "https://example.com/callback/")

if token:
	sp = spotipy.Spotify(auth=token)

	if artist_limit > 100000:
		print "[ERROR] Maximum allowed limit is 100000. Limit has been resized."
		artist_limit = 100000

	retrieve_all_artists(artist_limit)
	retrieve_all_playlists(playlist_limit, category_id='decades', country='BR')
else:
	print "Can't get token for", username

cursor.close()
db.close()