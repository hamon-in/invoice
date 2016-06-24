from collections import ChainMap
import logging
import os

import yaml

from . import model
from . import helpers

class Command:
    def __init__(self, args):
        envars_config = {k.replace("INVOICE_", "").lower():v 
                         for k,v in os.environ.items() 
                         if k.startswith("INVOICE_")}
        self.args = ChainMap(args.__dict__, envars_config)
        self.l = logging.getLogger("invoice")

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
        super().__init__(args)

    def __call__(self):
        """
        Handler for init command
        """
        self.l.debug("Creating database '%s'", self.args['db'])
        model.create_database(self.args['db'])

class SummaryCommand(Command):
    def __init__(self, args):
        super().__init__(args)
    
    def __call__(self):
        sess = model.get_session(self.args['db'])

        self.l.info("Config:")
        for i in sess.query(model.Config).all():
            self.l.info("%10s:%10s", i.name, i.value)
        self.l.info("-"*20)
        
        self.l.info("Accounts:")
        for account in sess.query(model.Account).all():
            self.l.info(" %s", account.name)
            for client in account.clients:
                self.l.info("  %s", client.name)
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
        template = """# Edit the following template to suit your needs
# The file is in yaml
# | separates fields

# Remove taxes that you don't need
taxes:
     - service: 0.12
     - kk_cess: 0.5
     - sb_cess: 0.5


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
        template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name==self.args['name']).one()
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
        template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name==self.args['name']).one()
        sess.delete(template)
        sess.commit()

    
        
        


class AccountCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add_account,
                            'list' : self.list_accounts}


    def add_account(self):
        account = model.Account(name = self.args['name'],
                                address = self.args['address'],
                                phone = self.args['phone'],
                                email = self.args['email'],
                                pan = self.args['pan'],                                
                                serv_tax_num = self.args['serv'],
                                bank_account_num = self.args['acc'],
                                prefix = self.args['prefix'])
        sess = model.get_session(self.args['db'])
        sess.add(account)
        sess.commit()

    def list_accounts(self):
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
        account = sess.query(model.Account).filter(model.Account.name == self.args['account']).one()
        print (account)
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
        self.sc_handlers = {'add'  : self.add}
    
    def add(self):
        self.l.debug("Adding invoice")



def get_commands():
    return {"init"     : InitCommand,
            "account"  : AccountCommand,
            "client"   : ClientCommand,
            "template" : TemplateCommand,
            "summary"  : SummaryCommand,
            "invoice"  : InvoiceCommand}
