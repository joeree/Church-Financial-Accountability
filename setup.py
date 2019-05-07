"""
 Usage (Mac OS X):
     python setup.py py2app
"""

import sys
from setuptools import setup, find_packages

main_script = ['frontend.py']
VERSION = "0.0.5.2"

DATA_FILES = [
    ('resources', ['resources/currency_dict.json',
                   'resources/log.json',
                   'resources/settings_template.json']
     ),
    ('locales', ['locales/base.pot']),
    ('locales/en/LC_MESSAGES', ['locales/en/LC_MESSAGES/base.mo']),
    ('locales/ru/LC_MESSAGES', ['locales/ru/LC_MESSAGES/base.mo']),
    ('locales/uk/LC_MESSAGES', ['locales/uk/LC_MESSAGES/base.mo']),
    ]

MODULES = [
    'simplejson',
    'reportlab',
    ]


OPTIONS = {
    'iconfile': 'logo.icns',
    'argv_emulation': True,
    'packages': find_packages(),
    'plist': {
        'CFBundleName': 'Church Financial Accounting Program',
        'CFBundleDisplayName': 'CFAP',
        'CFBundleGetInfoStrring': "A financial accounting program.",
        'CFBundleIdentifier': "com.joesumi.osx.cfap",
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHumanReadableCopyright': u"Copyright © 2017-2019, Joseph Sumi, All Rights Reserved",
    },
}

DESC = """
Church Financial Accounting Program (CFAP) was created to give 
local churches and small NPOs a resource in keeping transparent and accountable
financial documents. It was developed from the need that current finance
software was either too costly and/or advanced and free software did 
not work with multiple languages or currencies and/or was not user friendly.
"""

setup(
    app=main_script,
    setup_requires=['py2app'],
    
    name='CFAP',  # Required
    version=VERSION,  # Required
    description='A financial accounting program.',  # Optional
    long_description=DESC,  # Optional
    long_description_content_type='text/markdown',  # Optional
    author='Joseph Sumi',  # Optional
    author_email='josephsumi@gmail.com',  # Optional

    install_requires=MODULES,
    options={'py2app': OPTIONS},
    py_modules=['backend', 'buildreports', 'calculator', 'mbox'],
    data_files=DATA_FILES,
    
    classifiers=[
        #  How mature is this project?
        #  3 - Alpha
        #  4 - Beta
        #  5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Public',
        'Topic  :: Accounting Software',
        'License :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        ],
    keywords='accounting software',  # Optional
    python_requires='>=3',
)
