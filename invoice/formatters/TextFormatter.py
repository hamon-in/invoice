from decimal import Decimal
import io

from .common import Formatter

# PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]


class TextFormatter(Formatter):
    stdout_output = True

    def __init__(self, dir="generated"):
        super().__init__(dir)

    def create_invoice_layer(self, invoice_data):
        client_address = invoice_data['client_address'].encode('utf-8').decode('unicode_escape')
        bank_details = invoice_data['bank_details'].encode('utf-8').decode('unicode_escape')
        date = invoice_data['date']
        number = invoice_data['number']
        particulars = invoice_data['particulars']
        data_columns = invoice_data['columns']
        footers = invoice_data['footers']
        taxes = invoice_data['taxes']
        bill_unit = invoice_data['bill_unit']

        content = ["="*80]
        content.append("Date: {}\n".format(date))
        content.append("Invoice Number: {}\n".format(number))
        content.append("Bill to:")
        for i in client_address.split("\n"):
            content.append(" {}".format(i))
        content.append("")
        content.append("Subject: {}".format(particulars))
        content.append("")
        headers = invoice_data['fields']

        # Compute column widths
        widths = [0] * len(headers)
        for idx,i in enumerate(headers):
            widths[idx] = len(i)
        for i in data_columns:
            for idx,col in enumerate(i):
                fw = len(str(col))
                if widths[idx] < fw:
                    widths[idx] = fw
        for i in footers:
            for idx,col in enumerate(i):
                fw = len(str(col))
                if widths[idx] < fw:
                    widths[idx] = fw
                    
        format_widths_center =  ["{{:^{}}}".format(x) for x in widths]
        format_widths =  ["{{:>{}}}".format(x) for x in widths]

        data_fmt_string = " | ".join(format_widths)
        header_fmt_string = " | ".join(format_widths_center)
        sep_fmt_string = "-+-".join("-"*x for x in widths)+"-"

        # Now start generating
        content.append(sep_fmt_string)
        content.append(header_fmt_string.format(*headers))
        content.append(sep_fmt_string)

        total = Decimal(0)
        for i in data_columns:
            if i[-1]:
                total += Decimal(i[-1])
                i[-1] = "{} {}".format(i[-1], bill_unit)
            content.append(data_fmt_string.format(*[str(t).strip() for t in i]))
        content.append(sep_fmt_string)

        extra_vals = dict(net_total = total)
        for t,v in taxes.items():
            n = total*Decimal(v)
            extra_vals[t] = n.quantize(Decimal('0.01'))
        extra_vals['gross_total'] = sum(extra_vals.values())

        for i in footers:
            c1 = []
            i[-1] = "{} {}".format(i[-1], bill_unit)
            for j in i:
                if j.startswith("b:"):
                    j = j.replace("b:", "")
                j = j.format(**extra_vals)
                c1.append(j)
            content.append(data_fmt_string.format(*c1))
        content.append(sep_fmt_string)
        content.append("")
        content.append("Payment details:")
        for i in bank_details.split("\n"):
            content.append(" {}".format(i))

        content.append("="*80)
        return "\n".join(content)


    def create_timesheet_layer(self, timesheet_data):
        data = timesheet_data['data']
        client = timesheet_data['client']
        date = timesheet_data['date']
        employee = timesheet_data['emp']
        description = timesheet_data['desc']
        
        # Create top material with number and client address

        content = ["="*80]
        content.append("Date: {}".format(date))
        content.append("")
        content.append("Description: {}".format(description))
        content.append("")

        widths = [10, 15, 10]
        format_widths =  ["{{:^{}}}".format(x) for x in widths]
        fmt_string = " | ".join(format_widths)

        content.append(fmt_string.format("Day", "Date", "Hours"))
        sep_fmt_string = "-+-".join("-"*x for x in widths)+"-"
        content.append(sep_fmt_string)

        total = sum((Decimal(x[1]) for x in data), Decimal(0)).quantize(Decimal('0.01'))
        
        for date, hours in data:
            c = ([date.strftime('%a'), date.strftime('%d %b %Y'), str(Decimal(hours).quantize(Decimal('0.01')))])
            content.append(fmt_string.format(*c))
        content.append(sep_fmt_string)

        content.append(fmt_string.format(*['', "Total hours", str(total)]))

        # content.append(Table(columns, colWidths=[50, 150, 50], style = list_style, hAlign='LEFT'))
        # doc.build(content)
        # return packet
        content.append("")
        content.append("="*80)
        return "\n".join(content)

    def generate_timesheet(self, timesheet, stdout = False, overwrite = False):
        timesheet_data = self.create_timesheet_layer(timesheet.serialise())
        if stdout:
            print ("")
            print (timesheet_data)
            print ("")
            fname = 'on stdout'
        else:
            fname = self.gen_unique_filename(timesheet.file_name+".txt", overwrite)
            with open(fname, "w") as f:
                f.write(timesheet_data)
        return fname
        


    def generate_invoice(self, invoice, stdout=False, overwrite = False):
        invoice_data = self.create_invoice_layer(invoice.serialise())
        if stdout:
            print ("")
            print (invoice_data)
            print ("")
            fname = 'on stdout'
        else:
            fname = self.gen_unique_filename(invoice.file_name+".txt", overwrite)
            with open(fname, "w") as f:
                f.write(invoice_data)
        return fname

