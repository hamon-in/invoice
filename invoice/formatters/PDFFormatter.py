import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .common import Formatter

class PDFFormatter(Formatter):
    def create_invoice_layer(self, invoice_data):
        packet = io.BytesIO()
        # create a new PDF with Reportlab
        can = canvas.Canvas(packet, pagesize=letter)
        can.drawString(100, 300, "Goodbye world")
        can.save()
        packet.seek(0)
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

