from spotipy import Spotify

from db import get_threads_by_user_subscriptions, get_user_profile_db


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
    top_tracks_raw = sp.current_user_top_tracks(limit=5, time_range="medium_term")[
        "items"
    ]

    top_tracks = []

    for track in top_tracks_raw:
        top_tracks.append(
            {
                "name": track["name"],
                "artists": track["artists"][0]["name"],
                "spotify_url": track["uri"],
            }
        )

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
    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="medium_term")[
        "items"
    ]
    top_artists = []
    for artist in top_artists_raw:
        top_artists.append(
            {
                "name": artist["name"],
                "genres": artist["genres"] if len(artist["genres"]) > 0 else "unknown",
                "spotify_url": artist["uri"],
            }
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
    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="medium_term")[
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


def get_album_image_url(spotify_url, sp):
    """
    Fetches the album image from a Spotify track or album URL.

    Args
    -----
        spotify_url : str
            The Spotify URL (track or album).
        sp: Spotify
            Spotipy client object.

    Returns
    ------
        str
            Album image URL or placeholder if not found.
    """
    try:
        print(f"DEBUG - Spotify URL received: {spotify_url}")
        parts = spotify_url.split("/")
        if "track" in parts:
            track_id = parts[-1].split("?")[0]
            print(f"DEBUG - Detected track ID: {track_id}")
            track = sp.track(track_id)
            return track["album"]["images"][0]["url"]
        elif "album" in parts:
            album_id = parts[-1].split("?")[0]
            print(f"DEBUG - Detected album ID: {album_id}")
            album = sp.album(album_id)
            return album["images"][0]["url"]
        else:
            print("DEBUG - URL is not a track or album.")
            return "/static/tunelink.png"
    except Exception as e:
        print(f"Error fetching album image: {e}")
        return "/static/tunelink.png"


def get_dashboard_data(token_info, user_id):
    """Retrives user information and subscribed forum threads including assosiacted Spotify album images.

    Args
    -------
        token_info : dict
            A dictionary containing the access token for Spotify API.
        user_id : int
            The ID of the user in the database.

    Returns
    -------
        tuple
            A tuple containing the user profile and a list of threads with associated Spotify album images.

    """
    try:
        sp = Spotify(auth=token_info["access_token"])
        user = get_user(token_info["access_token"])

        threads = get_threads_by_user_subscriptions(user_id)
        for thread in threads:
            spotify_url = thread.get("spotify_url")
            if spotify_url is not None:
                thread["album_image"] = get_album_image_url(spotify_url, sp)
            else:
                thread["album_image"] = "/static/tunelink.png"

        return user, threads
    except Exception as e:
        print(f"[error] Failed to fetch dashboard data: {e}")
        return None, []
