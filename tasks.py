from dbexchanges import Session, engine, Base, OCRImage, OCRSchedule
from celery import Celery

from io import BytesIO
from PIL import Image
import logging
import time
import random
from string import ascii_letters

app = Celery('tasks', broker='redis://127.0.0.1:6666', backend="redis://127.0.0.1:7777")
logging.basicConfig(filename='run.log', level=logging.DEBUG)
session = Session()

def get_image_from_db(image_url: str):
    """
    retrieves image from db
    :param image_url:
    :return:
    """
    r = session.query(OCRImage.color).filter(OCRImage.url == image_url).first()
    return r[0]

def save_processed_image_to_db(url: str, image):
    """
    saves image to db
    :param url:
    :param image:
    :return:
    """
    stream = BytesIO()
    image.save(stream, format="PNG")
    session.query(OCRImage).filter(OCRImage.url == url).update({"bw": stream.getvalue()})
    session.commit()
    stream.close()

@app.task
def desaturate(image_url: str, image_hash:str):
    """
    processes image to b&w
    :param image_url:
    :param image_hash:
    :return:
    """
    image = get_image_from_db(image_url)
    try:
        c = Image.open(BytesIO(image))
        l = c.convert('L')
        rgb = l.convert("RGB")
        save_processed_image_to_db(image_url, rgb)
        return image_hash
    except OSError as ose:
        logging.error("couldn't desaturate image %s, the error was: %s" % (image_url, ose))

@app.task
def ocr_api_call(imhash: str):
    """
    placeholder for a network api call
    :param imhash:
    :return:
    """
    r = session.query(OCRImage).filter(OCRImage.imhash==imhash).first()
    logging.info("processing image %s" % r.imhash)
    session.query(OCRImage).filter(OCRImage.imhash == imhash).update({"ocr_status": OCRSchedule.PENDING})
    session.commit()
    #### TODO try catch/timeout for error states
    time.sleep(random.randrange(0,60))
    # generate random string
    mock_ocr_text = "".join([random.choice(ascii_letters) for x in range(0,50)])
    ####
    session.query(OCRImage).filter(OCRImage.imhash == imhash).update({"ocr_status": OCRSchedule.DONE})
    session.query(OCRImage).filter(OCRImage.imhash == imhash).update({"ocr_result": mock_ocr_text})
    session.commit()