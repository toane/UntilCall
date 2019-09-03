import requests
import pytest
from dbexchanges import Session, OCRImage, Base, engine
from unittest.mock import Mock, create_autospec, patch

session = Session()


@pytest.fixture
def test_url():
    return "http://placehold.jp/24/cc9999/993333/150x100.png"

@pytest.fixture
def prepare():
    # clear images table
    session.query(OCRImage).delete()
    session.commit()

def test_process_image(prepare, test_url):
    """
    processing a new image should work
    :return:
    """
    p = requests.get("http://127.0.0.1:5555/download/%s" % test_url).json()
    assert p["status"] == "ok"

def test_process_existing(test_url):
    """
    processing a known image should't work
    :return:
    """
    p = requests.get("http://127.0.0.1:5555/download/%s" % test_url).json()
    assert p["status"] == "error"

def test_bw_exists(test_url):
    """
    we should have bw data for the image
    :return:
    """
    im = session.query(OCRImage).filter(OCRImage.url == test_url).first()
    assert im.bw is not None

def test_catalogue(test_url):
    """
    our image should be in the catalogue
    :return:
    """
    p = requests.get("http://127.0.0.1:5555/catalogue").json()
    assert test_url in [x['url'] for x in p["items"]]


