import sys
import spotipy
import spotipy.util as util
import pprint

def get_artist(name):
	results = sp.search(q='artist:' + name, type='artist')
	items = results['artists']['items']
	if len(items) > 0:
		return items[0]
	else:
		return None

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

if len(sys.argv) > 1:
	username = sys.argv[1]
else:
	print "Usage: %s username" % (sys.argv[0],)
	sys.exit()

token = util.prompt_for_user_token(username, scope, client_id = "791f489dbfac46009b49332c0897001c", client_secret = "39bfe9b8132441ab870b0157dc92bd52", redirect_uri = "https://example.com/callback/")

if token:
	sp = spotipy.Spotify(auth=token)
#   results = sp.user("213odzhe2txitmf2mba76wryy")
#   pprint.pprint(results)
	results = sp.search(q='year:2000', type='artist', limit=50)
	#results = sp.current_user_playlists(limit=2)
	for i, item in enumerate(results['artists']['items']):
		print i, item['name']
	print
	pp = pprint.PrettyPrinter(indent=1)
	#pp.pprint(results)
else:
	print "Can't get token for", username



