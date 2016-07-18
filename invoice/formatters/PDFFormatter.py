from decimal import Decimal
import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.platypus.tables import TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

from .common import Formatter

# PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]



class PDFFormatter(Formatter):
    def __init__(self):
        self.styles = dict(name = ParagraphStyle("name", fontName = "Times-Roman", leading = 36,
                                                 fontSize = 30, alignment = TA_CENTER),

                           address = ParagraphStyle("address", fontName = "Times-Italic", leading = 9.6,
                                                    fontSize = 8, alignment = TA_CENTER),

                           to_address = ParagraphStyle("to_address", fontName = "Times-Italic", leading = 12,
                                                       fontSize = 10, alignment = TA_LEFT),

                           table_header = ParagraphStyle("table_header", fontName = "Times-Roman", leading = 12,
                                                         fontSize = 10, alignment = TA_CENTER),

                           table_small = ParagraphStyle("table_header", fontName = "Times-Roman", leading = 12,
                                                         fontSize = 8, alignment = TA_CENTER),

                           regular = ParagraphStyle("to_address", fontName = "Times-Roman", leading = 12,
                                                    fontSize = 10, alignment = TA_RIGHT)
          )
        super().__init__()

    def create_invoice_layer(self, invoice_data):
        client_address = invoice_data['client_address'].encode('utf-8').decode('unicode_escape')
        bank_details = invoice_data['bank_details'].encode('utf-8').decode('unicode_escape')
        date = invoice_data['date']
        number = invoice_data['number']
        particulars = invoice_data['particulars']
        data_columns = invoice_data['columns']
        footers = invoice_data['footers']
        taxes = invoice_data['taxes']

        # create a new PDF with Reportlab
        packet = io.BytesIO()
        doc = SimpleDocTemplate(packet)

        # Create top material with number and client address
        content = [Spacer(1, 2*inch)]
        content.append(Paragraph("<b>Date: </b>{}".format(date), self.styles['to_address']))
        content.append(Spacer(1, 0.25*inch))
        content.append(Paragraph("<b>Invoice Number: </b>{}".format(number), self.styles['to_address']))
        content.append(Spacer(1, 0.25*inch))
        content.append(Paragraph("<b>Bill to:</b>", self.styles['to_address']))
        for i in client_address.split("\n"):
            content.append(Paragraph(i, self.styles['to_address']))
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("<b>Subject: </b>{}".format(particulars), self.styles['to_address']))


        # Now the table headers
        headers = invoice_data['fields']
        columns = [[Paragraph("<b>%s</b>"%x, self.styles['regular']) for x in headers]]

        list_style = TableStyle(
            [('LINEABOVE', (0,0), (-1,0), 1, colors.black),
             ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
             ('BACKGROUND',(0,0), (-1,0), colors.grey),
             ('BACKGROUND' ,(-1,1), (-1,-1), colors.lightgrey),
             ('ALIGN' ,(-1,1), (-1,-1), 'RIGHT'),
             ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
             ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
             ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
         ])

        total = Decimal(0)
        content.append(Spacer(1, 0.1*inch))
        for i in data_columns:
            if i[-1]:
                total += Decimal(i[-1])
            columns.append(Paragraph(str(t), self.styles['regular']) for t in i)

        extra_vals = dict(net_total = total)
        for t,v in taxes.items():
            n = total*Decimal(v)
            extra_vals[t] = n.quantize(Decimal('0.01'))

        extra_vals['gross_total'] = sum(extra_vals.values())

        for i in footers:
            c1 =[] 
            for j in i:
                j = j.format(**extra_vals)
                if j.startswith("b:"):
                    c1.append(Paragraph("<b>{}</b>".format(j.replace("b:","")), self.styles['regular']))
                else:
                    c1.append(Paragraph(str(j), self.styles['regular']))
            columns.append(c1)

        content.append(Table(columns, style = list_style))

        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("<b>Payment details:</b>", self.styles['to_address']))
        for i in bank_details.split("\n"):
            content.append(Paragraph(i, self.styles['to_address']))


        doc.build(content)
        return packet

    def add_to_letterhead(self, data, letterhead):
        #move to the beginning of the StringIO buffer
        new_pdf = PdfFileReader(data)
        # read your existing PDF
        
        existing_pdf = PdfFileReader(io.BytesIO(letterhead))
        output = PdfFileWriter()
        # add the "watermark" (which is the new pdf) on the existing page
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
        return output

    def create_timesheet_layer(self, timesheet_data):
        data = timesheet_data['data']
        client = timesheet_data['client']
        date = timesheet_data['date']
        employee = timesheet_data['emp']
        description = timesheet_data['desc']
        
        packet = io.BytesIO()
        doc = SimpleDocTemplate(packet)

        # Create top material with number and client address
        content = [Spacer(1, 1.25*inch)]

        content.append(Paragraph("<b>Date: </b>{}".format(date), self.styles['to_address']))
        content.append(Spacer(1, 0.25*inch))
        content.append(Paragraph("<b>Description: </b>{}".format(description), self.styles['to_address']))
        content.append(Spacer(1, 0.25*inch))

        columns = [[Paragraph("<b>%s</b>"%x, self.styles['table_header']) for x in ["Date","Hours"]]]
        list_style = TableStyle(
            [('LINEABOVE', (0,0), (-1,0), 1, colors.black),
             ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
             ('BACKGROUND',(0,0), (-1,0), colors.grey),

             # ('ALIGN' ,(-1,1), (-1,-1), 'RIGHT'),
             ('ALIGN' ,(0,0), (-1,0), 'CENTER'),

             ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
             ('BACKGROUND' ,(0,-1), (-1,-1), colors.lightgrey),
             ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
             ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
         ])

        total = sum((Decimal(x[1]) for x in data), Decimal(0)).quantize(Decimal('0.01'))
        
        for date, hours in data:
            columns.append([Paragraph(str(date), self.styles['table_small']),
                            Paragraph(str(Decimal(hours).quantize(Decimal('0.01'))), self.styles['table_small'])])
        columns.append([Paragraph("<b>Total hours</b>", self.styles['table_small']), 
                        Paragraph(str(total), self.styles['table_small'])])

        content.append(Table(columns, colWidths=120, style = list_style, hAlign='LEFT'))



        doc.build(content)
        return packet

        

    def generate_timesheet(self, timesheet):
        timesheet_layer = self.create_timesheet_layer(timesheet.serialise())
        final_timesheet = self.add_to_letterhead(timesheet_layer, timesheet.template.letterhead)

        outputStream = open(timesheet.file_name+".pdf", "wb")
        final_timesheet.write(outputStream)
        outputStream.close()
        


    def generate_invoice(self, invoice):
        invoice_layer = self.create_invoice_layer(invoice.serialise())
        final_invoice = self.add_to_letterhead(invoice_layer, invoice.template.letterhead)

        outputStream = open(invoice.file_name+".pdf", "wb")
        final_invoice.write(outputStream)
        outputStream.close()

