from operator import attrgetter

from spotipy import Spotify

from db import get_user_profile_db


def get_user_profile(access_token: str, user_id: str):
    """Fetches the user profile, top tracks, top artists and top genres from Spotify.

    Args
    -------
        access_token : str
            The access token for Spotify API.
        user_id : str
            The ID of the user.

    Returns
    -------
        dict
            A dictionary containing the user profile, top tracks, top artists, top genres, user bio and Spotify URL.
    """

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
    """Fetches the top tracks of the user from Spotify.

    Args
    -------
        sp : Spotify
            The Spotify object to interact with the API.

    Returns
    -------
        top_tracks : list
            A list of dictionaries containing the top tracks and their artists.

    """
    top_tracks_raw = sp.current_user_top_tracks(limit=5, time_range="short_term")[
        "items"
    ]

    top_tracks = []

    for t in top_tracks_raw:
        top_tracks.append({"name": t["name"], "artists": t["artists"][0]})

    return top_tracks


def get_user_top_artists(sp: Spotify):
    """Fetches the top artists of the user from Spotify.

    Args
    -------
        sp : Spotify
            The Spotify object to interact with the API.

    Returns
    -------
        top_artists : list
            A list of dictionaries containing the top artists and their genres.
    """
    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="short_term")[
        "items"
    ]
    top_artists = []
    for a in top_artists_raw:
        top_artists.append(
            {"name": a["name"], "genres": a["genres"][0] if a["genres"] else "unknown"}
        )
    return top_artists


def get_user_top_genres(sp: Spotify):
    """Fetches the top genres of the user from Spotify.

    Args
    -------
        sp : Spotify
            The Spotify object to interact with the API.

    Returns
    -------
        top_genres : list
            A list of the top genres of the user.
    """
    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="short_term")[
        "items"
    ]
    genre_list = []

    for artist in top_artists_raw:
        genre_list.extend(artist["genres"])

    top_genres = sorted(set(genre_list))[:5]
    return top_genres


def get_user_profile_id_and_display_name(access_token):
    """Fetches the Spotify ID and display name of the user.
    Args
    -------
        access_token : str
            The access token for Spotify API.
    Returns
    -------
        dict
            A dictionary containing the Spotify ID and display name of the user.
    """
    sp = Spotify(auth=access_token)
    profile = sp.current_user()

    spotify_id = profile["id"]
    display_name = profile["display_name"]

    return {"spotify_id": spotify_id, "display_name": display_name}


def get_user(access_token: str):
    """Fetches the user profile from Spotify.

    Args
    -------
        access_token : str
            The access token for Spotify API.

    Returns
    -------
        user : dict
            A dictionary containing the user profile information.
    """
    sp = Spotify(auth=access_token)
    user = sp.current_user()

    return user
