import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

                           regular = ParagraphStyle("to_address", fontName = "Times-Roman", leading = 12,
                                                    fontSize = 10, alignment = TA_LEFT)
          )
        super().__init__()

    def create_invoice_layer(self, invoice_data):
        client_address = invoice_data['client_address'].encode('utf-8').decode('unicode_escape')

        date = invoice_data['date']
        number = invoice_data['number']

        # create a new PDF with Reportlab
        packet = io.BytesIO()
        doc = SimpleDocTemplate(packet)

        # Create top material with number and client address
        content = [Spacer(1, 2*inch)]
        content.append(Paragraph("<b>Invoice Number: </b>{}".format(number), self.styles['to_address']))
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("<b>Bill to:</b>", self.styles['to_address']))
        for i in client_address.split("\n"):
            content.append(Paragraph(i, self.styles['to_address']))

        # Now the table headers
        headers = invoice_data['fields']
        columns = [[Paragraph("<b>%s</b>"%x, self.styles['regular']) for x in headers]]

        list_style = TableStyle(
            [('LINEABOVE', (0,0), (-1,0), 1, colors.black),
             ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
             ('BACKGROUND',(0,0), (-1,0), colors.grey),
             ('BACKGROUND' ,(-1,1), (-1,-1), colors.lightgrey),
             ('ALIGN' ,(-1,1), (-1,-1), 'LEFT'),
             ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
             ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
             ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
         ])

        content.append(Spacer(1, 0.5*inch))
        content.append(Table(columns, style = list_style))

        doc.build(content)
        return packet

    def generate(self, invoice):
        invoice_layer = self.create_invoice_layer(invoice.serialise())

        #move to the beginning of the StringIO buffer
        new_pdf = PdfFileReader(invoice_layer)
        # read your existing PDF
        
        existing_pdf = PdfFileReader(io.BytesIO(invoice.template.letterhead))
        output = PdfFileWriter()
        # add the "watermark" (which is the new pdf) on the existing page
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
        # finally, write "output" to a real file
        outputStream = open(invoice.file_name+".pdf", "wb")
        output.write(outputStream)
        outputStream.close()

