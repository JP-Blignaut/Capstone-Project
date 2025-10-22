from requests_oauthlib import OAuth1Session
import os
import json
import requests
from django.conf import settings

# ---- Config (use env vars in real code) ----
CONSUMER_KEY = "ZT7rgZUZbWB9TNKeVuFfqQaqP"
CONSUMER_SECRET = "0frt9U04xMVJOCWw1BUnzS6BGkUuD0YBWKBuWqSAVLcSnfpdNW"

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHENTICATE_URL   = "https://api.twitter.com/oauth/authorize"   # or oauth/authenticate
ACCESS_TOKEN_URL   = "https://api.twitter.com/oauth/access_token"

class Tweet():
    _instance = None  # Missing from the original notes.
    def __new__(cls):
        if cls._instance is None:
            print("Creating the Tweet instance")
            cls._instance = super(Tweet, cls).__new__(cls)
            cls._instance.authenticate()
        return cls._instance


    def authenticate(self):
        
        # Get request token
        # Include the callback in the session so it's part of the signed request
        oauth = OAuth1Session( 
            client_key=CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
             callback_uri="oob",   # out-of-band PIN flow
        )
        try:
            fetch_response = oauth.fetch_request_token(
                        REQUEST_TOKEN_URL,
                        data={"x_auth_access_type": "write"}
                        )

        except ValueError as e:
            print("There may be an issue with your consumer key/secret"
            " or request signature.")

        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        print("Got OAuth token: %s" % resource_owner_key)
        print("Got OAuth token secret: %s" % resource_owner_secret)

        authorization_url = oauth.authorization_url(AUTHENTICATE_URL)
        print("Please go here and authorize: %s" % authorization_url)
        verifier = input("Please input the verifier PIN code: ").strip()

        oauth = OAuth1Session(
            client_key=CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        access_token = oauth_tokens['oauth_token']
        access_token_secret = oauth_tokens['oauth_token_secret']    

        print("Got access token: %s" % access_token)
        print("Got access token secret: %s" % access_token_secret)
        self.oauth = OAuth1Session(
            client_key=CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

    def upload_image(self, image_path):
        """Upload an image to Twitter and return the media ID"""
        if not self.oauth:
            raise ValueError("Authentication failed!")
        
           
        print(f"Attempting to open image at: {image_path}")
        
        # Read the image file
        with open(image_path, 'rb') as image_file:
            file = {'media': image_file}
            
            # Upload to Twitter's media upload endpoint
            response = self.oauth.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                files=file
            )
        
        if response.status_code != 200:
            raise Exception(
                "Image upload failed: {}{}".format(
                response.status_code, response.text
                ))
        
        media_data = response.json()
        return media_data['media_id_string']
    
    def make_tweet(self, tweet_text, image_path=None):
        """
        Create a tweet with optional image
        
        Args:
            tweet_text (str): The text content of the tweet
            image_path (str, optional): Path to image file to attach
        """
        if not self.oauth:
            raise ValueError("Authentication failed!")
        
        # Prepare tweet data
        tweet_data = {"text": tweet_text}
        
        # If image is provided, upload it first and add media to tweet
        if image_path:
            try:
                media_id = self.upload_image(image_path)
                tweet_data["media"] = {"media_ids": [media_id]}
                print(f"Image uploaded successfully. Media ID: {media_id}")
            except Exception as e:
                print(f"Failed to upload image: {e}")
                raise
        
        # Make the tweet request
        response = self.oauth.post(
            "https://api.twitter.com/2/tweets",
            json=tweet_data,
        )
        
        if response.status_code != 201:
            raise Exception(
                "Request returned as an error: {}{}".format(
                response.status_code, response.text
                ))
        print("Response code: {}".format(response.status_code))
        
        # Saving the response as JSON:
        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))

