from operator import attrgetter

from spotipy import Spotify

from db import get_user_profile_db


def get_user_profile(access_token: str, user_id: str):

    sp = Spotify(auth=access_token)

    user = sp.current_user()

    top_tracks = get_user_top_tracks(sp)

    top_artists = get_user_top_artists(sp)

    top_genres = get_user_top_genres(sp)

    user_profile_db_dict = get_user_profile_db(user_id)
    bio = user_profile_db_dict["bio"]
    spotify_url = user_profile_db_dict["spotify_url"]

    return {
        "user": user,
        "top_tracks": top_tracks,
        "top_artists": top_artists,
        "top_genres": top_genres,
        "bio": bio,
        "spotify_url": spotify_url,
    }


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


def get_user(access_token: str):
    sp = Spotify(auth=access_token)
    user = sp.current_user()

    return user
