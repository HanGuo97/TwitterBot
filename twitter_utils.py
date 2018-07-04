import copy
import spacy
import numpy as np
from . import gcloud_utils
import preprocessor as twitter_prepro

# nlp = spacy.load('en_core_web_sm')
twitter_prepro.set_options(twitter_prepro.OPT.URL, twitter_prepro.OPT.EMOJI)


def _tweet_preprocessing(tweet_texts):
    """Preprocessing
        1. remove URLs (and put them in separate place)
        2. remove Emojis

    Returns the cleaned Tweet and parsed URLs
    """
    cleaned_tweet_texts = twitter_prepro.clean(tweet_texts)
    parsed_url = twitter_prepro.parse(tweet_texts).urls
    if parsed_url is not None:
        parsed_url = [u.match for u in parsed_url]

    return cleaned_tweet_texts, parsed_url


def filter_by_following(tweet, frienship):
    return frienship[0].following


def get_basic_tweet_info(tweet):
    text, urls = _tweet_preprocessing(tweet.text)
    return {
        "TweetID": tweet.id,
        "RawTweet": tweet.text,
        "ProcessedTweet": text,
        "URLs": urls}


def get_basic_tweet_user_info(tweet):
    description, urls = _tweet_preprocessing(tweet.user.description)
    text_classes, wanted_text_classes = _get_text_classification(description)

    return {
        "UserID": tweet.user.id,
        "UserName": tweet.user.name,
        "UserDescrip": description,
        "UserDescripURLs": urls,
        "UserDescripClassif": text_classes,
        "UserDescripWantedClassif": wanted_text_classes}


def _get_text_classification(text):
    try:
        maybe_expanded_text = _duplicate_if_required(text)
        text_classes = gcloud_utils.classify_text(maybe_expanded_text)
        # [{Science}, {Computer Science, Education}]
        # --> {Science, Computer Science, Education}
        wanted_text_classes = _merge_sets([
            # filter text classes belonging to the the classes
            # defined in `gcloud_utils.UserDescripClasses`
            # e.g. only those who has `Science` in text categories
            gcloud_utils.UserDescripClasses.intersection(p[0].split("/"))
            for p in text_classes])

        return text_classes or None, wanted_text_classes or None

    except Exception as e:
        print("Trigger Some Errors, ignored:\t", e)
        return None, None


def _duplicate_if_required(text, min_tokens=20):
    """Used in GCloud Text Classification to Satisfy its minimum token count

        If texts = [a b c d e ...], duplicates into [a b c d e . a b c ...]

    """
    tokens = text.split()
    if len(tokens) < min_tokens:
        # print("Text has length %d < %d" % (len(tokens), min_tokens))

        _tokens = copy.deepcopy(tokens)
        _tokens.insert(0, ".")
        duplicate_times = int(np.floor(min_tokens / len(tokens)))
        for _ in range(duplicate_times):
            tokens.extend(_tokens)
    return " ".join(tokens)


def _merge_sets(list_of_sets):
    """[{Set1}, {Set2}] --> {Set1} | {Set2}"""
    merged_sets = set()
    for element in list_of_sets:
        merged_sets = merged_sets | element
    return merged_sets
