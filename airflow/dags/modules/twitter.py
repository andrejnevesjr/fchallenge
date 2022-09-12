
"""
Twitter API custom library
Dependencies: Tweepy
"""
__version__ = '0.0.1'
__author__ = 'André Junior'

from ast import Raise
from typing import Dict, List
from modules.custom_exceptions import TwitterAPIError, TwitterNoPostsFound, TwitterAPIUnavailable, TwitterAuthorizationError
from tweepy import TweepError
import os
import sys
import tweepy
import hashlib
from datetime import datetime, timedelta, date
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))


class Twitter():
    def __init__(self, **kwargs):
        self._consumer_key = kwargs['consumer_key']
        self._consumer_secret = kwargs['consumer_secret']
        self._access_token = kwargs['access_token']
        self._access_token_secret = kwargs['access_token_secret']
        self.api = self._get_session()

    def _get_session(self):
        """Initialize Twitter Session using credentials

        Returns:
            twitter_session: Twitter session
        """
        try:
            authentication = tweepy.OAuthHandler(
                self._consumer_key, self._consumer_secret)
            authentication.set_access_token(
                self._access_token, self._access_token_secret)

            twitter_session = tweepy.API(
                authentication,
                # number of allowed retries
                retry_count=3,
                # delay in second between retries
                retry_delay=2,
                # if the api wait when it hits the rate limit
                wait_on_rate_limit=True,
                # If the api print a notification when the rate limit is hit
                wait_on_rate_limit_notify=True)

            return twitter_session
        except:
            raise TwitterAPIError

    @staticmethod
    def past_week_end_date() -> datetime:
        """Function to generate past Saturday (End of Week),
        while considering Sunday = 0 and Saturday = 7

        Returns:
           past_saturday (datetime): Date from past saturday with truncated hour
        """
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_saturday = current_date - \
            timedelta(days=((datetime.now().isoweekday() + 1) % 7))
        return past_saturday

    def get_posts_from_range(self, **kwargs) -> List:
        """Get posts from specificed date or use default range

        Raises:
            TwitterNoPostsFound: If no posts are found an error is raised.

        Returns:
            List: All tweets retrieved from API
        """
        list_tweets = []

        # Default start date to find tweets if nothing is provided
        default_start = (Twitter.past_week_end_date() -
                         timedelta(days=6)).strftime("%Y-%m-%d")
        # Default end date to find tweets if nothing is provided
        default_end = (Twitter.past_week_end_date()).strftime("%Y-%m-%d")
        # Set dates to search tweets
        startDate = (kwargs.get("startDate") if kwargs.get(
            "startDate") != "" else default_start)
        endDate = (kwargs.get("endDate") if kwargs.get(
            "startDate") != "" else default_end)
        # Set keyword(s) to search
        text_query = kwargs.get("text_query")
        # Set max tweets per request
        max_tweets = kwargs.get("max_tweets", 100)
        print(f"start_date: {startDate}")
        print(f"end_date: {endDate}")

        # To manage the Twitter API pagination use the oject .Cursor() is required to go
        # through twitter for the required tweets

        #  Pass into the items() methods to set the limit you want to impose.
        response_tweets = tweepy.Cursor(self.api.search,
                                        q=text_query,
                                        until=endDate,
                                        weet_mode="extended").items(max_tweets)

        # issues with authentication can raise an generic error.
        try:

            for tweet in response_tweets:

                tw_hashtags = [hashtag["text"].lower()
                               for hashtag in tweet.entities["hashtags"]]

                if "flixbus" in tw_hashtags:

                    if tweet.created_at >= datetime.strptime(startDate, "%Y-%m-%d") \
                            and tweet.created_at <= datetime.strptime(endDate, "%Y-%m-%d"):

                        list_tweets.append({"tw_user_id": hashlib.md5((tweet.author._json["screen_name"]).encode("utf8")).hexdigest(),
                                            "tw_location": tweet.author._json["location"],
                                            "tw_num_followers": tweet.author._json["followers_count"],
                                            "tw_created_at": str(tweet.created_at),
                                            "tw_hashtags": tw_hashtags,
                                            "tw_num_tweets": tweet.author._json["statuses_count"],
                                            "tw_is_retweet": "yes" if hasattr(tweet, 'retweeted_status') else "no",
                                            "dt_processing": str(date.today())
                                            })
            if len(list_tweets) > 0:
                return list_tweets
            else:
                raise TwitterNoPostsFound
        except TweepError:
            raise TwitterAuthorizationError

    def is_api_available(self) -> bool:
        """Check if Twitter API is available

        Raises:
            TwitterAPIUnavailable: Exception if API is not avaialble

        Returns:
            Bool: Returns true if API is available.
        """

        # FlixBus Account
        id = "999925369"
        try:
            self.api.get_status(id)
            return True
        except:
            raise TwitterAPIUnavailable
