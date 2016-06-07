from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine

Base = declarative_base()

class InvoiceBase:
    def __repr__(self):
        return "<{}(name='{}'...)>".format(self.name)

class Config(InvoiceBase, Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key = True)
    name = Column(String(50), unique = True)
    value = Column(String(100))

class Account(InvoiceBase, Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key = True)
    name = Column(String(50))


def create_database(db_file):
    url = "sqlite:///{}".format(db_file)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    
    
    
    

