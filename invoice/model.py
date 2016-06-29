from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, BLOB, Date
from sqlalchemy.orm import sessionmaker, relationship

import yaml

from  .helpers import memoise

Base = declarative_base()

class InvoiceBase:
    def __repr__(self):
        name = self.name if hasattr(self, "name") else self.id
        return "<{}(name='{}'...)>".format(self.__class__.__name__, name)

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
    name = Column(String(50), primary_key = True)
    address = Column(String(500))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    invoices = relationship("Invoice", back_populates="client")
    
class InvoiceTemplate(InvoiceBase,  Base):
    __tablename__ = "templates"
    name = Column(String(50), primary_key = True)
    description = Column(String(200))
    template = Column(String(500))
    invoices = relationship("Invoice", back_populates="template")
    letterhead = Column(BLOB(1024*1024))

    def fields(self):
        data = yaml.load(self.template)
        return [x.strip() for x in data['rows'].split("|")]

class Invoice(InvoiceBase, Base):
    __tablename__ = "invoices"
    id = Column(Integer,  primary_key = True)
    date = Column(Date)
    template = relationship('InvoiceTemplate')
    particulars = Column(String)
    client = relationship('Client')
    template_id = Column(String, ForeignKey('templates.name'))
    client_id = Column(String,  ForeignKey('clients.name'))
    content = Column(String)

    @property
    def file_name(self):
        datestr = self.date.strftime("%Y%m%d")
        return "{}-{}-{}".format(datestr, self.client.name, self.particulars.replace(" ", "-")[:10])

    @property
    def number(self):
        curr_year = int(self.date.strftime("%Y"))
        curr_month = int(self.date.strftime("%m"))
        if 1 <= curr_month <= 4: 
            next_year = curr_year
            curr_year -= 1
        else:
            next_year = curr_year + 1
        return "{}/{}-{}".format(curr_year, next_year, self.id)
            
    def serialise(self):
        """
        Takes all the data necessary to generate this invoice and coverts
        it into a nice dictionary that can be used by the formatter to 
        create the final PDF/HTML invoice.
        """
        client_address = self.client.address
        date = self.date.strftime("%d %b %Y")
        invoice_number = self.number
        return dict(client_address = client_address,
                    date = date,
                    number = invoice_number)
    


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
    

    
    

