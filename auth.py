import os

from flask import request
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth

from db import controll_user_login
from spotify import get_user_profile_id_and_display_name


def spotify_auth(session):
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=os.getenv("SPOTIPY_SCOPE"),
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )
    return auth_manager.get_authorize_url()


def handle_callback(session):
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=os.getenv("SPOTIPY_SCOPE"),
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code)
    session["token_info"] = token_info

    spotify_id, display_name = get_user_profile_id_and_display_name(
        token_info["access_token"]
    )

    session["user_id"] = controll_user_login(spotify_id, display_name)

    return None
