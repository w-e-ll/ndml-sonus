#!/bin/env python

import argparse
import csv
import os
import shutil
import zipfile

from datetime import datetime

from ndml_sonus.lib.ndml_utils_tgw import Config
from ndml_sonus.scripts.common_exceptions import *


class Parser:
    """
    PSX Parser for a given list of csv reports.
    Updates every line by adding two new columns.
    Contains some common used functions.
    Saves output to csv files in csv folder.
    Cleans input csv folder.
    """
    def __init__(self, conf):
        self.conf = conf
        self.system_datetime = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        self._unzip_and_remove(self.conf.zip_dir, self.conf.archive_file_name)
        for name, ext, path in self._get_files(self.conf.zip_dir):
            output_file = self._make_output_file(name, ext)
            record_obj = self._read_file(path, name)
            self._write_to_file(name, output_file, record_obj)
        self._clean_input_csv_folder(self.conf.zip_dir)

    def _unzip_and_remove(self, zip_dir, archive_name):
        archive = None
        try:
            for file in os.listdir(zip_dir):
                if archive_name and '.zip' in file:
                    archive = os.path.join(zip_dir, file)
                    self.conf.log.info('Unzipping file %s' % file)
                    with zipfile.ZipFile(archive, 'r') as zip_ref:
                        zip_ref.extractall(self.conf.zip_dir)

                self.conf.log.info('Unzipped file %s' % file)
                os.remove(archive)
                self.conf.log.info('Removed zip file %s' % archive)
                break
        except Exception as exc:
            msg = '%s: Error: %s' % (archive, exc)
            self.conf.log.error(msg)

    def _get_files(self, path):
        """Get report files from zip folder"""
        self.conf.log.info('Getting list of report files with name, ext and path')
        for file in os.listdir(path):
            name, ext = os.path.splitext(file)
            if name in self.conf.file_names.split(","):
                if os.path.isfile(os.path.join(path, file)):
                    file_and_path = os.path.join(path, file)
                    yield name, ext, file_and_path
            else:
                continue

    def _make_output_file(self, file_name, extension):
        """creates output file with path and name"""
        file_name = self.conf.switch_name + '_' + file_name + extension
        return os.path.join(self.conf.csv_dir, file_name)

    def _read_file(self, file_path, file_name):
        """Reading a file line by line without loading all object in memory"""
        try:
            return (line for line in open(file_path))
        except IOError as e:
            msg = '%s/%s: I/O error: %s' % (self.conf.switch_name, file_name, e)
            self.conf.log.error(msg)
            raise ParseException(msg)

    def _write_to_file(self, file_name, out_file_path, records):
        """Parsing a report and exporting report records"""
        try:
            with open(out_file_path, 'w') as file_obj:
                writer = csv.writer(file_obj, delimiter=';')
                header = next(records)
                header = (self.conf.columns_to_add + header.replace("\n", "")).split(',')
                writer.writerow(header)

                exp_line_count = 1
                for rec in records:
                    clean_rec = "".join(rec.split())
                    record = ";".join(
                        [self.system_datetime, self.conf.node_name, clean_rec.replace(",", ";")]
                    ).split(";")
                    exp_line_count += 1
                    writer.writerow(record)

            self.conf.log.info('%s/%s: exported %d lines' % (self.conf.switch_name, file_name, exp_line_count))

        except IOError as e:
            # Cleanup
            os.unlink(file_name)
            msg = '%s/%s: I/O error: %s' % (self.conf.switch_name, file_name, e)
            self.conf.log.error(msg)
            raise ExportException(msg)

        except ParseException as e:
            os.unlink(file_name)
            msg = '%s/%s: I/O error: %s' % (self.conf.switch_name, file_name, e)
            self.conf.log.error(msg)
            raise

    def _clean_input_csv_folder(self, path):
        """Cleans input csv folder and makes new one"""
        shutil.rmtree(path)
        os.mkdir(path)
        self.conf.log.info("Input csv folder was cleaned.", path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True, help='config file for the script')
    args = parser.parse_args()

    conf = Config(args.config, 'parser')

    conf.log.info('Report parsing starting')
    Parser(conf)
    conf.log.info('All done')


if __name__ == '__main__':
    main()

