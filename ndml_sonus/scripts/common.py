import os
import time
from datetime import datetime
import csv

from ndml_sonus.scripts.common_exceptions import *
from ndml_sonus.scripts.separators import *
from ndml_sonus.scripts.second_step import SecondStepParser
from ndml_sonus.scripts.field_merger import FieldMerger


class SonusParser:
class SonusParser:
    """
    Contains some common used functions
    """

    def __init__(self, conf, host, report):
        self.conf = conf
        self.switch = host
        self.report = report
        self.host = host

        # Context info to include in all logging messages
        self.context = '%s/%s' % (self.switch.name, self.report.name)

        self.report_filename = conf.raw_file_name(host, report)
        self.output_filename = conf.csv_file_name(host, report)
        self.tmp_output_filename = conf.tmp_file_name(host, report)

        self.row_header = report.fields_list

        self.report_fd = self._openReport()
        self._get_fileinfo()

    def _get_fileinfo(self):
        """
        get the switch name and last modification date out of the filename and also the tgwname
        """
        # check if there is a tgw part in the name ex: str21uxt_tgw1
        first_part = os.path.basename(self.report_filename).split('-')[0]
        switchname_part = first_part.split('_')
        if len(switchname_part) > 1:
            self.switchname = switchname_part[0].upper()
            self.tgwname = switchname_part[1].upper()
        else:
            self.switchname = switchname_part[0].upper()
        # check if there is a tgw part in the name ex: str21uxt_tgw1

        filedate = os.stat(self.report_filename)[8]
        self.reportdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(filedate))

    def _openReport(self):
        try:
            fd = open(self.report_filename, 'r')
            return fd
        except IOError as e:
            msg = '%s: I/O error: %s' % (self.context, e)
            self.conf.log.error(msg)
            raise ParseException(msg)

    def export(self):
        """
        Export data to a csv file
        """
        self.conf.log.info('%s: parsing and exporting ...' % self.context)
        try:
            out_file = open(self.tmp_output_filename, 'w')
            w = csv.writer(out_file, dialect='excel', delimiter=';', lineterminator='\n')

            # First output line is the list of row headers
            w.writerow(self.row_header)

            # Process all rows from the report and export them directly
            exp_line_count = 1
            for record in self.parse():
                exp_line_count += 1
                w.writerow(record)

            out_file.close()
            self.conf.log.info('%s: exported %d lines' % (self.context, exp_line_count))

        except IOError as e:
            # Cleanup
            out_file.close()
            os.unlink(self.tmp_output_filename)

            msg = '%s: I/O error: %s' % (self.context, e)
            self.conf.log.error(msg)
            raise ExportException(msg)

        except ParseException as e:
            # Cleanup
            out_file.close()
            os.unlink(self.tmp_output_filename)

            raise

    def parse(self):
        raise NotImplementedError()


class NoMatchException(ParseException):
    pass


class StatusNotOKException(ParseException):
    pass


class SonusLineParser(SonusParser):
    def parse(self):
        results = []
        for line in self.report_fd:
            results = self.parse_line(line)

            for result in results:
                yield result

    def parse_line(self, line):
        raise NotImplementedError()


class SonusFullTextParser(SonusParser):
    def parse(self):
        return self.parse_text(self.report_fd.read())

    def parse_text(self, text):
        raise NotImplementedError()


class AutoFieldsAdder:
    def __init__(self, report, host_name, log):
        self.host_name = host_name
        self.report = report
        ORACLE_DATE_FORMAT = '%Y/%m/%d %H:%M:%S'
        self.system_datetime = datetime.now().strftime(ORACLE_DATE_FORMAT)
        self.field_merger = FieldMerger()
        self.auto_remove = ['Empty']

    def add_auto_fields(self, result_dict):
        if self.report.auto_add_date:
            self.field_merger.merge({'Date': self.system_datetime}, result_dict)

        if self.report.auto_add_report_host:
            self.field_merger.merge({'Report Host': self.host_name}, result_dict)

        self.field_merger.merge({'Empty': ''}, result_dict)

    def remove_auto_fields(self, result_dict):
        for item_to_remove in self.auto_remove:
            result_dict.pop(item_to_remove)


class NonOptionalParameterNotFoundException(ParseException):
    pass


class CsvLineEmitter:
    def __init__(self, report, log, auto_field_adder):
        self.report = report
        self.fields_to_emit = report.fields_list
        self.optional_fields = report.optional_fields
        self.known_unused_fields = report.known_unused_fields
        self.log = log
        self.auto_field_adder = auto_field_adder

    def warn_about_unused_fields(self, params_dict):
        self.auto_field_adder.remove_auto_fields(params_dict)
        for key in params_dict:
            if key not in self.fields_to_emit:
                pass
                # self.log.info(
                #    'Field "%s" with value "%s" was unused, probably a new field in the report' % (
                #        key, params_dict[key]
                #    )
                #)

    def emit_line_from_dict(self, params_dict):

        csv_line = []
        non_optional_params_not_found = []

        for param in self.fields_to_emit:
            if param in params_dict:
                param_value = params_dict[param]
            else:
                param_value = ''
                if param in self.optional_fields:
                    self.log.debug(
                        'Param %s not found in params_dict %s. '
                        'Generating empty field in CSV because it is an optional param.' % (param, params_dict)
                    )
                else:
                    non_optional_params_not_found.append(param)

            csv_line.append(param_value)

        if len(non_optional_params_not_found) > 0:
            raise NonOptionalParameterNotFoundException(
                'Report %s : Non-optional params %s not found' % (self.report.name, non_optional_params_not_found)
            )
        else:
            self.warn_about_unused_fields(params_dict)
            return csv_line


# Move this regex to a GSXCommandFullTextParser class
class CommandFullTextParser(SonusFullTextParser):
    separator = FullTextRegexSeparator(
r'''
Node:\s*(?P<Node>\S+)\s*Date:\s*(?P<Date>\d+/\d+/\d+\s\d+:\d+:\d+)\s*\w+\s*
\s*Zone:\s*(?P<Zone>\S+)\n
(?P<CommandOutput>.*?)
%

Result:\s*(?P<Result>\S+)
'''
        )

    def __init__(self, conf, host, report):
        SonusFullTextParser.__init__(self, conf, host, report)
        self.auto_fields_adder = AutoFieldsAdder(self.report, self.host.name, self.conf.log)
        self.csv_line_emitter = CsvLineEmitter(report, conf.log, self.auto_fields_adder)
        self.second_step_parser = SecondStepParser.create_from_report(self.report)

    def parse_text(self, text):
        nodes_results_and_commands_outputs = list(self.separator.separate(text))
        for node_result_and_command_output in nodes_results_and_commands_outputs:
            if self.report.check_result:
                try:
                    result = node_result_and_command_output.pop('Result').upper()
                    if result not in ['OK', 'COMPLETED']:
                        raise StatusNotOKException()
                except KeyError:
                    raise StatusNotOKException()

            command_output_fields = self.parse_command_output(node_result_and_command_output.pop('CommandOutput'))
            for csv_line in command_output_fields:
                result_dict = node_result_and_command_output.copy()
                result_dict.update(csv_line)

                self.auto_fields_adder.add_auto_fields(result_dict)
                self.second_step_parser.parse_dict(self.report, result_dict)

                result_element = self.csv_line_emitter.emit_line_from_dict(result_dict)

                yield result_element

    def parse_command_output(self, text):
        raise NotImplementedError()


class NodeAndResultParser(SonusLineParser):
    def __init__(self, conf, host, report):
        SonusLineParser.__init__(self, conf, host, report)
        self.node_separator = RegexSeparator(r'Node:\s*(?P<Node>\w+)\s*Date:\s*(?P<Date>\d+/\d+/\d+\s*\d+:\d+:\d+)\s*\w+')
        self.result_separator = RegexSeparator(r'Result:\s*(?P<Result>.*?)$')
        self.report_is_ok = True
        self.record_to_emit = False
        self.fields_to_emit = report.fields_list
        self.commands = [line.strip().upper() for line in report.commands]

        self.fields = {}
        self.auto_fields_adder = AutoFieldsAdder(report, self.host.name, conf.log)
        self.csv_line_emitter = CsvLineEmitter(report, conf.log, self.auto_fields_adder)
        self.field_merger = FieldMerger()
        self.second_step_parser = SecondStepParser.create_from_report(self.report)

    def update_fields(self, d):
        self.field_merger.merge(d, self.fields)

    def clear_fields_except_node_and_date(self):
        self.fields = dict(
            Node=self.fields['Node'],
            Date=self.fields['Date'],
        )

    def get_csv_line(self):
        self.auto_fields_adder.add_auto_fields(self.fields)
        self.second_step_parser.parse_dict(self.report, self.fields)

        if self.record_to_emit:
            result_element = self.csv_line_emitter.emit_line_from_dict(self.fields)
            result = [result_element]
            self.clear_fields_except_node_and_date()
            self.record_to_emit = False
        else:
            result = []

        return result

    def found_node_separator(self, line):
        self.update_fields(self.node_separator.separate(line))

    def found_result_separator(self, line):
        result = self.result_separator.separate(line)['Result']
        results = {'OK': True}
        result_is_ok = results.get(result.upper(), False)

        self.report_is_ok = self.report_is_ok and result_is_ok

        result = self.get_csv_line()

        self.fields.clear()

        return result

    def parse_line(self, line):
        results = []

        if len(line.strip()) == 0 or line.strip() == '%' or self.command_in_line(line):
            results = []
        elif self.node_separator.matches(line):
            self.found_node_separator(line)
        elif self.result_separator.matches(line):
            results = self.found_result_separator(line)

        return results

    def command_in_line(self, line):
        command_in_line = False
        for command in self.commands:
            if command in line.strip().upper():
                command_in_line = True
                break

        return command_in_line

    def matches(self, line):
        return self.node_separator.matches(line) or self.result_separator.matches(line) or len(
            line.strip()) == 0 or line.strip() == '%' or self.command_in_line(line)


class SeparatedRecordsParserWithMultipleFieldSeparators(NodeAndResultParser):
    def __init__(self, record_separator, field_separators, conf, host, report):
        NodeAndResultParser.__init__(self, conf, host, report)
        self.record_separator = record_separator
        self.field_separators = field_separators

    def found_record_separator(self, line):
        result = self.get_csv_line()

        self.update_fields(self.record_separator.separate(line))
        self.record_to_emit = True

        return result

    def found_field(self, line, field_separator):
        self.update_fields(field_separator.separate(line))
        return []

    def parse_line(self, line):
        if self.record_separator.matches(line):
            results = self.found_record_separator(line)
        elif NodeAndResultParser.matches(self, line):
            results = NodeAndResultParser.parse_line(self, line)
        else:
            for field_separator in self.field_separators:
                if field_separator.matches(line):
                    results = self.found_field(line, field_separator)
                    break
            else:
                results = []

        return results


class SeparatedRecordsParser(SeparatedRecordsParserWithMultipleFieldSeparators):
    def __init__(self, record_separator, field_separator, conf, host, report):
        field_separators = [field_separator]
        SeparatedRecordsParserWithMultipleFieldSeparators.__init__(
            self, record_separator, field_separators, conf, host, report
        )


class RegexSeparatedRecordsParser(SeparatedRecordsParser):
    def __init__(self, field_separator, conf, host, report):
        record_separator = RegexSeparator(self.regex)
        SeparatedRecordsParser.__init__(self, record_separator, field_separator, conf, host, report)


class RegexParserWithMultipleFieldsSeparator(SeparatedRecordsParserWithMultipleFieldSeparators):
    def __init__(self, conf, host, report):
        record_separator = RegexSeparator(self.regex)
        SeparatedRecordsParserWithMultipleFieldSeparators.__init__(
            self, record_separator, self.field_separators, conf, host, report
        )


# Refactor to use the FullTextRegexSeparator
class RegexFullTextParser(CommandFullTextParser):
    regex = r''
    regex_mode = 0

    def __init__(self, *args, **kwargs):
        CommandFullTextParser.__init__(self, *args, **kwargs)
        self.compiled_regex = re.compile(self.regex, self.regex_mode)

    def parse_command_output(self, text):
        matches = self.compiled_regex.finditer(text)

        for match in matches:
            yield match.groupdict()


class RegexOneColumnParser(RegexSeparatedRecordsParser):
    def __init__(self, conf, host, report):
        field_separator = SingleColumnSeparator()
        RegexSeparatedRecordsParser.__init__(self, field_separator, conf, host, report)


class RegexNestingOneColumnParser(RegexSeparatedRecordsParser):
    def __init__(self, conf, host, report):
        field_separator = NestingSingleColumnSeparator()
        RegexSeparatedRecordsParser.__init__(self, field_separator, conf, host, report)


class RegexTwoColumnParser(RegexSeparatedRecordsParser):
    def __init__(self, conf, host, report):
        field_separator = FixedColumnSeparator([(1, 41), (41, 100), ])
        RegexSeparatedRecordsParser.__init__(self, field_separator, conf, host, report)
