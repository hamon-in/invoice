from collections import ChainMap
import logging
import os

from . import model

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


class AccountCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add_account,
                            'list' : self.list_accounts}


    def add_account(self):
        print (self.args['name'])
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




def get_commands():
    return {"init" : InitCommand,
            "account": AccountCommand}
