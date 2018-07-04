import os
import six
import copy
import numpy as np
# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

UserDescripClasses = set(["Science", "Education", "Computers & Electronics"])
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "/Users/AlexGuo/Desktop/TwitterAnalysis-af5fec03f5d2.json")


def classify_text(text):
    """Classifies content categories of the provided text."""
    client = language.LanguageServiceClient()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    document = types.Document(
        content=text.encode('utf-8'),
        type=enums.Document.Type.PLAIN_TEXT)

    categories = client.classify_text(document).categories
    return [(c.name, c.confidence) for c in categories]
