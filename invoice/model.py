from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, BLOB
from sqlalchemy.orm import sessionmaker, relationship

from  .helpers import memoise

Base = declarative_base()

class InvoiceBase:
    def __repr__(self):
        return "<{}(name='{}'...)>".format(self.__class__.__name__, self.name)

class Config(InvoiceBase, Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key = True)
    name = Column(String(50), unique = True)
    value = Column(String(100))

class Account(InvoiceBase, Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key = True)
    name = Column(String(50))
    address = Column(String(500))
    phone = Column(String(15))
    email = Column(String(30))
    pan = Column(String(10))
    serv_tax_num = Column(String(10))
    bank_account_num = Column(String(20))
    prefix = Column(String(10))
    clients = relationship('Client', backref="account")

class Client(InvoiceBase, Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key = True)
    name = Column(String(50))
    address = Column(String(500))
    account_id = Column(Integer, ForeignKey('accounts.id'))

class InvoiceTemplate(InvoiceBase,  Base):
    __tablename__ = "templates"
    name = Column(String(50), primary_key = True)
    description = Column(String(200))
    template = Column(String(500))
    
class Invoice(InvoiceBase, Base):
    __tablename__ = "invoices"
    id = Column(Integer,  primary_key = True)
    date = Column(String(500))
    template = relationship('InvoiceTemplate')
    template_id = Column(String, ForeignKey('templates.name'))


@memoise
def get_session(db_file):
    url = "sqlite:///{}".format(db_file)
    engine = create_engine(url)
    Session = sessionmaker(bind = engine)
    session = Session()
    return session

def create_database(db_file):
    url = "sqlite:///{}".format(db_file)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    

    
    

