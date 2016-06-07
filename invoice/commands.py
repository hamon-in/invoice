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

class InitCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        print ("Database is {}".format(self.args))

    def __call__(self):
        """
        Handler for init command
        """
        self.l.debug("Creating database '%s'", self.args['db'])
        model.create_database(self.args['db'])


class CompanyCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        print ("Database is {}".format(self.args['db']))



def get_commands():
    return {"init" : InitCommand,
            "company": CompanyCommand}
