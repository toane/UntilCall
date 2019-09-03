from sqlalchemy import Integer, String, BLOB, Column, Enum, create_engine, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

Base = declarative_base()

class OCRSchedule(enum.Enum):
    SCHEDULED = 0 # should be done at some point
    PENDING = 1 # ocr request is running
    DONE = 2 # got a response from ocr service


class OCRImage(Base):
    __tablename__ = 'images'
    id=Column(Integer, primary_key=True)
    url=Column('url', String(32))
    color=Column('color', BLOB)
    bw=Column('bw', BLOB)
    ocr_status=Column('ocr_status', Enum(OCRSchedule))
    ocr_result=Column('ocr_result', String)
    imhash = Column('imhash', String, unique=True)

    def __init__(self, url, color, bw, ocr_status, ocr_result, imhash):
        self.url = url
        self.color = color
        self.bw = bw
        self.ocr_status = ocr_status
        self.ocr_result = ocr_result
        self.imhash = imhash # md5

class RequestLog(Base):
    __tablename__ = 'requestlog'
    id=Column(Integer, primary_key=True)
    request_url = Column('request_url', String(32))
    timestamp = Column('timestamp', Date)

    def __init__(self, request_url, timestamp):
        self.request_url = request_url
        self.timestamp = timestamp

engine = create_engine('sqlite:///alchemy.db')
Session = sessionmaker(bind=engine)

