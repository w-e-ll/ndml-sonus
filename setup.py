import os

from glob import glob
from setuptools import setup, find_packages

from ndml_sonus import VERSION

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ndml-sonus',
    description="Ndml-sonus development",
    version=VERSION,
    long_description=README,
    author='Valentin Sheboldaev',
    classifiers=[
        'Development Status :: 5 - Production',
        'Environment :: Console',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.10.4'
    ],
    packages=find_packages(),
    data_files=[
        ('', glob('*.py')),
        ('', glob('*.txt')),
    ],
    include_package_data=True,
    platforms=['Any'],
    zip_safe=False,
    install_requires=[
        'cx-Oracle == 8.3.0',
        'ecdsa == 0.18.0',
        'paramiko == 2.11.0',
        'pycryptodome == 3.15.0',
        'pyyaml == 6.0'
    ],
    entry_points={
        'console_scripts': [
            'getdata_sonus_ssh_VM.py=ndml_sonus.scripts.getdata_sonus_ssh_VM:main',
            'parser_sonus.py=ndml_sonus.scripts.parser_sonus:main',
            'psx_archive_parser.py=ndml_sonus.scripts.psx_archive_parser:main'
        ],

    }
)


