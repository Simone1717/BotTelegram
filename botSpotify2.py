import telebot
from telebot import types
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius

# Inizializza il bot di Telegram
bot_token = 'token_telegram'
bot = telebot.TeleBot(bot_token)

# Inizializza l'oggetto Spotipy per accedere all'API di Spotify
spotify_client_id = 'token_id_spotify'
spotify_client_secret = 'secret_token_spotify'

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=spotify_client_id,
                                                                         client_secret=spotify_client_secret))

# Legenda: Comandi disponibili con il bot
legend_message = """
<b>Legenda:</b>
- /start: Avvia il bot e mostra un messaggio di benvenuto.
- /testo Titolo_Canzone Nome_Cantante: Ottiene il testo di una canzone specificata dal titolo e dall'artista.
- /canzone Titolo_Canzone Nome_Cantante: Mostra le informazioni su una singola canzone, incluso il testo.
- /album Titolo_Album Nome_Artista: Mostra le informazioni su un album di un determinato artista.
- /artisti Nome_Cantante: Mostra artisti correlati a un determinato artista.
- /playlist Titolo_Playlist: Trova una playlist basata sul titolo specificato.
"""

# Gestisce il comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Benvenuto! Scrivi il nome di un cantante per ottenere le sue canzoni più ascoltate su Spotify.")
    bot.send_message(message.chat.id, legend_message, parse_mode="HTML")

# Funzione per inviare la legenda come messaggio fisso
def send_legend(message):
    bot.send_message(message.chat.id, legend_message, parse_mode="HTML")

# Gestisce il comando /testo per ottenere il testo di una canzone
@bot.message_handler(commands=['testo'])
def send_lyrics(message):
    command = message.text.split()
    if len(command) < 3:
        bot.reply_to(message, "Utilizzo corretto: /testo Titolo_Canzone Nome_Cantante")
        send_legend(message)
        return
    song_title = ' '.join(command[1:-1])
    artist_name = command[-1]
    lyrics = get_lyrics(song_title, artist_name)
    if lyrics:
        bot.reply_to(message, lyrics)
    else:
        bot.reply_to(message, f"Non ho trovato il testo della canzone {song_title} di {artist_name}.")
    send_legend(message)

# Gestisce il comando /canzone per ottenere informazioni su una singola canzone
@bot.message_handler(commands=['canzone'])
def send_single_track(message):
    command = message.text.split()
    if len(command) < 3:
        bot.reply_to(message, "Utilizzo corretto: /canzone Titolo_Canzone Nome_Cantante")
        send_legend(message)
        return
    song_title = ' '.join(command[1:-1])
    artist_name = command[-1]
    track_info = get_single_track_info(song_title, artist_name)
    if track_info:
        response = f"<b>{track_info['name']}</b> - {', '.join(artist['name'] for artist in track_info['artists'])}\n"
        response += f"Data di uscita: {track_info['release_date']}\n"
        response += f"Ascolta su Spotify: {track_info['spotify_url']}\n"
        response += f"Ascoltatori mensili: {track_info['monthly_listeners']}\n"
        send_track(message.chat.id, track_info['cover_url'], response, track_info['spotify_url'], track_info['id'])
    else:
        bot.reply_to(message, f"Non ho trovato informazioni sulla canzone {song_title} di {artist_name} su Spotify.")
    send_legend(message)

# Modifica il comando /album per includere i dettagli della traccia quando si clicca su di essa
@bot.message_handler(commands=['album'])
def send_album_info(message):
    command = message.text.split()
    if len(command) < 3:
        bot.reply_to(message, "Utilizzo corretto: /album Titolo_Album Nome_Artista")
        send_legend(message)
        return
    album_title = ' '.join(command[1:-1])
    artist_name = command[-1]
    album_info = get_album_info(album_title, artist_name)
    if album_info:
        response = f"<b>{album_info['name']}</b> di {', '.join(artist['name'] for artist in album_info['artists'])}\n"
        response += f"Data di pubblicazione: {album_info['release_date']}\n"
        response += "Lista delle tracce:\n"
        markup = types.InlineKeyboardMarkup()
        for i, track in enumerate(album_info['tracks'], start=1):
            response += f"{i}. {track['name']}\n"
            markup.add(types.InlineKeyboardButton(track['name'], callback_data=f"track_{track['id']}"))
        bot.send_photo(message.chat.id, album_info['cover_url'], caption=response, parse_mode="HTML", reply_markup=markup)
    else:
        bot.reply_to(message, f"Non ho trovato informazioni sull'album {album_title} di {artist_name} su Spotify.")
    send_legend(message)

# Gestisce il comando /artisti per ottenere artisti correlati a un determinato artista
@bot.message_handler(commands=['artisti'])
def send_related_artists(message):
    command = message.text.split()
    if len(command) < 2:
        bot.reply_to(message, "Utilizzo corretto: /artisti Nome_Cantante")
        send_legend(message)
        return
    artist_name = ' '.join(command[1:])
    related_artists = get_related_artists(artist_name)
    if related_artists:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for related_artist in related_artists:
            button_artist = types.InlineKeyboardButton(related_artist, callback_data=f"artist_{related_artist}")
            markup.add(button_artist)
        bot.send_message(message.chat.id, "Scegli un artista correlato:", reply_markup=markup)
    else:
        bot.reply_to(message, f"Non ho trovato artisti correlati a {artist_name}.")
    send_legend(message)

# Gestisce tutti i messaggi di testo
@bot.message_handler(func=lambda message: True)
def send_top_tracks(message):
    artist_name = message.text.strip()
    tracks = get_top_tracks(artist_name)
    if tracks:
        for track in tracks:
            track_info = get_track_info(track['id'])
            response = f"<b>{track['name']}</b> - {', '.join(artist['name'] for artist in track['artists'])}\n"
            response += f"Data di uscita: {track_info['release_date']}\n"
            response += f"Ascoltatori mensili: {track_info['monthly_listeners']}\n"
            send_track(message.chat.id, track_info['cover_url'], response, track['external_urls']['spotify'], track['id'])
    else:
        bot.reply_to(message, f"Non ho trovato informazioni su {artist_name} su Spotify.")
    send_legend(message)
    
    
## Gestisce il comando /playlist per ottenere una playlist basata su un titolo specifico
@bot.message_handler(commands=['playlist'])
def send_playlist(message):
    command = message.text.split(maxsplit=1)
    if len(command) < 2:
        bot.reply_to(message, "Utilizzo corretto: /playlist Titolo_Playlist")
        send_legend(message)
        return
    
    playlist_title = command[1].strip()
    if not playlist_title:
        bot.reply_to(message, "Per favore fornisci un titolo di playlist valido.")
        send_legend(message)
        return
    
    playlist_info = get_playlist_by_title(playlist_title)
    if playlist_info:
        response = f"<b>{playlist_info['name']}</b>\n"
        response += f"Descrizione: {playlist_info['description']}\n"
        response += f"Ascolta su Spotify: {playlist_info['spotify_url']}\n"
        send_playlist_message(message.chat.id, playlist_info['cover_url'], response, playlist_info['spotify_url'])
    else:
        bot.reply_to(message, f"Non ho trovato una playlist con il titolo '{playlist_title}' su Spotify.")
    send_legend(message)

# Funzione per cercare una playlist basata su un titolo specifico
def get_playlist_by_title(title):
    try:
        result = sp.search(q=title, type='playlist', limit=1)
        if result['playlists']['items']:
            playlist_info = result['playlists']['items'][0]
            cover_url = playlist_info['images'][0]['url'] if playlist_info['images'] else None
            name = playlist_info['name']
            description = playlist_info['description']
            spotify_url = playlist_info['external_urls']['spotify']
            return {'name': name, 'description': description, 'cover_url': cover_url, 'spotify_url': spotify_url}
        else:
            return None
    except Exception as e:
        print(f"Errore durante la ricerca della playlist: {e}")
        return None

# Funzione per inviare la playlist con il markup inline
def send_playlist_message(chat_id, cover_url, response, spotify_url):
    markup = types.InlineKeyboardMarkup()
    button_listen = types.InlineKeyboardButton("Ascolta su Spotify", url=spotify_url)
    markup.add(button_listen)
    if cover_url:
        bot.send_photo(chat_id, cover_url, caption=response, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, response, parse_mode="HTML", reply_markup=markup)


# Funzione per ottenere le canzoni più ascoltate di un determinato artista su Spotify
def get_top_tracks(artist_name, limit=5):
    result = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    if result['artists']['items']:
        artist_id = result['artists']['items'][0]['id']
        top_tracks = sp.artist_top_tracks(artist_id, country='US')['tracks'][:limit]
        return top_tracks
    else:
        return None

# Funzione per ottenere informazioni aggiuntive su una traccia
def get_track_info(track_id):
    track_info = sp.track(track_id)
    cover_url = track_info['album']['images'][0]['url']
    release_date = track_info['album']['release_date']
    artist_id = track_info['artists'][0]['id']
    monthly_listeners = sp.artist(artist_id)['followers']['total']
    return {'cover_url': cover_url, 'release_date': release_date, 'monthly_listeners': monthly_listeners}

# Funzione per ottenere informazioni su una singola canzone
def get_single_track_info(song_title, artist_name):
    result = sp.search(q=f'track:{song_title} artist:{artist_name}', type='track', limit=1)
    if result['tracks']['items']:
        track_info = result['tracks']['items'][0]
        cover_url = track_info['album']['images'][0]['url']
        release_date = track_info['album']['release_date']
        spotify_url = track_info['external_urls']['spotify']
        artist_id = track_info['artists'][0]['id']
        monthly_listeners = sp.artist(artist_id)['followers']['total']
        return {'name': track_info['name'], 'artists': track_info['artists'], 'release_date': release_date,
                'spotify_url': spotify_url, 'cover_url': cover_url, 'id': track_info['id'], 'monthly_listeners': monthly_listeners}
    else:
        return None

# Funzione per ottenere informazioni su un album di un determinato artista
def get_album_info(album_title, artist_name):
    result = sp.search(q=f'album:{album_title} artist:{artist_name}', type='album', limit=1)
    if result['albums']['items']:
        album_id = result['albums']['items'][0]['id']
        album_info = sp.album(album_id)
        tracks = [{'id': track['id'], 'name': track['name']} for track in album_info['tracks']['items']]
        cover_url = album_info['images'][0]['url']
        return {'name': album_info['name'], 'artists': album_info['artists'], 'release_date': album_info['release_date'],
                'tracks': tracks, 'cover_url': cover_url}
    else:
        return None

# Funzione per ottenere informazioni su una singola traccia tramite l'ID
def get_single_track_info_by_id(track_id):
    try:
        track_info = sp.track(track_id)
        cover_url = track_info['album']['images'][0]['url']
        release_date = track_info['album']['release_date']
        spotify_url = track_info['external_urls']['spotify']
        artist_id = track_info['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        monthly_listeners = artist_info['followers']['total']
        return {'name': track_info['name'], 'artists': track_info['artists'], 'release_date': release_date,
                'spotify_url': spotify_url, 'cover_url': cover_url, 'monthly_listeners': monthly_listeners}
    except:
        return None

# Gestisce il clic su una traccia dell'album
@bot.callback_query_handler(func=lambda call: call.data.startswith('track_'))
def callback_get_track(call):
    track_id = call.data.split('_')[-1]
    track_info = get_single_track_info_by_id(track_id)
    if track_info:
        response = f"<b>{track_info['name']}</b> - {', '.join(artist['name'] for artist in track_info['artists'])}\n"
        response += f"Data di uscita: {track_info['release_date']}\n"
        response += f"Ascolta su Spotify: {track_info['spotify_url']}\n"
        response += f"Ascoltatori mensili: {track_info['monthly_listeners']}\n"
        send_track(call.message.chat.id, track_info['cover_url'], response, track_info['spotify_url'], track_id)
    else:
        bot.send_message(call.message.chat.id, "Non ho trovato informazioni sulla traccia.")
    send_legend(call.message)

# Gestisce la selezione di un artista correlato
@bot.callback_query_handler(func=lambda call: call.data.startswith('artist_'))
def callback_get_related_tracks(call):
    artist_name = call.data.split('_')[-1]
    tracks = get_top_tracks(artist_name, limit=3)
    if tracks:
        for track in tracks:
            track_info = get_track_info(track['id'])
            response = f"<b>{track['name']}</b> - {', '.join(artist['name'] for artist in track['artists'])}\n"
            response += f"Data di uscita: {track_info['release_date']}\n"
            response += f"Ascoltatori mensili: {track_info['monthly_listeners']}\n"
            response += f"Ascolta su Spotify: {track['external_urls']['spotify']}\n"
            send_track(call.message.chat.id, track_info['cover_url'], response, track['external_urls']['spotify'], track['id'])
    else:
        bot.send_message(call.message.chat.id, f"Non ho trovato informazioni su {artist_name} su Spotify.")
    send_legend(call.message)

# Gestisce le callback dei pulsanti
@bot.callback_query_handler(func=lambda call: call.data.startswith('lyrics_'))
def callback_get_lyrics(call):
    track_id = call.data.split('_')[-1]
    track_info = sp.track(track_id)
    song_title = track_info['name']
    artist_name = track_info['artists'][0]['name']
    lyrics = get_lyrics(song_title, artist_name)
    if lyrics:
        bot.send_message(call.message.chat.id, lyrics)
    else:
        bot.send_message(call.message.chat.id, f"Non ho trovato il testo della canzone {song_title} di {artist_name}.")
    send_legend(call.message)

# Funzione per ottenere artisti correlati a un determinato artista
def get_related_artists(artist_name, limit=7):
    result = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    if result['artists']['items']:
        artist_id = result['artists']['items'][0]['id']
        related_artists = sp.artist_related_artists(artist_id)['artists']
        return [related_artist['name'] for related_artist in related_artists]
    else:
        return None

# Funzione per ottenere il testo di una canzone utilizzando l'API di Genius
def get_lyrics(song_title, artist_name):
    genius = lyricsgenius.Genius("token_genius")
    song = genius.search_song(song_title, artist_name)
    if song:
        return song.lyrics
    else:
        return None

# Funzione per inviare la traccia con il markup inline
def send_track(chat_id, cover_url, response, spotify_url, track_id):
    markup = types.InlineKeyboardMarkup()
    button_listen = types.InlineKeyboardButton("Ascolta su Spotify", url=spotify_url)
    button_lyrics = types.InlineKeyboardButton("Testo", callback_data=f"lyrics_{track_id}")
    markup.add(button_listen, button_lyrics)
    bot.send_photo(chat_id, cover_url, caption=response, parse_mode="HTML", reply_markup=markup)

# Avvia il bot
bot.polling()

