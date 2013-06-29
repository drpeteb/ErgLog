from sqlalchemy import (
    Column,
    Integer,
    Text,
    Date,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

def calculate_split(time, distance):
    split = time/(distance/500)
    return split

class Rower(Base):
    """SQLAlchemy declarative model class for Rower objects"""
    __tablename__ = 'rowers'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)

    def __init__(self, name):
        self.name = name

class ErgRecord(Base):
    """SQLAlchemy declarative model class for ErgRecord objects"""
    __tablename__ = 'ergrecords'
    id = Column(Integer, primary_key=True)
    rower_id = Column(Integer)          # Id of the rower who did this erg
    date = Column(Date, unique=True)    # Date of the erg
    time = Column(Integer)              # Time to complete in tenths
    distance = Column(Integer)          # Distance travelled in metres
    split = Column(Integer)             # Split in tenths

    def __init__(self, rower_id, date, distance):
        self.rower_id = rower_id
        self.date = date
        self.distance = distance
        self.time = 1800
        self.split = calculate_split(self.time, self.distance)


