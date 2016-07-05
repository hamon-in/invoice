import datetime
from collections import ChainMap
import logging
import os

import yaml
from sqlalchemy.orm.exc import NoResultFound

from . import model
from . import helpers
from . import formatters
from . import __version__


class Command:
    def __init__(self, args, db_init = True):
        envars_config = {k.replace("INVOICE_", "").lower():v 
                         for k,v in os.environ.items() 
                         if k.startswith("INVOICE_")}
        self.args = ChainMap(args.__dict__, envars_config)
        self.l = logging.getLogger("invoice")
        self.formatters = formatters.get_formatters()

        # Check database version
        if db_init:
            sess = model.get_session(self.args['db'])
            try:
                db_version = sess.query(model.Config).filter(model.Config.name == "version").one().value
                if db_version != __version__:
                    self.l.critical("Database version is %s. Software version is %s. Can't proceed.", db_version, __version__)
                    raise TypeError("Database version mismatch")
                self.l.info("Database version is '%s'", db_version)
            except NoResultFound:
                self.l.critical("No version found in database. Cannot proceed.")
                raise
        

    def __call__(self):
        sc_name = self.args['op']
        self.l.debug(" Sub command %s", self.args['op'])

        try:
            sc_handler = self.sc_handlers[sc_name]
        except KeyError:
            self.l.error("No handler for command %s", self.args['op'])
            raise
        return sc_handler()


class InitCommand(Command):
    def __init__(self, args):
        super().__init__(args, db_init = False)

    def __call__(self):
        """
        Handler for init command
        """
        self.l.debug("Creating database '%s'", self.args['db'])
        model.create_database(self.args['db'])
        sess = model.get_session(self.args['db'])
        c = model.Config(name = "version", value = __version__, system = True)
        sess.add(c)
        sess.commit()

class SummaryCommand(Command):
    def __init__(self, args):
        super().__init__(args)
    
    def __call__(self):
        sess = model.get_session(self.args['db'])

        self.l.info("Config:")
        for i in sess.query(model.Config).all():
            system = "*" if i.system else ''
            self.l.info("%s %10s:%10s", system, i.name, i.value)
        self.l.info("-"*20)
        
        for account in sess.query(model.Account).all():
            self.l.info("Account: %s", account.name)
            for client in account.clients:
                self.l.info("  Client: %s", client.name)
                for invoice in client.invoices:
                    self.l.info("     %s | %s | %s", invoice.id, invoice.date.strftime("%d/%m/%Y") , invoice.particulars)
        self.l.info("-"*20)

        self.l.info("Invoice templates:")
        for template in sess.query(model.InvoiceTemplate).all():
            self.l.info(" %s", template.name)        
        self.l.info("-"*20)

            
            
class TemplateCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {"add"  : self.add,
                            "edit" : self.edit,
                            "rm"   : self.rm}


    def add(self):
        template = """# -*- yaml -*-
# Local Variables: 
# eval: (orgtbl-mode) 
# End:
# Edit the following template to suit your needs
# The file is in yaml
# | separates fields

# Remove taxes that you don't need
taxes:
   service: 0.12
   kk_cess: 0.5
   sb_cess: 0.5


rows: |
        | Serial no | Description | Quantity | Rate | Total |


footer: |
        | | | | Net total | {net_total} |
        | | | | Service tax | {service} |
        | | | | KK Cess | {kk_cess} |
        | | | | Swach Bharat Cess | {sb_cess} |
        | | | | Gross total | {gross_total} |
        
"""
        for i in range(2):
            fname, template = helpers.get_from_file(template)
            try:
                yaml.load(template)
                break
            except yaml.YAMLError:
                if i != 1:
                    self.l.warn("Error in input. Please check again")
                    input()
        else:
            self.l.critical("Error in template format. Aborting")
            raise ValueError("Bad format in invoice template. Can't proceed.")
        letterhead = ''
        if self.args['letterhead']:
            self.l.debug("Adding letterhead")
            with open(self.args['letterhead'], "rb") as f:
                letterhead = f.read()

        temp = model.InvoiceTemplate(name = self.args['name'], 
                                     description = self.args['desc'], 
                                     template = template,
                                     letterhead = letterhead)
        sess = model.get_session(self.args['db'])
        sess.add(temp)
        sess.commit()

    def edit(self):
        sess = model.get_session(self.args['db'])
        try:
            template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name==self.args['name']).one()
        except NoResultFound:
            self.l.critical("No such template '%s'",self.args['name'])
            raise 
        if 'desc' in self.args:
            template.description = self.args['desc']
            self.l.debug("Description of %s updated", self.args['name'])
        else:
            for i in range(2):
                fname, new_template = helpers.get_from_file(template.template)
                try:
                    yaml.load(new_template)
                    template.template = new_template
                    self.l.debug("Template of %s updated", self.args['name'])
                    break
                except yaml.YAMLError:
                    if i != 1:
                        self.l.warn("Error in input. Please check again")
                        input()
            else:
                self.l.critical("Error in template format. Aborting")
                raise ValueError("Bad format in invoice template. Can't proceed.")

        sess.add(template)
        sess.commit()
        self.l.debug("Saved")
        
    def rm(self):
        sess = model.get_session(self.args['db'])
        try:
            template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name==self.args['name']).one()
        except NoResultFound:
            self.l.critical("No such template '%s'", self.args['name'])
            raise
        sess.delete(template)
        sess.commit()

    
        
        


class AccountCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add,
                            'list' : self.list,
                            'edit' : self.edit}

    def edit(self):
        name = self.args["name"]
        address = self.args["address"]
        phone = self.args["phone"]
        email = self.args["email"]
        pan = self.args["pan"]
        serv = self.args["serv"]
        bank_details = self.args["bank_details"]
        prefix = self.args["prefix"]

        sess = model.get_session(self.args['db'])
        try:
            account = sess.query(model.Account).filter(model.Account.name == name).one()
        except NoResultFound:
            self.l.critical("No account with name %s", name)
            raise

        if address:
            account.address = address
        if phone:
            account.phone = phone
        if email:
            account.email = email
        if pan:
            account.pan = pan
        if serv:
            account.serv_tax_num = serv
        if bank_details:
            account.bank_details = bank_details
        if prefix:
            account.prefix = prefix

        sess.add(account)
        sess.commit()

    def add(self):
        account = model.Account(name = self.args['name'],
                                address = self.args['address'],
                                phone = self.args['phone'],
                                email = self.args['email'],
                                pan = self.args['pan'],                                
                                serv_tax_num = self.args['serv'],
                                bank_details = self.args['bank_details'],
                                prefix = self.args['prefix'])
        sess = model.get_session(self.args['db'])
        sess.add(account)
        sess.commit()

    def list(self):
        sess = model.get_session(self.args['db'])
        self.l.info("Accounts")
        for i in sess.query(model.Account).all():
            self.l.info(" %5d | %s",i.id, i.name)

class ClientCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add_client,
                            'list' : self.list_clients}

    def add_client(self):
        sess = model.get_session(self.args['db'])
        try:
            account = sess.query(model.Account).filter(model.Account.name == self.args['account']).one()
        except NoResultFound:
            self.l.critical("No such account '%s'", self.args['account'])
            raise

        client = model.Client(name = self.args['name'],
                              address = self.args['address'],
                              account = account)


        sess.add(client)
        sess.commit()

    
    def list_clients(self):
        sess = model.get_session(self.args['db'])
        self.l.info("Clients")
        for i in sess.query(model.Client).all():
            self.l.info(" %5d | %s | %s ",i.id, i.name, i.account.name)


class InvoiceCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add,
                            'generate' : self.generate,
                            'edit' : self.edit,
                            "rm" : self.rm}
    
    def add(self):
        self.l.debug("Adding invoice")
        sess = model.get_session(self.args['db'])
        date = datetime.datetime.strptime(self.args['date'], "%d/%m/%Y")
        subject = self.args['particulars']
        try:
            template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name == self.args['template']).one()
        except NoResultFound:
            self.l.critical("No such template '%s'", self.args['template'])
            raise
        try:
            client = sess.query(model.Client).filter(model.Client.name == self.args['client']).one() 
        except NoResultFound:
            self.l.critical("No such client '%s'", self.args['client'])
            raise
        
        fields = template.fields
        boilerplate = """# -*- text -*-
# Local Variables: 
# eval: (orgtbl-mode) 
# End:
#
# The fields are as follows
# {}
#
#

|{}|

""".format(", ".join(fields), "|".join(["          "]*5))

        _, data = helpers.get_from_file(boilerplate)
        invoice = model.Invoice(date = date,
                                particulars = subject,
                                content = data,
                                template = template,
                                client = client)
        sess.add(invoice)

        sess.commit()
        
    def generate(self):
        sess = model.get_session(self.args['db'])
        date_start = datetime.datetime.strptime(self.args['from'], "%d/%m/%Y")
        date_to = datetime.datetime.strptime(self.args['to'], "%d/%m/%Y")
        fmt_name = self.args['format']
        formatter = self.formatters[fmt_name]()

        self.l.info("Invoices between %s and %s", self.args['from'], self.args['to'])
        invoices = sess.query(model.Invoice).join(model.Client).filter(model.Client.name == self.args['client'],
                                                                       date_start <= model.Invoice.date,
                                                                       model.Invoice.date <= date_to).all()
        if invoices:
            for invoice in invoices:
                self.l.info("  Generating invoice %s", invoice.file_name)
                formatter.generate(invoice)
        else:
            self.l.critical("No invoices found matching these criteria")

    def rm(self):
        sess = model.get_session(self.args['db'])
        id_ = self.args['id']
        try:
            invoice = sess.query(model.Invoice).filter(model.Invoice.id == id_).one()
        except NoResultFound:
            self.l.critical("No invoice with id %s", id_)
            raise
        sess.delete(invoice)
        sess.commit()

    def edit(self):
        id = self.args["id"]
        client = self.args["client"]
        template = self.args["template"]
        date = self.args["date"]
        particulars = self.args["particulars"]
        edit_content = self.args['edit']
        
        sess = model.get_session(self.args['db'])
        try:
            invoice = sess.query(model.Invoice).filter(model.Invoice.id == id).one()
        except NoResultFound:
            self.l.critical("No invoice with id %s", id)
            raise

        if client:
            try:
                client = sess.query(model.Client).filter(model.Client.name == client).one()
                invoice.client = client
            except NoResultFound:
                self.l.critical("No such client '%s'", client)
                raise

        if template:
            try:
                template  = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name == template).one()
                invoice.template = template
            except NoResultFound:
                self.l.critical("No such template '%s'", template)
                raise
        if date:
            invoice.date = datetime.datetime.strptime(date, "%d/%m/%Y")
        if particulars:
            invoice.particulars = particulars

        if edit_content:
            _, data = helpers.get_from_file(invoice.content)
            invoice.content = data

        sess.add(invoice)
        sess.commit()

        




def get_commands():
    return {"init"     : InitCommand,
            "account"  : AccountCommand,
            "client"   : ClientCommand,
            "template" : TemplateCommand,
            "summary"  : SummaryCommand,
            "invoice"  : InvoiceCommand}
