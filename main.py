from io import BytesIO
from typing import List

from tornado.web import RequestHandler, Application, url
from dbexchanges import Session, engine, Base, OCRImage, OCRSchedule, RequestLog
from requests.exceptions import ConnectionError
from tasks import desaturate, ocr_api_call
from hashlib import md5
import tornado.ioloop
from datetime import datetime
from os import path
import requests
from PIL import Image
import logging
import base64
import json

Base.metadata.create_all(engine)
session = Session()
logging.basicConfig(filename='run.log', level=logging.DEBUG)

def get_catalogue() -> List[OCRImage]:
    return session.query(OCRImage).all()

def check_image_exists(imhash: str) -> bool:
    r = session.query(OCRImage).filter(OCRImage.imhash == imhash).first()
    if r is not None:
        logging.warning("%s already processed" % imhash)
        return True
    else:
        logging.info("%s absent from db, processing" % imhash)
        return False

class WatchPicture(RequestHandler):
    def get(self, image_md5: str, variant=None):
        o = session.query(OCRImage).filter(OCRImage.imhash == image_md5).first()
        if o is not None:
            color_image64 = base64.b64encode(o.color)
            bw_image64 = base64.b64encode(o.bw)
            if variant == "bw":
                self.write("<img src=\"data:image/png; base64, %s \"/>" % bw_image64.decode())
            else:
                self.write("<img src=\"data:image/png; base64, %s \"/>" % color_image64.decode())
        else:
            self.write({"status":"error","error":"no such image %s" % image_md5})


class BrowseImageCatalogue(RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        rows = {"items": [{"url":k.url,"ocr_status":k.ocr_status.name,"ocr_result":k.ocr_result,"md5": k.imhash} for k in get_catalogue()]}
        self.write(rows)

class FetchImageRequestHandler(RequestHandler):

    @staticmethod
    def download(image_url: str) :
        """
        downloads the picture at image_url
        returns (picture, b64encoded picture, file extension)
        :param image_url: URL for picture to process
        :return:
        """
        im = requests.get(image_url).content
        b64im = base64.b64encode(im)
        # get file extension
        file = image_url.rsplit('/', 1)[-1]
        _, ext = path.splitext(file)
        ext = ext.lower()
        ext = ext.strip('.')
        return im, b64im, ext

    def get(self, image_url: str):
        if image_url:
            rl = RequestLog(request_url=image_url, timestamp=datetime.utcnow())
            session.add(rl)
            session.commit()
            try:
                im, b64im, ext = self.download(image_url)
                # check if target can be parsed as an image
                Image.open(BytesIO(im))
                imhash = md5(im).hexdigest()
                exists = check_image_exists(imhash)
                if not exists:
                    o = OCRImage(url=image_url, color=im, bw=None, ocr_status=OCRSchedule.SCHEDULED,ocr_result=None, imhash=imhash)
                    session.add(o)
                    session.commit()
                    res = {"md5": imhash, "url": image_url,"status":"ok"}
                    # desaturate, then call ocr task when done
                    desaturate.apply_async([image_url, imhash], link=ocr_api_call.s())
                    self.write(res)
                else:
                    res = {"md5": imhash, "url": image_url, "status": "error", "error": "image already processed"}
                    self.write(res)
            except ConnectionError as ce:
                res = {"status":"error","error":"couldn't download image at %s" % image_url}
                self.write(res)
            except OSError as ose:
                res = {"status": "error", "error": "%s doesn't look like a picture file" % image_url}
                self.write(res)

if __name__ == "__main__":
    logging.info("starting server")
    app = Application([
        url(r"/download/(.*)", FetchImageRequestHandler),
        url(r"/catalogue", BrowseImageCatalogue),
        url(r"/watch/(.*)/(.*)", WatchPicture)
        ]
    )
    app.listen(5555)
    tornado.ioloop.IOLoop.current().start()
    session.close()