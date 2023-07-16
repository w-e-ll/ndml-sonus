import re

from ndml_sonus.scripts.common import CommandFullTextParser
from ndml_sonus.scripts.separators import FullTextRegexSeparator, CompositeSeparator


class SgxCommandFullTextParser(CommandFullTextParser):
    separator = FullTextRegexSeparator(r'''
swmml -n (?P<SgxNode>\S+) -e \S+
(?P<CommandOutput>.*?)
\$ '''[1:])


# Refactor to use the FullTextRegexSeparator
class SgxRegexFullTextParser(SgxCommandFullTextParser):
    regex = r''
    regex_mode = re.MULTILINE

    def __init__(self, *args, **kwargs):
        SgxCommandFullTextParser.__init__(self, *args, **kwargs)
        self.compiled_regex = re.compile(self.regex, self.regex_mode)

    def parse_command_output(self, text):
        matches = self.compiled_regex.finditer(text)

        for match in matches:
            yield match.groupdict()


class SgxCommandSeparatorParser(SgxCommandFullTextParser):
    command_separator = None

    def parse_command_output(self, text):
        return self.command_separator.separate(text)


class SgxCcClientParser(SgxRegexFullTextParser):
    regex = r'^\s*(?P<Host>\S+)\s+(?P<Uid>\d+)\s+(?P<Gid>\d+)\s+(?P<Service>\S+)\s+(?P<Node>\S+)\s+(?P<Cic_Start>\d+)\s+(?P<Cic_End>\d+)\s+(?P<Rpc>\d+)\s+(?P<Args>.*?)$'


class SgxClientParser(SgxRegexFullTextParser):
    regex = r'^\s*(?P<Host>\S+)\s+(?P<Uid>\d+)\s+(?P<Gid>\d+)\s+(?P<Service>\S+)\s+(?P<Alt_Host>\S{3,})?\s+(?P<Dual>\w)\s+(?P<Proto>\S+)\s+(?P<Auth>\S+)\s+(?P<Args>.*?)$'


class SgxGtParser(SgxRegexFullTextParser):
    regex = r'^\s*TT=(?P<TT>\d+), NP=(?P<NP>\S+), NA=(?P<NA>\S+), DIG=(?P<DIG>"\d+"), PC=(?P<PC>\d+), SSN=(?P<SSN>\d+), RI=(?P<RI>\S+), BKUPPC=(?P<BKUPPC>\d+), BKUPSSN=(?P<BKUPSSN>\d+), BKUPRI=(?P<BKUPRI>\S+), LOADSHR=(?P<LOADSHR>\S+);\s*$'


class SgxOspcParser(SgxRegexFullTextParser):
    regex = r'^ +(?P<Own_Point_Code>.*?)\s+(?P<Network_Indicator>\S+)$'


class SgxSctpAssociationsParser(SgxRegexFullTextParser):
    regex = r'^  ID: (?P<Id>\d+)\s+state: (?P<State>\S+)\s+local vtag (?P<Local_Vtag>\S+)$'


class SgxSlkParser(SgxRegexFullTextParser):
    regex = r'^\s*(?P<Name>\S+)\s+(?P<Nbr>\d+)\s+(?P<LSet_Name>\S+)\s+(?P<LSet_Nbr>\d+)\s+(?P<SLC>\d+)\s+(?P<Port>\d+)\s+(?P<Chan>\d+)\s+(?P<Speed>\d+)\s+(?P<ADPC>.*?)\s+(?P<State>\S+)\s+(?P<Status>\S+)$'


class SgxTcapClientParser(SgxRegexFullTextParser):
    regex = r'^\s*(?P<Host>\S+)\s+(?P<Uid>\d+)\s+(?P<Gid>\d+)\s+(?P<Service>\S+)\s+(?P<Node>\S+)\s+(?P<SSN>\d+)\s+(?P<Args>.*?)$'


class SgxLsetSeparator(CompositeSeparator):
    def __init__(self):
        parent_separator = FullTextRegexSeparator(r'''
--- LINK SET ---

Name                              Nbr      ADPC      Status  Active Links  PC count  Err Correction  LinkType   MTP Restart  Lset Type

^(?P<Linkset_Name>\S+)\s+(?P<Linkset_Nbr>\d+)\s+(?P<Linkset_ADPC>.*?)\s+(?P<Linkset_Status>[aAr])\s+(?P<Linkset_Active_Links>\d+)\s+(?P<Linkset_PC_Count>\d+)\s+(?P<Linkset_Err_Correction>\S+)\s+(?P<Linkset_Linktype>\S+)\s+(?P<Linkset_MTP_Restart>\S+)\s+(?P<Linkset_Lset_type>\S+)\s*$


        --- SIGNALING LINKS ---
(?P<signaling_links>.*?)


'''[1:], re.DOTALL | re.MULTILINE)

        field_to_pass = 'signaling_links'
        child_separator = FullTextRegexSeparator(
            r'''^\s*(?P<Signaling_Link_Name>\S+)\s+(?P<Signaling_Link_Nbr>\d+)\s+(?P<Signaling_Link_SLC>\d+)\s+(?P<Signaling_Link_Status>[aA])\s*$''',
            re.DOTALL | re.MULTILINE)
        CompositeSeparator.__init__(self, parent_separator, field_to_pass, child_separator)


class SgxLsetParser(SgxCommandSeparatorParser):
    command_separator = SgxLsetSeparator()


class SgxRsetParser(SgxCommandSeparatorParser):
    command_separator = CompositeSeparator(
        FullTextRegexSeparator(r'''
Name                                 DPC        State   Status  Load sharing

^(?P<Routeset_Name>\S+) +(?P<Routeset_DPC>.*?) +(?P<Routeset_State>\S+) +(?P<Routeset_Status>\S+) +(?P<Routeset_Load_sharing>\S+)$


        --- ROUTES ---
(?P<routes>.*?)


'''[1:], re.DOTALL | re.MULTILINE),
        'routes',
        FullTextRegexSeparator(r'''^ *(?P<Route_Name>\S+) +(?P<Route_Status>[aAxXR]+)$''', re.DOTALL | re.MULTILINE)
    )
