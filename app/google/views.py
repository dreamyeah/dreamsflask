import os
from pprint import pformat
from time import time
from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required, \
    current_user
from flask.json import jsonify
import requests
from requests_oauthlib import OAuth2Session
from . import google
from .. import db
from ..models import User

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# This information is obtained upon registration of a new Google OAuth
# application at https://code.google.com/apis/console

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
redirect_uri = os.environ.get('REDIRECT_URI')


# OAuth endpoints given in the Google API documentation

authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://accounts.google.com/o/oauth2/token"
refresh_url = token_url # True for Google but not all providers.
scope = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

@google.route("/")
def demo():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Google)
    using an URL with a few key OAuth parameters.
    """
    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = google.authorization_url(authorization_base_url,
        # offline for refresh token
        # force to always make user click authorize
        access_type="offline", approval_prompt="force")
        # access_type="online", approval_prompt="auto")

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    print "state:"
    print state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.
@google.route("/login/authorized", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    google = OAuth2Session(client_id, redirect_uri=redirect_uri,
                           state=session['oauth_state'])
    token = google.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # We use the session as a simple DB for this example.
    session['oauth_token'] = token

    print "token"
    print  token
    return redirect(url_for('google.profile'))

@google.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    google = OAuth2Session(client_id, token=session['oauth_token'])
    userinfo = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    print userinfo
    email = userinfo['email']
    username = userinfo['name']
    header_url = userinfo['picture']
    user = User.query.filter_by(email=email).first()
    if user is not None:
        flash('You have been logged in.')
        login_user(user, True)
        return redirect(request.args.get('next') or url_for('main.index'))
    else:
        user = User(email=email,
                    username=username,
                    confirmed = True,
                    header_url = header_url
                    )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(request.args.get('next') or url_for('main.index'))

