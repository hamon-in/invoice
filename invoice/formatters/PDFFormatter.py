import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
styles = getSampleStyleSheet()

from .common import Formatter

class PDFFormatter(Formatter):
    def create_invoice_layer(self, invoice_data):
        packet = io.BytesIO()
        # create a new PDF with Reportlab
        doc = SimpleDocTemplate(packet)
        Story = [Spacer(1,2*inch)]
        style = styles["BodyText"]
        
        client_address = invoice_data['client_address'].encode('utf-8').decode('unicode_escape')
        client_address = client_address.replace('\n', '<br/>')
        text = "<b><i>Bill to:</i></b><br/>{}".format(client_address)
        p = Paragraph(text, style)
        Story.append(p)
        Story.append(Spacer(1,0.2*inch))
        doc.build(Story)

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

