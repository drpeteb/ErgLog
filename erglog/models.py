from pyramid.security import (
    Allow,
    Everyone,
    )

from sqlalchemy import (
    Column,
    Integer,
    Text,
    Date,
    Boolean,
    PickleType,
    ForeignKey
    )

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import DBAPIError

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    )

from sqlalchemy.schema import(
    UniqueConstraint,
    )

from zope.sqlalchemy import ZopeTransactionExtension

# Database session
class DBInterface(object):

    def add_to_db(self, thing):
        try:
            DBSession.add(thing)
            DBSession.flush()
        except DBAPIError:
            raise

    def list_all(self, thing):
        try:
            thing_list = DBSession.query(thing).all()
        except DBAPIError:
            thing_list = []
        return thing_list

    def get_rower_by_username(self, username):
        try:
            rower = DBSession.query(Rower).filter_by(username=username).one()
            return rower
        except DBAPIError:
            raise

    def remove_rower_by_username(self, username):
        try:
            DBSession.delete(DBSession.query(Rower).filter_by(username=username).one())
            DBSession.flush()
        except DBAPIError:
            raise     

    def promote_admin(self, username):
        try:
            DBSession.query(Rower).filter_by(username=username).one().admin = True
            DBSession.flush()
        except DBAPIError:
            raise

    def demote_admin(self, username):
        try:
            DBSession.query(Rower).filter_by(username=username).one().admin = False
            DBSession.flush()
        except DBAPIError:
            raise
        
    def get_thing_by_id(self, class_to_fetch, id):
        try:
            thing = DBSession.query(class_to_fetch).filter_by(id=id).one()
            return thing
        except DBAPIError:
            raise

    def get_erg_type_by_mulitple_and_increment(self, class_to_fetch, multiple, increment):
        try:
            id = DBSession.query(class_to_fetch).filter_by(multiple=multiple).filter_by(increment=increment).one()
        except:
            raise

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DBI = DBInterface()

# Security
class RootFactory(object):
    __acl__ = [ (Allow, 'group:members', 'standard'),
                (Allow, 'group:admins', 'admin') ]
    def __init__(self, request):
        pass

# SQLAlchemy ORM classes
Base = declarative_base()

class Rower(Base):
    __tablename__ = 'rowers'
    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True)
    password = Column(Text)
    name = Column(Text, unique=True)
    admin = Column(Boolean)

    def __init__(self, username, password, name, admin=False):
        self.username = username
        self.password = password
        self.name = name
        self.admin = admin

class ErgTypeTime(Base):
    __tablename__ = 'fixed_times'
    id = Column(Integer, primary_key=True)
    increment = Column(Integer)
    multiple = Column(Integer)

    __table_args__ = (UniqueConstraint('increment', 'multiple', name='_increment_multiple_uc'),)

    def __init__(self, increment, multiple):
        self.increment = increment
        self.multiple = multiple

class ErgTypeDistance(Base):
    __tablename__ = 'fixed_distances'
    id = Column(Integer, primary_key=True)
    increment = Column(Integer)
    multiple = Column(Integer)

    __table_args__ = (UniqueConstraint('increment', 'multiple', name='_increment_multiple_uc'),)

    def __init__(self, increment, multiple):
        self.increment = increment
        self.multiple = multiple

class ErgRecordTime(Base):
    __tablename__ = 'time_erg_records'
    id = Column(Integer, primary_key=True)
    rower_id = Column(Integer, ForeignKey('rowers.id'))
    rower = relationship("Rower", backref=backref('time_erg_records', order_by=id, cascade="all, delete, delete-orphan"))
    date = Column(Date)
    increment = Column(Integer, ForeignKey('fixed_times.increment'))
    multiple = Column(Integer, ForeignKey('fixed_times.multiple'))
    distance = Column(Integer)
    split_list = Column(PickleType)

    def __init__(self, rower_id, date, distance, increment, multiple, split_list):
        self.rower_id = rower_id
        self.date = date
        self.distance = distance
        self.increment = increment
        self.multiple = multiple
        self.split_list = split_list

class ErgRecordDistance(Base):
    __tablename__ = 'distance_erg_records'
    id = Column(Integer, primary_key=True)
    rower_id = Column(Integer, ForeignKey('rowers.id'))
    rower = relationship("Rower", backref=backref('distance_erg_records', order_by=id, cascade="all, delete, delete-orphan"))
    date = Column(Date)
    increment = Column(Integer, ForeignKey('fixed_distances.increment'))
    multiple = Column(Integer, ForeignKey('fixed_distances.multiple'))
    time = Column(Integer)
    split_list = Column(PickleType)

    def __init__(self, rower_id, date, time, increment, multiple, split_list):
        self.rower_id = rower_id
        self.date = date
        self.time = time
        self.increment = increment
        self.multiple = multiple
        self.split_list = split_list
