from collections import OrderedDict

from . import PDFFormatter

def get_formatters():
    return OrderedDict([('pdf',  PDFFormatter)])

