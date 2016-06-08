import argparse
import logging

from . import model
from . import commands

l = None

def setup_logging(level = logging.DEBUG):
    global l 
    l = logging.getLogger("invoice")
    l.setLevel(level)
    shandler = logging.StreamHandler()
    shandler.setFormatter(logging.Formatter("%(message)s"))
    shandler.setLevel(level)
    l.addHandler(shandler)
    

def parse_args():
    parser = argparse.ArgumentParser(description = "Manage invoices")
    parser.add_argument("-f", "--file" , dest = "db", help = "Name of database file", default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(title="Commands", dest="command", help = "Commands available")
    subparsers.required = True

    init_parser = subparsers.add_parser("init", help="Initialise invoice database")

    account_parser = subparsers.add_parser("account", help="Manage Accounts")
    account_parser.add_argument("-v", "--verbose", help="Display verbose output")

    account_subparsers = account_parser.add_subparsers(title = "Account commands", dest="acc_op", metavar = "<Account operation>", help="Commands to manipulate accounts")
    account_subparsers.required = True
    account_add_parser = account_subparsers.add_parser("add", help = "Create a new account")
    account_add_parser.add_argument("-n", "--name", help = "Name of account", required = True)
    account_add_parser.add_argument("-a", "--address", help = "Billing address account", required = True)
    account_add_parser.add_argument("-p", "--phone", help = "Phone number", required = True)
    account_add_parser.add_argument("-e", "--email", help = "Email address", required = True)
    account_add_parser.add_argument("--pan", help = "Pan number")
    account_add_parser.add_argument("--serv", help = "Service tax number")
    account_add_parser.add_argument("--acc", help = "Bank account number")
    account_add_parser.add_argument("--prefix", help = "Invoice number prefix")
    
    account_add_parser = account_subparsers.add_parser("list", help = "List accounts")

    args = parser.parse_args()
    return args


def dispatch(args):
    cmd = args.command if hasattr(args, "command") else ""
    l.debug("Command is '%s'", cmd)
    dispatcher = commands.get_commands()
    command_class = dispatcher[cmd]
    command_handler = command_class(args)
    command_handler()

def main():
    setup_logging()
    args = parse_args()
    dispatch(args)

if __name__ == '__main__':
    main()
    
