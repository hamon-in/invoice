import argparse

import model

def parse_args():
    parser = argparse.ArgumentParser(description = "Manage invoices")
    parser.add_argument("-f", "--file" , help = "Name of database file", required = True)
    subparsers = parser.add_subparsers(title="Commands", dest="command", help = "Commands available")
    subparsers.required = True

    init_parser = subparsers.add_parser("init", help="Initialise invoice database")

    args = parser.parse_args()
    return args

def run_init(args):
    """
    Handler for init command
    """
    model.create_database(args.file)

def dispatch(args):
    cmd = args.command if hasattr(args, "command") else ""
    dispatcher = {"init" : run_init}[cmd](args)

def main():
    args = parse_args()
    dispatch(args)

if __name__ == '__main__':
    main()
    
