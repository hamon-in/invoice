import datetime
from decimal import Decimal
import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, BLOB, Date, Boolean, Table
from sqlalchemy.orm import sessionmaker, relationship

import yaml

from  .helpers import memoise, wrap

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
    system = Column(Boolean())

    

class Account(InvoiceBase, Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key = True)
    name = Column(String(50))
    address = Column(String(500))
    phone = Column(String(15))
    email = Column(String(30))
    pan = Column(String(10))
    serv_tax_num = Column(String(10))
    bank_details = Column(String(500))
    prefix = Column(String(10))
    clients = relationship('Client', backref="account")

    def summary(self, indent = 0):
        ret = []
        extra_indent = 18 # The length of "Address         : "
        ret.append(" "*indent + "Address         : {}".format(wrap(self.address.replace(r"\n", "\n"), indent+extra_indent)))
        ret.append(" "*indent + "Phone           : {}".format(self.phone))
        ret.append(" "*indent + "Email           : {}".format(self.email))
        ret.append(" "*indent + "PAN             : {}".format(self.pan))
        ret.append(" "*indent + "Serv tax number : {}".format(self.serv_tax_num))
        ret.append(" "*indent + "Bank details    : {}".format(wrap(self.bank_details.replace(r"\n", "\n"), indent+extra_indent)))
        ret.append(" "*indent + "Prefix          : {}".format(self.prefix))
        return "\n".join(ret)

        
class Client(InvoiceBase, Base):
    __tablename__ = "clients"
    name = Column(String(50), primary_key = True)
    address = Column(String(500))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    invoices = relationship("Invoice", back_populates="client")
    timesheets = relationship("Timesheet", back_populates="client")
    


class InvoiceTemplate(InvoiceBase,  Base):
    __tablename__ = "templates"
    name = Column(String(50), primary_key = True)
    description = Column(String(200))
    template = Column(String(500))
    invoices = relationship("Invoice", back_populates="template")
    timesheets = relationship("Timesheet", back_populates="template")
    letterhead = Column(BLOB(1024*1024))

    @property
    def taxes(self):
        data = yaml.load(self.template)
        return data.get('taxes',{})

    @property
    def fields(self):
        data = yaml.load(self.template)
        return [x.strip() for x in data['rows'].strip().strip("|").split("|")]

    @property
    def footers(self):
        data = yaml.load(self.template)
        footer_rows = data['footer'].strip().split("\n")
        return [[t.strip() for t in x.strip("|").split("|")] for x in  footer_rows]

association_table = Table('invoice_tag', Base.metadata,
    Column('invoice_id', Integer, ForeignKey('invoices.id')),
    Column('tag_name', Integer, ForeignKey('invoicetags.name')))
        
class InvoiceTag(InvoiceBase, Base):
    __tablename__ = "invoicetags"
    name = Column(String, primary_key = True)
    invoices = relationship('Invoice', secondary=association_table, back_populates="tags")
    system = Column(Boolean(), default = False)

class Timesheet(InvoiceBase, Base):
    __tablename__ = "timesheets"
    id = Column(Integer, primary_key = True)
    template_id = Column(String, ForeignKey('templates.name'))
    template = relationship('InvoiceTemplate')
    client_id = Column(String,  ForeignKey('clients.name'))
    employee = Column(String(50))
    description = Column(String(100))
    date = Column(Date)
    data = Column(String(1000))
    client = relationship('Client')
    
    def summary(self, indent):
        ret = []
        ret.append(" "*indent + "Id         : {}".format(self.id))
        ret.append(" "*indent + "Date       : {}".format(self.date.strftime("%d %b %Y")))
        ret.append(" "*indent + "Template   : {}".format(self.template.name, self.template.description))
        ret.append(" "*indent + "Description: {}".format(self.description))
        return "\n".join(ret)
    
    @property
    def file_name(self):
        datestr = self.date.strftime("%Y%m%d")
        return "Timesheet-{}-{}-{}".format(datestr, self.client.name, self.employee)

    def serialise(self):
        data = json.loads(self.data)
        data = sorted(data.items(), key=lambda x: datetime.datetime.strptime(x[0], '%d/%m/%Y %a'))
        data = [[datetime.datetime.strptime(day, '%d/%m/%Y %a'), duration] for day,duration in data]
        
        return dict(client = self.client.name,
                    data = data,
                    date = self.date.strftime("%d/%b/%Y"),
                    desc = self.description,
                    emp = self.employee)

    def to_table(self):
        data = json.loads(self.data)
        data = sorted(data.items(), key=lambda x: datetime.datetime.strptime(x[0], '%d/%m/%Y %a'))
        org_table = ["| {} | {} |".format(k,Decimal(v).quantize(Decimal('0.01'))) for k,v in data]
        return "\n".join(org_table)
        
    def set_from_table(self, data):
        data = data.strip()
        ret = {}
        for i in (j.strip() for j in data.split("\n")):
            if i.startswith("#"):
                continue
            k,v = [x.strip() for x in i.strip("|").strip().split("|")]
            ret[k] = v
        self.data = json.dumps(ret)

            
                


class Invoice(InvoiceBase, Base):
    __tablename__ = "invoices"
    id = Column(Integer,  primary_key = True)
    date = Column(Date)
    template_id = Column(String, ForeignKey('templates.name'))
    template = relationship('InvoiceTemplate')
    particulars = Column(String)
    client = relationship('Client')
    client_id = Column(String,  ForeignKey('clients.name'))
    content = Column(String)
    tags = relationship('InvoiceTag', secondary=association_table, back_populates="invoices")
    
    def summary(self, indent):
        ret = []
        ret.append(" "*indent + "Id          : {}".format(self.id))
        ret.append(" "*indent + "Date        : {}".format(self.date.strftime("%d %b %Y")))
        ret.append(" "*indent + "Template    : {} ({})".format(self.template.name, self.template.description))
        ret.append(" "*indent + "Particulars : {}".format(self.particulars))
        ret.append(" "*indent + "Tags        : {}".format(", ".join(x.name for x in self.tags)))
        return "\n".join(ret)

    @property
    def file_name(self):
        datestr = self.date.strftime("%Y%m%d")
        return "Invoice-{}-{}-{}".format(datestr, self.client.name, self.particulars.replace(" ", "-")[:10])

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
    
    @property
    def columns(self):
        ret = []
        for i in self.content.split("\n"):
            i = i.strip()
            if i.startswith("#") or not i:
                continue
            fields = i.strip().strip("|").split("|")
            fields[-1] = Decimal(fields[-1]).quantize(Decimal('0.01'))
            ret.append(fields)
        return ret

        
    def serialise(self):
        """
        Takes all the data necessary to generate this invoice and converts
        it into a nice dictionary that can be used by the formatter to create
        the final PDF/HTML invoice.
        """
        client_address = self.client.address
        date = self.date.strftime("%d %b %Y")
        invoice_number = self.number
        return dict(client_address = client_address,
                    date = date,
                    particulars = self.particulars,
                    number = invoice_number,
                    fields = self.template.fields,
                    columns = self.columns,
                    footers = self.template.footers,
                    taxes = self.template.taxes,
                    bank_details = self.client.account.bank_details)
    


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
    

    
    

