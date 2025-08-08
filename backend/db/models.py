from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Float
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Network(Base):
    __tablename__ = 'networks'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    domain = Column(String, unique=True)
    accounts = relationship("Account", back_populates="network")
    posts = relationship("Post", back_populates="network") 

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    network_id = Column(Integer, ForeignKey("networks.id"))
    network = relationship("Network", back_populates="accounts")
    url = Column(String, unique=True)
    followers = Column(BigInteger)
    score = Column(Float)
    blacklisted = Column(Boolean, default=False)
    just_added = Column(Boolean, default=True)
    posts = relationship("Post", back_populates="account")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="posts")
    network_id = Column(Integer, ForeignKey("networks.id"))
    network = relationship("Network", back_populates="posts")
    url = Column(String, unique=True)
    published_at = Column(DateTime)
    views = Column(BigInteger)
    likes = Column(BigInteger)
    comments = Column(BigInteger)
    score = Column(Float)
    used = Column(Boolean, default=False)
    description = Column(String)
