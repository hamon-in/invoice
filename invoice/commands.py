import datetime
from collections import ChainMap, defaultdict
from decimal import Decimal
import json
import logging
import os
import re

import yaml
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from . import model
from . import helpers
from . import formatters
from . import __version__


class Command:
    def __init__(self, args, db_init = True):
        defaults = dict(output="generated", chronological=False, format="txt", overwrite=False)
        envars_config = {k.replace("INVOICE_", "").lower():v 
                         for k,v in os.environ.items() 
                         if k.startswith("INVOICE_")}
        
        self.args = ChainMap(args.__dict__, envars_config, defaults)
        self.l = logging.getLogger("invoice")
        self.l.debug("Options : %s", self.args)
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
        try:
            c = model.Config(name = "version", value = __version__, system = True)
            sess.add(c)
            sess.commit()
        except IntegrityError:
            self.l.debug("Reinitialising database. Not changing version")

class SummaryCommand(Command):
    def __init__(self, args):
        super().__init__(args)
    
    def serialise_db(self, sess):
        ret = {}
        config = sess.query(model.Config).all()
        ret['config'] = [{"name" : i.name, "value" : i.value, "system" : i.system} for i in config]

        accounts = sess.query(model.Account).all()
        ret['accounts'] = [dict(id = i.id,
                                name = i.name,
                                address = i.address,
                                phone = i.phone,
                                email = i.email,
                                pan = i.pan,
                                serv_tax_num = i.serv_tax_num,
                                bank_details = i.bank_details,
                                prefix = i.prefix) for i in accounts]

        print (json.dumps(ret))

    def human_summary(self, sess):
        chronological = self.args['chronological']
        verbose = self.args['verbose']
        self.l.info("Config:")
        for i in sess.query(model.Config).all():
            system = "*" if i.system else ''
            self.l.info("%s %10s:%10s", system, i.name, i.value)
        self.l.info("-"*70)
        
        for account in sess.query(model.Account).all():
            self.l.info("Account: %s", account.name)
            if verbose:
                self.l.info(account.summary(2))
            for client in account.clients:
                invoices = sess.query(model.Invoice).filter(model.Invoice.client == client)
                timesheets = sess.query(model.Timesheet).filter(model.Timesheet.client == client)
                if chronological:
                    invoices = invoices.order_by(model.Invoice.date)
                    timesheets = timesheets.order_by(model.Timesheet.date)
                self.l.info("    Client: %s", client.name)
                if verbose:
                    self.l.info("      Address  : %s", helpers.wrap(client.address, 17))
                    self.l.info("      Billed in: %s\n", client.bill_unit)
                self.l.info("      Invoices:")
                for invoice in invoices:
                    if verbose:
                        self.l.info(invoice.summary(10)+"\n")
                    else:
                        self.l.info("       %s | %s | %s", invoice.id, invoice.date.strftime("%d %b %Y") , invoice.particulars)
                self.l.info("      Timesheets:")
                for timesheet in timesheets:
                    if verbose:
                        self.l.info(timesheet.summary(10)+"\n")
                    else:
                        self.l.info("       %s | %s | %s", timesheet.id, timesheet.date.strftime("%d %b %Y") , timesheet.description)
        self.l.info("-"*70)


        self.l.info("Invoice templates:")
        for template in sess.query(model.InvoiceTemplate).all():
            self.l.info(" %20s | %s ", template.name, template.description)
        self.l.info("-"*70)


    def __call__(self):
        sess = model.get_session(self.args['db'])
        if self.args['dump']:
            self.serialise_db(sess)
        else:
            self.human_summary(sess)

            
            
class TemplateCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {"add"  : self.add,
                            "edit" : self.edit,
                            "rm"   : self.rm,
                            "ls"   : self.list_}

    def list_(self):
        sess = model.get_session(self.args['db'])
        self.l.info("Templates :")
        for template in sess.query(model.InvoiceTemplate).all():
            self.l.info("%20s | %s ", template.name, template.description)

            


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
   service: 0.14
   kk_cess: 0.05
   sb_cess: 0.05


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
        if 'letterhead' in self.args:
            with open(self.args['letterhead'], "rb") as f:
                letterhead = f.read()
                template.letterhead = letterhead
                self.l.debug("Updated letterhead")
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
                            'ls' : self.list,
                            'edit' : self.edit}

    def edit(self):
        name = self.args["name"]
        address = self.args["address"]
        signatory = self.args['signatory']
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
        if signatory:
            account.signatory = signatory
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
                                signatory = self.args['signatory'],
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
        self.sc_handlers = {'add'  : self.add,
                            'ls' : self.list,
                            'edit' : self.edit,
        }

    def edit(self):
        sess = model.get_session(self.args['db'])
        account = self.args["account"]
        client = self.args['name']
        billing_unit = self.args["bunit"]
        address = self.args["address"]

        try:
            client = sess.query(model.Client).filter(model.Client.name == client).one()
        except NoResultFound:
            self.l.critical("No such client '%s'", client)
            raise

        if account:
            try:
                account = sess.query(model.Account).filter(model.Account.name == account).one()
                client.account = account
            except NoResultFound:
                self.l.critical("No such account '%s'", account)
                raise
        
        if billing_unit:
            client.bill_unit = billing_unit

        if address:
            client.address = address

        sess.add(client)
        sess.commit()

        


    def add(self):
        sess = model.get_session(self.args['db'])
        try:
            account = sess.query(model.Account).filter(model.Account.name == self.args['account']).one()
        except NoResultFound:
            self.l.critical("No such account '%s'", self.args['account'])
            raise

        client = model.Client(name = self.args['name'],
                              address = self.args['address'],
                              bill_unit = self.args['bunit'],
                              account = account)


        sess.add(client)
        sess.commit()

    
    def list(self):
        sess = model.get_session(self.args['db'])
        self.l.info("Clients")
        for i in sess.query(model.Client).all():
            self.l.info(" %s | %s ", i.name, i.account.name)


class InvoiceCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add,
                            'generate' : self.generate,
                            'edit' : self.edit,
                            'show' : self.show,
                            "rm" : self.rm, 
                            "ls" : self.list}
    
    def show(self):
        sess = model.get_session(self.args['db'])
        inv_id = int(self.args['id'])
        invoice = sess.query(model.Invoice).filter(model.Invoice.id == inv_id).one()
        text_formatter = self.formatters['txt']()
        generated_invoice = text_formatter.generate_invoice(invoice, True, False)
        print("\n{}\n".format(generated_invoice))

        
    def list(self):
        sess = model.get_session(self.args['db'])
        tags = self.args['tag']
        # tags = sess.query(model.InvoiceTag).filter(or_(*[model.InvoiceTag.name == x for x in tags])).all()
        # print (tags)
        if tags:
            invoices = sess.query(model.Invoice).filter(model.Invoice.tags.any(model.InvoiceTag.name.in_(tags))).all()
        else:
            invoices = sess.query(model.Invoice).all()

        if invoices:
            for invoice in invoices:
                tags = ", ".join (x.name for x in invoice.tags)
                self.l.info("     %3s | %s | %5s | %30s | %s ", invoice.id, invoice.date.strftime("%d %b %Y"), invoice.client.name,  invoice.particulars[:30], tags)
        else:
            self.l.info("No invoices matching criteria")
        
    def add(self):
        self.l.debug("Adding invoice")
        sess = model.get_session(self.args['db'])
        date = datetime.datetime.strptime(self.args['date'], "%d/%b/%Y")
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

""".format(", ".join(fields), "|".join(["          "]*len(fields)))

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
        date_start = datetime.datetime.strptime(self.args['from'], "%d/%b/%Y")
        date_to = datetime.datetime.strptime(self.args['to'], "%d/%b/%Y")
        fmt_name = self.args['format']
        formatter = self.formatters[fmt_name](self.args['output'])
        client = self.args['client']
        overwrite = self.args['overwrite']
        id = self.args['id']

        query = sess.query(model.Invoice).join(model.Client)
        if id != -1:
            self.l.info("Generating invoice with id %s", id)
            invoices = query.filter(model.Invoice.id == id).all()
        else:
            self.l.info("Invoices between %s and %s", self.args['from'], self.args['to'])
            invoices = query.filter(date_start <= model.Invoice.date,
                                    model.Invoice.date <= date_to)
            if client:
                self.l.info("Limiting to client %s", client)
                invoices = invoices.filter(model.Client.name == client)
            invoices = invoices.all()
        if invoices:
            for invoice in invoices:
                fname = formatter.generate_invoice(invoice, False, overwrite)
                self.l.info("  Generated invoice %s", fname)
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
        sess = model.get_session(self.args['db'])
        id = self.args["id"]
        client = self.args["client"]
        template = self.args["template"]
        date = self.args["date"]
        particulars = self.args["particulars"]
        edit_content = self.args['edit']

        add_tag_names = self.args['add_tags']
        replace_tag_names = self.args['replace_tags']
        add_tags = replace_tags = None

        if add_tag_names:
            add_tags = sess.query(model.InvoiceTag).filter(or_(*[model.InvoiceTag.name == i for i in add_tag_names])).all()
            if len(add_tag_names) != len(add_tags):
                self.l.warn("Some of the tags are invalid. Skipping them.")

        if replace_tag_names:
            replace_tags = sess.query(model.InvoiceTag).filter(or_(*[model.InvoiceTag.name == i for i in replace_tag_names])).all()
            if len(replace_tag_names) != len(replace_tags):
                self.l.warn("Some of the tags are invalid. Skipping them.")
            
            
        try:
            invoice = sess.query(model.Invoice).filter(model.Invoice.id == id).one()
        except NoResultFound:
            self.l.critical("No invoice with id %s", id)
            raise

        if add_tags:
            invoice.tags.extend(add_tags)

        if replace_tags:
            invoice.tags = replace_tags

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
            invoice.date = datetime.datetime.strptime(date, "%d/%b/%Y")
        if particulars:
            invoice.particulars = particulars

        if edit_content:
            _, data = helpers.get_from_file(invoice.content)
            invoice.content = data

        sess.add(invoice)
        sess.commit()

        
class TagCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'add'  : self.add,
                            'rm' : self.rm,
                            "ls" : self.list}
                            # 'edit' : self.edit,
                            # "rm" : self.rm, 
                            # }

    def list(self):
        sess = model.get_session(self.args['db'])
        self.l.info("Tags:")
        for t in sess.query(model.InvoiceTag).all():
            self.l.info(" %s %s", t.name, "*" if t.system else '')

    def add(self):
        sess = model.get_session(self.args['db'])
        t = model.InvoiceTag(name = self.args['name'], system = False)
        sess.add(t)
        sess.commit()
        
    def rm(self):
        sess = model.get_session(self.args['db'])
        try:
            t = sess.query(model.InvoiceTag).filter(model.InvoiceTag.name == self.args['name']).one()
            if t.system:
                self.l.warn("Cannot delete system tag %s", self.args['db'])
            else:
                sess.delete(t)
                sess.commit()
        except NoResultFound:
            self.l.critical("No such tag '%s'", self.args['name'])
            raise

class TimesheetCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.sc_handlers = {'import'   : self.import_,
                            'ls'       : self.ls,
                            'add'      : self.add,
                            'generate' : self.generate,
                            'show'     : self.show,
                            'edit'     : self.edit,
                            'rm'       : self.rm,
                            'parse'    : self.parse}

    def show(self):
        sess = model.get_session(self.args['db'])
        ts_id = int(self.args['id'])
        timesheet = sess.query(model.Timesheet).filter(model.Timesheet.id == ts_id).one()
        text_formatter = self.formatters['txt']()
        generated_timesheet = text_formatter.generate_timesheet(timesheet, True, False)
        print("\n{}\n".format(generated_timesheet))

    
    def parse(self):
        with open(self.args['timesheet']) as f:
            timesheet = json.loads(self.parse_timesheet(f))
            self.l.info("\nParsed timesheet:")
            data = sorted(timesheet.items(), key=lambda x: datetime.datetime.strptime(x[0], '%d/%m/%Y %a'))
            total = Decimal(0.0)
            for k,v in data:
                value = Decimal(v)
                total += value
                self.l.info("%15s | %+6s ", k, value.quantize(Decimal('0.01')))

            self.l.info("----------------+-------")
            self.l.info("%15s | %+6s\n", "Total", total.quantize(Decimal('0.01')))
        

    def ls(self):
        sess = model.get_session(self.args['db'])
        timesheets = sess.query(model.Timesheet)
        if self.args['chronological']:
            timesheets = timesheets.order_by(model.Timesheet.date)
        
        self.l.info("Timesheets:")
        for timesheet in timesheets.all():
            self.l.info("  %4s | %8s | %10s | %s | %s ", 
                        timesheet.id, 
                        timesheet.client.name, 
                        timesheet.employee, 
                        timesheet.date.strftime("%d/%b/%Y"),
                        timesheet.description)

    def rm(self):
        ts_id = self.args["id"]
        sess = model.get_session(self.args['db'])

        try:
            timesheet = sess.query(model.Timesheet).filter(model.Timesheet.id == int(ts_id)).one()
        except NoResultFound:
            self.l.critical("No such timesheet '%s'", ts_id)
            raise
        sess.delete(timesheet)
        sess.commit()

        
    def edit(self):
        ts_id = self.args["id"]
        date = self.args['date']
        employee = self.args['employee']
        client = self.args['client']
        desc = self.args['description']
        edit = self.args['edit']
        
        sess = model.get_session(self.args['db'])
        try:
            timesheet = sess.query(model.Timesheet).filter(model.Timesheet.id == int(ts_id)).one()
        except NoResultFound:
            self.l.critical("No such timesheet '%s'", ts_id)
            raise

        if date:
            timesheet.date = datetime.datetime.strptime(date, "%d/%b/%Y")
        if employee:
            timesheet.employee = employee
        if desc:
            timesheet.description = desc
        if client:
            try:
                client = sess.query(model.Client).filter(model.Client.name == client).one()
                timesheet.client = client
            except NoResultFound:
                self.l.critical("No such client '%s'", client)
                raise

        if edit:
            template = """# -*- text -*-
# Local Variables: 
# eval: (orgtbl-mode) 
# End:
#
{}
""".format(timesheet.to_table())
            _, template = helpers.get_from_file(template)
            timesheet.set_from_table(template)
            
        sess.add(timesheet)
        sess.commit()

    def parse_timesheet(self, data):
        ret = defaultdict(int)
        day_re = re.compile(r'\*\* [[<](\d+)-(\d+)-(\d+) [a-zA-Z]+')
        period_re = re.compile(r'.*CLOCK: \[(\d+)-(\d+)-(\d+) [a-zA-Z]+ (\d+):(\d+)\]--\[(\d+)-(\d+)-(\d+) [a-zA-Z]+ (\d+):(\d+)\] =>  \d+:\d+')
        for i in data:
            day = day_re.search(i)
            period_search = period_re.search(i)
            if day:
                y, m, dom = day.groups()
                cday = datetime.date(day=int(dom), month=int(m), year=int(y)).strftime('%d/%m/%Y %a')
            if period_search:
                y0, m0, d0, hh0, mm0, y1, m1, d1, hh1, mm1 = period_search.groups()
                t_start = datetime.datetime(year = int(y0), month = int(m0), day = int(d0), 
                                            hour = int(hh0), minute = int(mm0))
                t_end = datetime.datetime(year = int(y1), month = int(m1), day = int(d1), 
                                          hour = int(hh1), minute = int(mm1))
                duration = (t_end - t_start).total_seconds() / (60 * 60)
                ret[cday] += duration
        return json.dumps(ret)

    def generate(self):
        sess = model.get_session(self.args['db'])
        id = model.get_session(self.args['id'])
        date_start = datetime.datetime.strptime(self.args['from'], "%d/%b/%Y")
        date_to = datetime.datetime.strptime(self.args['to'], "%d/%b/%Y")
        fmt_name = self.args['format']
        formatter = self.formatters[fmt_name](self.args['output'])
        employee = self.args['employee']
        client = self.args['client']
        overwrite = self.args['overwrite']
        id = self.args['id']

        if id != -1:
            self.l.info("Generating timesheet with %s", id)
            j = sess.query(model.Timesheet).filter(model.Timesheet.id == id)
        else:
            self.l.info("Timesheets between %s and %s", self.args['from'], self.args['to'])
            j = sess.query(model.Timesheet).join(model.Client).filter(date_start <= model.Timesheet.date,
                                                                      model.Timesheet.date <= date_to)
            if client:
                self.l.info("Filtering by client %s", client)
                j = j.filter(model.Client.name == client)
            if employee:
                self.l.info("Filtering by employee %s", employee)
                j = j.filter(model.Timesheet.employee == employee)

        timesheets = j.all()
        if timesheets:
            for timesheet in timesheets:
                fname = formatter.generate_timesheet(timesheet, False, overwrite)
                self.l.info("  Generated timesheet %s", fname)

        else:
            self.l.critical("No timesheet found matching these criteria")

    def add(self):
        sess = model.get_session(self.args['db'])
        date = datetime.datetime.strptime(self.args['date'], "%d/%b/%Y")
        employee = self.args['employee']
        client = self.args['client']
        template = self.args['template']
        desc = self.args['description']

        try:
            client = sess.query(model.Client).filter(model.Client.name == client).one()
        except NoResultFound:
            self.l.critical("No such client '%s'", client)
            raise

        try:
            template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name == template).one()
        except NoResultFound:
            self.l.critical("No such template '%s'", template)
            raise

        timesheet = model.Timesheet(date = date,
                                    employee = employee,
                                    template = template,
                                    description = desc,
                                    client = client)
        
        template = """# -*- text -*-
# Local Variables: 
# eval: (orgtbl-mode) 
# End:
#
|   |   |
"""
        _, template = helpers.get_from_file(template)
        timesheet.set_from_table(template)
            
        sess.add(timesheet)
        sess.commit()


    def import_(self):
        sess = model.get_session(self.args['db'])

        date = datetime.datetime.strptime(self.args['date'], "%d/%b/%Y")
        description = self.args['description']
        employee = self.args['employee']
        template = self.args['template']
        try:
            template = sess.query(model.InvoiceTemplate).filter(model.InvoiceTemplate.name == template).one()
        except NoResultFound:
            self.l.critical("No such template '%s'", template)
            raise

        try:
            client = sess.query(model.Client).filter(model.Client.name == self.args['client']).one()
        except NoResultFound:
            self.l.critical("No such client '%s'", client)
            raise

        with open(self.args['timesheet']) as f:
            timesheet = self.parse_timesheet(f)

        t = model.Timesheet(employee = employee,
                            template = template,
                            description = description,
                            client = client,
                            date = date,
                            data = timesheet)
        sess.add(t)
        sess.commit()



def get_commands():
    return {"init"     : InitCommand,
            "account"  : AccountCommand,
            "client"   : ClientCommand,
            "template" : TemplateCommand,
            "summary"  : SummaryCommand,
            "invoice"  : InvoiceCommand,
            "tag"      : TagCommand,
            "timesheet": TimesheetCommand}
