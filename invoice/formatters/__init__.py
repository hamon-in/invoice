from collections import OrderedDict

from .PDFFormatter import PDFFormatter
from .TextFormatter import TextFormatter

def get_formatters():
    return OrderedDict([('pdf',  PDFFormatter),
                        ('txt',  TextFormatter)])

