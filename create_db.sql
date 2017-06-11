CREATE DATABASE spotify
	DEFAULT CHARACTER SET utf8
	DEFAULT COLLATE utf8_general_ci;
USE spotify;

CREATE TABLE Album (id VARCHAR(50), name VARCHAR(250), album_type VARCHAR(20), release_date VARCHAR(20), popularity INT(4) UNSIGNED, PRIMARY KEY(id));
CREATE TABLE Artist (id VARCHAR(50), name VARCHAR(200), followers INT(10), popularity INT(4) UNSIGNED, PRIMARY KEY(id));
CREATE TABLE Track (id VARCHAR(50), name VARCHAR(250), duration_ms INT(10) UNSIGNED, explicit BOOLEAN, popularity INT(4) UNSIGNED, PRIMARY KEY(id));
CREATE TABLE User (id VARCHAR(50), display_name VARCHAR(100), followers INT(10), PRIMARY KEY(id));
CREATE TABLE Playlist (id VARCHAR(50), name VARCHAR(100), owner VARCHAR(50), description VARCHAR(1000), followers INT(10), collaborative BOOLEAN, public BOOLEAN, FOREIGN KEY(owner) REFERENCES User(id) ON DELETE RESTRICT, PRIMARY KEY(id));

CREATE TABLE AlbumTrack (album_id VARCHAR(50), track_id VARCHAR(50), disc_number INT(2), track_number INT(3), PRIMARY KEY(album_id, track_id), FOREIGN KEY(album_id) REFERENCES Album(id) ON DELETE CASCADE, FOREIGN KEY(track_id) REFERENCES Track(id) ON DELETE CASCADE);
CREATE TABLE ArtistGenre (artist_id VARCHAR(50), genre VARCHAR(50), PRIMARY KEY(artist_id, genre), FOREIGN KEY(artist_id) REFERENCES Artist(id) ON DELETE CASCADE);
CREATE TABLE ArtistAlbum (artist_id VARCHAR(50), album_id VARCHAR(50), PRIMARY KEY(artist_id, album_id), FOREIGN KEY(artist_id) REFERENCES Artist(id) ON DELETE CASCADE, FOREIGN KEY(album_id) REFERENCES Album(id) ON DELETE CASCADE);
CREATE TABLE TrackArtist (track_id VARCHAR(50), artist_id VARCHAR(50), PRIMARY KEY(track_id, artist_id), FOREIGN KEY(track_id) REFERENCES Track(id) ON DELETE CASCADE, FOREIGN KEY(artist_id) REFERENCES Artist(id) ON DELETE RESTRICT);
CREATE TABLE PlaylistTrack (playlist_id VARCHAR(50), track_id VARCHAR(50), PRIMARY KEY(playlist_id, track_id), FOREIGN KEY(playlist_id) REFERENCES Playlist(id) ON DELETE CASCADE, FOREIGN KEY(track_id) REFERENCES Track(id) ON DELETE CASCADE);