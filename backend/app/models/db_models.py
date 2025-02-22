from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# Association table for the many-to-many relationship between users and tournaments
user_tournaments = Table('user_tournaments', Base.metadata,
                         Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                         Column('tournament_id', Integer, ForeignKey('tournaments.id'), primary_key=True)
                         )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)

    tournaments = relationship('Tournament', secondary=user_tournaments, back_populates='organizers')


class Tournament(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    sheets_link = Column(String, nullable=False)
    form_link = Column(String, nullable=False)
    sign_up_deadline = Column(DateTime, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    organizers = relationship('User', secondary=user_tournaments, back_populates='tournaments')
