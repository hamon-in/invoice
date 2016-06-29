import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

from .common import Formatter

# PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]

styles = getSampleStyleSheet()
BodyStyle = styles["BodyText"]
BodyStyle.fontName = "Times-Roman"


class PDFFormatter(Formatter):
    def create_invoice_layer(self, invoice_data):
        client_address = invoice_data['client_address'].encode('utf-8').decode('unicode_escape')
        client_address = client_address.replace('\n', '<br/>')
        date = invoice_data['date']
        number = invoice_data['number']

        packet = io.BytesIO()
        # create a new PDF with Reportlab
        doc = SimpleDocTemplate(packet)
        content = [Spacer(1,2*inch)]

        content.append(Paragraph("<b>Date:</b> {}".format(date), BodyStyle))
        content.append(Paragraph("<b>Number:</b> {}".format(number), BodyStyle))
        doc.build(content)

        text = "<b><i>Bill to:</i></b><br/>{}".format(client_address)
        content.append(Paragraph(text, BodyStyle))
        content.append(Spacer(1,0.2*inch))


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
        outputStream = open("output.pdf", "wb")
        output.write(outputStream)
        outputStream.close()

