from spotipy import Spotify

from db import get_connection, get_user_profile


def get_user_profile(session):
    token_info = session.get("token_info")
    if not token_info:
        return None

    sp = Spotify(auth=token_info["access_token"])

    user = sp.current_user()

    top_tracks = get_user_top_tracks(sp)

    top_artists = get_user_top_artists(sp)

    top_genres = get_user_top_genres(sp)

    bio, spotify_url = get_user_profile(session)

    return user, top_tracks, top_artists, top_genres, bio, spotify_url


def get_user_top_tracks(sp: Spotify):
    top_tracks_raw = sp.current_user_top_tracks(limit=5, time_range="short_term")[
        "items"
    ]

    top_tracks = []

    for t in top_tracks_raw:
        top_tracks.append({"name": t["name"], "artists": t["artists"][0]})

    return top_tracks


def get_user_top_artists(sp: Spotify):
    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="short_term")[
        "items"
    ]
    top_artists = []
    for a in top_artists_raw:
        top_artists.append(
            {"name": a["name"], "genres": a["genres"][0] if a["genres"] else "unknown"}
        )
    return top_artists


def get_user_top_genres(sp):
    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="short_term")[
        "items"
    ]
    genre_list = []

    for artist in top_artists_raw:
        genre_list.extend(artist["genres"])

    top_genres = sorted(set(genre_list))[:5]
    return top_genres


def get_user_profile_id_and_display_name(access_token):
    sp = Spotify(auth=access_token)
    profile = sp.current_user()

    spotify_id = profile["id"]
    display_name = profile["display_name"]

    return spotify_id, display_name


def get_user(access_token):
    sp = Spotify(auth=access_token)
    user = sp.current_user()

    return user
