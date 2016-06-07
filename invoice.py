import argparse

import model
import commands

def parse_args():
    parser = argparse.ArgumentParser(description = "Manage invoices")
    parser.add_argument("-f", "--file" , dest = "db", help = "Name of database file", default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(title="Commands", dest="command", help = "Commands available")
    subparsers.required = True

    init_parser = subparsers.add_parser("init", help="Initialise invoice database")

    company_parser = subparsers.add_parser("company", help="Manage companies")
    company_parser.add_argument("-v", "--verbose", help="Display verbose output")
    company_ops = company_parser.add_mutually_exclusive_group()

    company_ops.add_argument("-a", "--add", help="Add a new company")
    company_ops.add_argument("-l", "--list", help="List companies")
    company_ops.add_argument("-r", "--rm", help="Delete a company")

    args = parser.parse_args()
    return args


def dispatch(args):
    cmd = args.command if hasattr(args, "command") else ""
    dispatcher = commands.get_commands()
    command_class = dispatcher[cmd]
    command_handler = command_class(args)

def main():
    args = parse_args()
    dispatch(args)

if __name__ == '__main__':
    main()
    
