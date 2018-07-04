import os
import time
import tweepy
from TFLibrary.utils import misc_utils


class TwitterTweeter(object):
    def __init__(self,
                 consumer_key, consumer_secret,
                 access_token, access_token_secret):

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)

        self._api = api
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret

    def _retweet(self, tweet_ID):
        self._api.retweet(tweet_ID)

    def retweet(self, tweet_IDs):
        for tweet_ID in tweet_IDs:

            try:
                self._retweet(tweet_ID)
                time.sleep(5)

            except tweepy.TweepError as e:
                print(e)


class TwitterReader(object):

    def __init__(self, logdir,
                 consumer_key, consumer_secret,
                 access_token, access_token_secret,
                 filter_fns, process_fns,
                 load_from_history=True, debug=False):

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)

        if not os.path.isdir(logdir):
            os.makedirs(logdir)

        self._api = api
        self._logdir = logdir
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret

        self._filter_fns = filter_fns
        self._process_fns = process_fns

        self._debug = debug

        # load previously cached data
        if load_from_history and \
                os.path.exists(self.home_timeline_history_logdir) and \
                os.path.exists(self.friendship_history_logdir):

            self._tweet_collections = misc_utils.load_object(
                self.home_timeline_history_logdir)
            self._friendship_collections = misc_utils.load_object(
                self.friendship_history_logdir)

            misc_utils.assert_all_same([
                len(self._tweet_collections),
                len(self._friendship_collections)])

        else:
            self._tweet_collections = []
            self._friendship_collections = []

    def reading_tweets(self, screen_name="AlexGuoHan"):
        for tweets in tweepy.Cursor(self._api.home_timeline,
                                    screen_name=screen_name).pages():
            # get friendship
            friendships = self._get_friendships(tweets)

            # cache the objects, and save to disk
            self._tweet_collections.extend(tweets)
            self._friendship_collections.extend(friendships)

            misc_utils.save_object(self._tweet_collections,
                                   self.home_timeline_history_logdir)
            misc_utils.save_object(self._friendship_collections,
                                   self.friendship_history_logdir)

            yield tweets, friendships
            if self._debug:
                break

            time.sleep(60)

    def filter_tweets(self, tweets, friendships):
        filtered_tweets = []
        for tweet, friendship in zip(tweets, friendships):
            _be_kept = [fn(tweet, friendship)
                        for fn in self._filter_fns]
            if all(_be_kept):
                filtered_tweets.append(tweet)

        return filtered_tweets

    def process_tweets(self, tweets):
        processed_tweets = []
        for tweet in tweets:
            processed_tweet = misc_utils.merge_dicts(*
                [fn(tweet) for fn in self._process_fns])
            processed_tweets.append(processed_tweet)

        return processed_tweets

    def _get_friendships(self, tweets):
        friendships = []
        for tweet in tweets:
            friendship = self._api.show_friendship(
                source_screen_name="AlexGuoHan",
                target_id=tweet.user.id)
            friendships.append(friendship)
        return friendships

    @property
    def num_history(self):
        if len(self._tweet_collections) != len(self._friendship_collections):
            raise ValueError(
                "len(tweet_collections) != len(friendship_collections)")
        return len(self._tweet_collections)

    @property
    def home_timeline_history_logdir(self):
        return os.path.join(self._logdir, "home_timeline.pkl")

    @property
    def friendship_history_logdir(self):
        return os.path.join(self._logdir, "friendship.pkl")
