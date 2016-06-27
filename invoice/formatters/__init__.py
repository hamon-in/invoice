from collections import OrderedDict

from .PDFFormatter import PDFFormatter

def get_formatters():
    return OrderedDict([('pdf',  PDFFormatter)])

