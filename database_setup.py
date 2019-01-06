from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

"""Table to store users and their credentials"""


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    password = Column(String(80))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'id': self.id,
           'email': self.email,
           'picture': self.picture,
           'password': self.password,
        }

"""Table to store venue types, eg bars, cafe, etc"""


class VenueType(Base):
    __tablename__ = 'venue_type'

    id = Column(Integer, primary_key=True)
    type = Column(String(80))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'type': self.type,
            'user_id':self.user_id,
        }

"""Table to store venues and information including name, address, description,
    and user that created the venue"""


class Venue(Base):
    __tablename__ = 'venue'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    type_id = Column(Integer, ForeignKey('venue_type.id'))
    streetname = Column(String(80))
    postcode = Column(String(80))
    description = Column(String(500))
    user = relationship(User)
    venue_type = relationship(VenueType)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'streetname': self.streetname,
            'postcode': self.postcode,
            'description': self.description,
            'user_id': self.user_id,
        }


"""Establish sqllite database"""
engine = create_engine('postgresql://postgres:postgres@localhost:5432/catalog')

Base.metadata.create_all(engine)
