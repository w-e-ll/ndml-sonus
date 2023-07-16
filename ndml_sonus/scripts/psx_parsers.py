#!/bin/env python
import csv
import re
from io import StringIO

from ndml_sonus.scripts.common import CommandFullTextParser
from ndml_sonus.scripts.separators import FullTextRegexSeparator, SingleColumnSeparator


class PsxListallCommandFullTextParser(CommandFullTextParser):
    separator = FullTextRegexSeparator(r'''
\s*Please standby for response....
\s*---------------------------
\s*Results will now be displayed....
\s*-----------------------------
(?P<CommandOutput>.*?)

Result:\s*(?P<Result>\S+)
PSX:\S+?:(?P<Node>\S+?)>'''[1:])


class PsxCsvParser(PsxListallCommandFullTextParser):
    def parse_command_output(self, text):
        text = text.replace('"~"', '""')
        reader = csv.DictReader(StringIO(text[3:]))
        for line in reader:
            yield line


class PsxFindCommandFullTextParser(CommandFullTextParser):
    separator = FullTextRegexSeparator(r'''
PSX:\S+?:(?P<Node>\S+?)> .*?

(?P<CommandOutput>.*?)

Result:\s*(?P<Result>\S+)'''[1:])


class PsxFindCommandSeparatorParser(PsxFindCommandFullTextParser):
    command_output_separator = None

    def parse_command_output(self, text):
        result = self.command_output_separator.separate(text)
        return result


class PsxFindCommandSingleColumnSeparatorParser(PsxFindCommandSeparatorParser):
    command_output_separator = SingleColumnSeparator()

    def parse_command_output(self, text):
        result = {}
        for line in text.splitlines():
            if self.command_output_separator.matches(line):
                result.update(self.command_output_separator.separate(line))
        return [result]


class PsxRegexFullTextParser(PsxFindCommandSeparatorParser):
    regex = r''
    regex_mode = re.DOTALL | re.MULTILINE

    def __init__(self, *args, **kwargs):
        PsxFindCommandFullTextParser.__init__(self, *args, **kwargs)
        self.command_output_separator = FullTextRegexSeparator(self.regex, self.regex_mode)


class PsxIpSignalingPeerGroupDataParser(PsxRegexFullTextParser):
    regex = r'''
\s*Ip_Signaling_Peer_Group_Id\s*:\s*(?P<Ip_Signaling_Peer_Group_Id>\S+)
\s*Sequence_Number\s*:\s*(?P<Sequence_Number>\d+)
\s*Service_Status\s*:\s*(?P<Service_Status>\d+)
\s*Ip_Address\s*:\s*(?P<Ip_Address>\S+)
\s*Port_Number\s*:\s*(?P<Port_Number>\d+)
\s*Server_FQDN\s*:\s*(?P<Server_FQDN>\S+)
\s*Server_FQDN_Port_Number\s*:\s*(?P<Server_FQDN_Port_Number>\d+)
\s*Attributes\s*:\s*(?P<Attributes>\d+)
'''[1:-1]
