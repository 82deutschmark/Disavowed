# Google OAuth authentication blueprint for the espionage game
# This module handles Google OAuth authentication for user login/logout
# Updated by Cascade to support both local development and Replit deployment
# Uses LOCAL_DOMAIN environment variable for local development fallback

import json
import os
import requests
from app import db
from flask import Blueprint, redirect, request, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, UserProgress
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
# Support both Replit and local development environments
if os.environ.get("REPLIT_DEV_DOMAIN"):
    # Running on Replit
    DEV_REDIRECT_URL = f'https://{os.environ["REPLIT_DEV_DOMAIN"]}/google_login/callback'
else:
    # Running locally - use LOCAL_DOMAIN from .env
    local_domain = os.environ.get("LOCAL_DOMAIN", "localhost:5000")
    DEV_REDIRECT_URL = f'http://{local_domain}/google_login/callback'

# Display setup instructions to the user:
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For local development, make sure LOCAL_DOMAIN is set in your .env file.
For Replit deployment, see: https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        # Replacing http:// with https:// is important as the external
        # protocol must be https to match the URI whitelisted
        redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@google_auth.route("/google_login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        # Replacing http:// with https:// is important as the external
        # protocol must be https to match the URI whitelisted
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=request.base_url.replace("http://", "https://"),
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    if userinfo.get("email_verified"):
        users_email = userinfo["email"]
        users_name = userinfo["given_name"]
        users_picture = userinfo.get("picture")
        google_id = userinfo["sub"]
    else:
        flash("User email not available or not verified by Google.", "error")
        return redirect(url_for("index"))

    # Check if user already exists
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        # Create new user with 50 diamonds
        user = User(
            google_id=google_id,
            email=users_email,
            name=users_name,
            profile_pic=users_picture,
            diamonds=50
        )
        db.session.add(user)
        db.session.commit()
        
        # Create user progress for new user
        user_progress = UserProgress(
            user_id=f"user_{user.id}",
            authenticated_user_id=user.id,
            currency_balances={"": 50, "": 50, "": 40, "": 45, "": 500}
        )
        db.session.add(user_progress)
        db.session.commit()
        
        flash(f"Welcome to DISAVOWED, {users_name}! You start with 50 diamonds.", "success")
    else:
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash(f"Welcome back, {users_name}!", "success")
    
    # Check if user has existing session progress to merge
    guest_user_id = session.get('user_id')
    if guest_user_id and guest_user_id != f"user_{user.id}":
        # Find guest progress
        guest_progress = UserProgress.query.filter_by(user_id=guest_user_id).first()
        user_progress = UserProgress.query.filter_by(authenticated_user_id=user.id).first()
        
        if guest_progress and user_progress:
            # Merge guest progress into authenticated user progress
            # Keep the more recent data and combine currency
            if guest_progress.current_node_id:
                user_progress.current_node_id = guest_progress.current_node_id
                user_progress.current_story_id = guest_progress.current_story_id
            
            # Combine currency balances
            guest_balances = guest_progress.currency_balances or {}
            user_balances = user_progress.currency_balances or {}
            for currency, amount in guest_balances.items():
                if currency in user_balances:
                    user_balances[currency] += amount
                else:
                    user_balances[currency] = amount
            user_progress.currency_balances = user_balances
            
            # Combine other progress data
            user_progress.choice_history.extend(guest_progress.choice_history or [])
            user_progress.encountered_characters.extend(guest_progress.encountered_characters or [])
            user_progress.active_missions.extend(guest_progress.active_missions or [])
            
            # Remove guest progress
            db.session.delete(guest_progress)
            db.session.commit()
            
            flash("Your game progress has been saved to your account!", "info")

    login_user(user)
    
    # Update session to use authenticated user ID
    session['user_id'] = f"user_{user.id}"
    
    return redirect(url_for("index"))


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    # Keep session for guest play
    if 'user_id' in session and session['user_id'].startswith('user_'):
        # Generate new guest session ID
        import uuid
        session['user_id'] = str(uuid.uuid4())
    flash("You have been logged out. You can continue playing as a guest.", "info")
    return redirect(url_for("index"))


@google_auth.route("/save_game")
def save_game_prompt():
    """Prompt unauthenticated users to save their game"""
    if current_user.is_authenticated:
        return redirect(url_for("game"))
    
    return redirect(url_for("google_auth.login"))