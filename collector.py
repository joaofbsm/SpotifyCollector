#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import spotipy
import spotipy.util as util
import pprint
import MySQLdb

# WORK PLAN
# - Get 100000 artists and parse the data -> Populate Artist, ArtistGenre, ArtistAlbum(Missing in doc)
# - Get Album data from those artists -> Populate Album, AlbumGenre, AlbumTrack
# - Get Track data from those albums -> Populate Track, TrackArtist
# - Get Playlist by searching by Category, e.g., Party -> Populate Playlist, User, Track, PlaylistTrack(Missing in doc)

# TODO
# - Check if the API will accept all those requests. If not, simplify DB by using simplified object types.
# - Maybe stop artist recursion and simply add their names for the current album
# - Maybe remove AlbumGenre
# - Recheck pass on exceptions for relationship table insertions

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

insert_album_genre = ("INSERT INTO AlbumGenre "
						"(album_id, genre) "
						"VALUES (%s, %s)")

insert_album_track = ("INSERT INTO AlbumTrack "
						"(album_id, track_id, disc_number, track_number) "
						"VALUES (%s, %s, %s, %s)")

insert_track = ("INSERT INTO Track "
				"(id, name, duration_ms, explicit, popularity) " 
				"VALUES (%s, %s, %s, %s, %s)")

insert_track_artist = ("INSERT INTO TrackArtist "
						"(track_id, artist_id) "
						"VALUES (%s, %s)")

#=================================MODULES=================================#

def get_all_artists(limit, offset):
	return sp.search(q='year:0000-9999', type='artist', market='US', limit=limit, offset=offset)

def get_artist(id):
	return sp.artist(id)

def get_album(id):
	return sp.album(id)

def get_track(id):
	return sp.track(id)

# Saves artist and all of it's relations
def save_entire_artist(artist): 
	save_artist(artist)
	save_artist_genre(artist)
	save_artist_albums(artist)

def save_artist(artist):
	print "[INSERT][ARTIST]", artist['name']
	try:
		cursor.execute(insert_artist, (artist['id'], artist['name'], artist['popularity']))
	except MySQLdb.IntegrityError:  # Impeeds duplicate tuple error from stopping execution
		pass

def save_artist_genre(artist): 
	for genre in artist['genres']:
		print "[INSERT][ARTIST_GENRE]", artist['name'], ",", genre
		try:
			cursor.execute(insert_artist_genre, (artist['id'], genre))
		except MySQLdb.IntegrityError:
			pass

def save_artist_albums(artist):
	albums = sp.artist_albums(artist['id'], limit=50)['items']  # Retrieves 50 albums at most
	albums.sort(key=lambda album:album['name'].lower())
	seen = set()  # Avoid duplicates
	for album in albums:
		if album['name'] not in seen:
			album = get_album(album['id'])  # Retrieves full album object
			save_entire_album(album)

			for artist in album['artists']:
				try:
					save_artist_album(artist, album)
				except MySQLdb.IntegrityError as err: 
					if err[0] == 1452:  # Artist not in DB yet(FK Error - Code 1452)
						print "[ERROR]["+ str(err[0]) +"]", err[1]
						artist = get_artist(artist['id'])
						save_entire_artist(artist)
			seen.add(album['name'])

def save_artist_album(artist, album):
	print "[INSERT][ARTIST_ALBUM]", artist['name'], ",", album['name']
	cursor.execute(insert_artist_album, (artist['id'], album['id']))

def save_entire_album(album):
	save_album(album)
	save_album_genre(album)
	save_album_tracks(album)

def save_album(album):
	print "[INSERT][ALBUM]", album['name']
	try:
		cursor.execute(insert_album, (album['id'], album['name'], album['album_type'], album['release_date'], album['popularity']))
	except MySQLdb.IntegrityError:  
		pass

def save_album_genre(album):
	for genre in album['genres']:
		print "[INSERT][ALBUM_GENRE]", album['name'], ",", genre
		try:
			cursor.execute(insert_album_genre, (album['id'], genre))
		except MySQLdb.IntegrityError:  
			pass

def save_album_tracks(album):
	tracks = album['tracks']['items']
	for track in tracks:
		track = get_track(track['id'])
		save_entire_track(track)
		save_album_track(album, track)

def save_album_track(album, track):
	print "[INSERT][ALBUM_TRACK]", album['name'], ",", track['name']
	cursor.execute(insert_album_track, (album['id'], track['id'], track['disc_number'], track['track_number']))

def save_entire_track(track):
	save_track(track)
	save_track_artist(track)

def save_track(track):
	print "[INSERT][TRACK]", track['name']
	try:
		cursor.execute(insert_track, (track['id'], track['name'], track['duration_ms'], int(track['explicit'] == 'true'), track['popularity']))
	except MySQLdb.IntegrityError:  
		pass	

def save_track_artist(track):
	for artist in track['artists']:
		print "[INSERT][TRACK_ARTIST]", track['name'], ",", artist['name']
		try:
			cursor.execute(insert_track_artist, (track['id'], artist['id']))
		except MySQLdb.IntegrityError:  
			pass

#===================================MAIN==================================#

if len(sys.argv) > 1:
	username = sys.argv[1]
	limit = int(sys.argv[2])
else:
	print "Usage: %s username limit" % (sys.argv[0],)
	sys.exit()

scope = 'user-library-read'
token = util.prompt_for_user_token(username, scope, client_id = "791f489dbfac46009b49332c0897001c", client_secret = "39bfe9b8132441ab870b0157dc92bd52", redirect_uri = "https://example.com/callback/")

if token:
	sp = spotipy.Spotify(auth=token)

	if limit > 100000:
		print "[ERROR] Maximum allowed limit is 100000. Limit has been resized."
		limit = 100000

	offset = 0;
	for i in range(limit / 50):
		artists = get_all_artists(50, offset)['artists']['items']
		for artist in artists:
			save_entire_artist(artist)
		offset += 50
	remainder = limit % 50
	artists = get_all_artists(remainder, offset)['artists']['items']
	for artist in artists:
		save_entire_artist(artist)

else:
	print "Can't get token for", username

cursor.close()
db.close()