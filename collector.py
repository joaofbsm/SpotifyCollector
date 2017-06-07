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
# - Receive data from 1 artist, parse it and then INSERT it into DB
# - Code loop to retrieve 100000 artists, 50 at a time(API limit), incrementing OFFSET with a step of 50 with a maximum of 100000.

pp = pprint.PrettyPrinter(indent=1)

# SQL Queries
insert_artist = ("INSERT INTO Artist "
				"(id, name, popularity) "
				"VALUES (%s, %s, %s)")

insert_artist_genre = ("INSERT INTO employees "
						"(first_name, last_name, hire_date, gender, birth_date) "
						"VALUES (%s, %s, %s, %s, %s)")

def get_album():
	pass

def get_all_artists(limit, offset):
	return sp.search(q='year:0000-9999', type='artist', market='US', limit=limit, offset=offset)
	

def get_artist(name):
	return sp.search(q='artist:' + name, type='artist', limit=limit)

def save_all_artists(artists, qtd, cursor):	
	for i in range(qtd):
		save_artist(artists['artists']['items'][i], cursor)
		#TODO: Populate ArtistGenre and ArtistAlbum

def save_artist(artist, cursor):
	try:
		cursor.execute(insert_artist, (artist['id'], artist['name'], artist['popularity']))
	except MySQLdb.IntegrityError:
		pass

def show_artist_albums(artist):
	albums = []
	results = sp.artist_albums(artist['id'], album_type='album')
	albums.extend(results['items'])
	while results['next']:
		results = sp.next(results)
		albums.extend(results['items'])
	seen = set() # to avoid dups
	albums.sort(key=lambda album:album['name'].lower())
	for album in albums:
		name = album['name']
		if name not in seen:
			print((' ' + name))
			seen.add(name)



scope = 'user-library-read'
artist_name = "Avril Lavigne"
	
#argument_switch = {'art':get_artist}
#argument_switch[sys.argv[2]](sys.argv[3], sys.argv[4])

if len(sys.argv) > 1:
	username = sys.argv[1]
	limit = int(sys.argv[2])
else:
	print "Usage: %s username limit" % (sys.argv[0],)
	sys.exit()

token = util.prompt_for_user_token(username, scope, client_id = "791f489dbfac46009b49332c0897001c", client_secret = "39bfe9b8132441ab870b0157dc92bd52", redirect_uri = "https://example.com/callback/")

if token:
	sp = spotipy.Spotify(auth=token)

	db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="spotify")
	cursor = db.cursor()

	db.autocommit(True)  # Autocommit INSERTs to spotify DB
	
	#results = get_artist(artist_name)

	if limit > 100000:
		print "[ERROR] Maximum allowed limit is 100000. Limit has been resized."
		limit = 100000

	offset = 0;
	for i in range(limit / 50):
		artists = get_all_artists(50, offset)
		save_all_artists(artists, 50, cursor)
		offset += 50
	remainder = limit % 50
	artists = get_all_artists(remainder, offset)
	save_all_artists(artists, remainder, cursor)

	#pp.pprint(results)

	#artist = results
	#print artist['artists']['items'][0]['id'], artist['artists']['items'][0]['name'], artist['artists']['items'][0]['popularity']

	#print results['artists']['items'][0]['name']
	db.close()
else:
	print "Can't get token for", username


