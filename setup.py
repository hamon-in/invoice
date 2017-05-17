from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

import invoice

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()



setup(
    name='invoice',
    version=invoice.__version__,

    description = ("A command line tool to manage invoices for a small company."),
    long_description = long_description,

    author = "Hamon Technologies LLP",
    author_email = "noufal@hamon.in",

    license='MIT',

    packages=find_packages(),
    
    zip_safe = False,

    keywords = "finance invoice",
    url='https://github.com/hamon-in/invoice',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    entry_points = { 'console_scripts' : [
        'invoice = invoice.invoice:main'
    ]}

)

