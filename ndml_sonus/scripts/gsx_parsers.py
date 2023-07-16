import re
import csv
from io import StringIO

from ndml_sonus.scripts.common import RegexFullTextParser, RegexOneColumnParser, \
    RegexParserWithMultipleFieldsSeparator, RegexNestingOneColumnParser, \
    RegexTwoColumnParser, CommandFullTextParser

from ndml_sonus.scripts.separators import SingleColumnSeparator, SimpleFixedColumnSeparator, \
    NameValueInTwoColumnsSeparator, FullTextRegexSeparator


class CarrierAdminParser(RegexFullTextParser):
    regex = r'\s*(?P<Carrier_Name>\S+)\s+(?P<Code>\d+)\s+(?P<Type>\S+)\s+(?P<Network_Plan>\S+)\s+(?P<State>\S+)\s*\n'


class CircuitServiceProfileParser(RegexOneColumnParser):
    regex = r'Circuit Service Profile (?P<Circuit_Service_Profile>\S*) Configuration'


class EchoCancellerProfileParser(RegexOneColumnParser):
    regex = r'\s*Echo Canceller Profile:\s*(?P<Echo_Canceller_Profile>\S+)'


class ShelfOneColumnParser(RegexOneColumnParser):
    regex = r"Shelf:\s*(?P<Shelf>\d+)\s*Slot:\s*(?P<Slot>\d+)\s*Port:\s*(?P<Port>\d+)\s*DS1:\s*(?P<DS1>\d+)"


class ShelfIfIndexParser(RegexOneColumnParser):
    regex = r"Shelf:\s*(?P<Shelf>\d+)\s*Slot:\s*(?P<Slot>\d+)\s*Port:\s*(?P<Port>\d+)\s*IfIndex:\s*(?P<IfIndex>\d+)"


class IsupSignalingGroupParser(RegexParserWithMultipleFieldsSeparator):
    regex = r'\s*ISUP Signaling Group : (?P<ISUP_Signaling_Group>\S+)\s+Version ID : (?P<Version_ID>\S+)\s*'
    field_separators = [SingleColumnSeparator(), SimpleFixedColumnSeparator([(1, 45), (45, 100)])]


class IsupServiceStatusParser(RegexFullTextParser):
    regex = r'\s*(?P<ISUP_Service>\S+)\s+(?P<Point_Code>\S+)\s+(?P<Status>\S+)\s+\n'


class IsupSignalingProfileParser(RegexFullTextParser):
    regex = r'\s*(?P<Name>\S+) +(?P<Admin_State>\S+) +(?P<Base_Profile>\S+)? +\n'


class IsupINRINFProfileAdmin(RegexOneColumnParser):
    regex = r'\s*ISUP INR INF Profile : (?P<ISUP_INR_INF_Profile>\S+)\s+'


class IsupServiceParser(RegexTwoColumnParser):
    regex = r"\s*ISUP Service\s*:\s*(?P<ISUP_Service>\S*)\s*Point Code\s*:\s*(?P<Point_Code>\S*)\s*"


class IsupProfileParser(RegexTwoColumnParser):
    regex = r"\s*ISUP Service Profile\s*:\s*(?P<ISUP_Service_Profile>\S*)\s*"


class SipServiceParser(RegexOneColumnParser):
    regex = r"\s*SIP Service\s*:\s*(?P<SIP_Service>\S+)"


class SipServiceStatusParser(RegexFullTextParser):
    regex = r'^ *(?P<SIP_Service>\w+) +(?P<Status>\w+) *$'
    regex_mode = re.MULTILINE


class Ss7GatewayParser(RegexNestingOneColumnParser):
    regex = r'SS7 Gateway (?P<Gateway>\S*) Configuration'


class Ss7NodeParser(RegexParserWithMultipleFieldsSeparator):
    regex = r'SS7 Node (?P<Ss7Node>\S*) Configuration'
    field_separators = [
        SingleColumnSeparator(),
        SimpleFixedColumnSeparator([(5, 26), (26, 100)]),
        SimpleFixedColumnSeparator([(5, 37), (37, 100)])
    ]


class StaticCallParser(RegexFullTextParser):
    regex = r'\s*(?P<Index>\d+)\s+(?P<Name>\S+)\s+(?P<AdminState>\S+)\s+(?P<CircuitMode>\S+)\s+(?P<shelfA>\d+)\s+(?P<shelfB>\d+)\s+/\s+(?P<LocalRTP>\S+)\s+(?P<slotA>\d+)\s+(?P<slotB>\d+)\s+/\s+(?P<LocalIP>\S+)\s+(?P<portA>\d+)\s+(?P<portB>\d+)\s+/\s+(?P<RemoteRTP>\S+)\s+(?P<channelA>\d+)\s+(?P<channelB>\d+)\s+/\s+(?P<RemoteIP>\S+)\s+(?P<servProfileA>\S*)\s+(?P<servProfileB>\S*)\s+\n'


class TrunkGroupAdminParser(RegexParserWithMultipleFieldsSeparator):
    regex = r'Local Trunk Name: (?P<Local_Trunk_Name>\S+)'
    field_separators = [NameValueInTwoColumnsSeparator((1, 49), (49, 100))]


class TrunkGroupStatusParser(RegexOneColumnParser):
    regex = r'\s*(?P<Local_Trunk_Name>\S+)\s+(?P<Total_Calls_Conf>\S+)\s+(?P<Total_Calls_Avail>\S+)\s+(?P<In_Calls_Resv>\d+)\s+(?P<In_Calls_Usage>\d+)\s+(?P<Outbound_Calls_Usages_no_pri>\d+)\s+(?P<Outbound_Calls_Usages_pri>\d+)\s+(?P<Outbound_Calls_Resv>\d+)\s+(?P<Oper_State>\S+)\s+\n'


class TrunkGroupBandwidthStatusParser(RegexFullTextParser):
    regex = r'''(?P<Local_Trunk_Name>\S+)\s+(?P<Bandwidth_Alloc>\S+)\s+(?P<Call_Alloc>\S+)\s+(?P<Current_BW_Limit>\S+)\s+(?P<Bandwidth_Available>\S+)\s+(?P<Inbound_BW_Usage>\d+)\s+(?P<Outbound_BW_Usage>\d+)\s*
(?P<Packet_Outage_State>\S+)\s+\n'''


class TrunkGroupDirectionParser(RegexFullTextParser):
    regex = r'(?P<Local_Trunk_Name>\S+)\s+(?P<One_Way_In_Conf>\S+)\s+(?P<One_Way_In_Avail>\S+)\s+(?P<One_Way_In_Usage>\d+)\s+(?P<One_Way_Out_Conf>\S+)\s+(?P<One_Way_Out_Avail>\S+)\s+(?P<One_Way_Out_Usage>\d+)\s+(?P<Two_Way_Conf>\S+)\s+(?P<Two_Way_Avail>\S+)\s+(?P<Two_Way_Usage>\d+)\s*$'
    regex_mode = re.MULTILINE


class StaticCallStatusParser(RegexFullTextParser):
    regex = r'\s*(?P<Index>\d+)\s+(?P<GCID>\S+)\s+(?P<OperState>\S+)\s+(?P<CreationTime>\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s*\n'


class NifGroupAdminParser(RegexFullTextParser):
    regex = r'^(?P<NIF_Group>\S+)\s+(?P<NIF_Group_State>\S+)\s{2,}(?P<Interface>\S+)\s+(?P<Interface_State>\S+)\s*$'
    regex_mode = re.MULTILINE


class SctpProfileAllAdminParser(RegexOneColumnParser):
    regex = r'\s*Sctp Profile:\s*(?P<Sctp_Profile>\S+)'


class GatewayServiceAdminParser(RegexOneColumnParser):
    regex = r'\s*Gateway Service\s*:\s*(?P<Gateway_Service>\S+)'


class ZoneAdminParser(RegexOneColumnParser):
    regex = r'\s*Zone Name:\s*(?P<Zone_Name>\S+)'


class SignalingPortAdminParser(RegexFullTextParser):
    # regex = r'\s*(?P<Port_Num>\d+)\s+(?P<Pri_IP_Addr>\S+)\s+(?P<Port>\d+)\s+(?P<Intf>\S+)\s+(?P<Mode>\S+)\s+(?P<State>\S+)\s+(?P<Sig_Zone>\S+)\s*\n\s*(?P<Sec_IP_Addr>\S+)\s+(?P<Recorder>\S+)\s+(?P<Slot>\d+)\s+(?P<NIF_Group>\S*)\s*\n\s*(?P<UDP_Checksum>\S*)\s+(?P<Sctp_Profile>\S+)\s*\n\s*(?P<State_2>\S+)\s*\n'
    # regex = r'\s*(?P<Port_Num>\d+)\s+(?P<Pri_IP_Addr>\S+)\s+(?P<Port>\d+)\s+(?P<Slot>\d+)\s+(?P<Intf>\S+)\s+\n\s*(?P<Sec_IP_Addr>\S+)\s+(?P<State>\S+)\s+(?P<Mode>\S+)\s+(?P<Recorder>\S+)\s*\n\s*(?P<Sig_Zone>\S+)\s+(?P<UDP_Checksum>\S*)\s*\n\s*(?P<NIF_Group>\S*)\s*\n\s*(?P<Sctp_Profile>\S+)\s*\n\s*(?P<Ipsec_Pol>\S*)\s*\n'
    regex = r'\s*(?P<Port_Num>\d+)\s(?P<Pri_IP_Addr>\S+)\s+(?P<Port>\d+)\s+(?P<Slot>\d+)\s+(?P<Intf>\S+)\s*\n\s{5}(?P<Sec_IP_Addr>\S+)\s+(?P<State>\S+)\s+(?P<Mode>\S+)\s+(?P<Recorder>\S+)\s*\n\s{5}(?P<Sig_Zone>\S+)\s+(?P<UDP_Checksum>\S*)\s*\n\s{5}(?P<NIF_Group>\S*)\s*(?P<Traceroute>\S*)\s*\n\s{5}(?P<Sctp_Profile>\S+)\s*\n\s{5}(?P<Ipsec_Pol>\S*)\s*\n'


class NifSubinterfaceAdmin(RegexFullTextParser):
    regex = r'^\s*(?P<shelf>\d+)-(?P<slot>\d+)\s+(?P<port>\d+)\s+(?P<name>\S+)\s+(?P<index>\d+)\s+(?P<mode>\S+)\s+(?P<IP_Address>\S+)\s+(?P<deviatn>\d+)\s*\n\s*(?P<type>\S+)\s+(?P<state>\S+)\s+(?P<action>\S+)\s+(?P<mask>\S+)\s+(?P<conting>\d+)\s*\n\s*(?P<vlantag>\d+)\s+(?P<timeout>\d+)\s+(?P<nexthop>\S+)\s*\n\s*(?P<bw>\d+)\s+(?P<PVP_bucket>\d+)\s+(?P<PVP_rate>\d+)\s*\n\s*(?P<IPSec_Policy>\S*)$'
    regex_mode = re.MULTILINE


class NifAdmin(RegexFullTextParser):
    regex = r'^\s*(?P<shelf>\d+)-(?P<slot>\d+)\s+(?P<port>\d+)\s+(?P<name>\S+)\s+(?P<index>\d+)\s+(?P<mode>\S+)\s+(?P<IP_Address>\S+)\s+(?P<deviatn>\d+)\s*\n\s*(?P<type>\S+)\s+(?P<class>\S+)\s+(?P<action>\S+)\s+(?P<mask>\S+)\s+(?P<conting>\d+)\s*\n\s*(?P<state>\S+)\s+(?P<timeout>\d+)\s+(?P<nexthop>\S+)\s*\n\s*(?P<DGPstate>\S+)\s+(?P<DGP_bucket>\d+)\s+(?P<DGP_rate>\d+)\s*\n\s*(?P<PVPstate>\S+)\s+(?P<PVP_bucket>\d+)\s+(?P<PVP_rate>\d+)\s*\n\s*(?P<LGPstate>\S+)\s+(?P<xnq>\S+)\s*\n\s*(?P<vstate>\S+)\s+(?P<tag>\d+)\s+(?P<IPSec_Policy>\S*)$'
    regex_mode = re.MULTILINE


class IPNetworkSelectorTableAdmin(CommandFullTextParser):
    def parse_command_output(self, text):
        result = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                split_line = line.split()
                if len(split_line) == 3:
                    # Easy case, all the IPs are properly separated
                    table_name, network_number, network_mask = split_line
                elif len(split_line) == 2:
                    # IPs are joined together.  This assumes that the netmask will always have 3 digits
                    # in the first octet (like 255.0.0.0). Netmask like 80.255.255.255 is not supported.
                    table_name = split_line[0]

                    split_dots = split_line[1].split('.')
                    network_number = '.'.join(split_dots[0:3] + [split_dots[3][:-3]])
                    network_mask = '.'.join([split_dots[3][-3:]] + split_dots[4:])
                else:
                    continue

                result.append(
                    {'Table Name': table_name, 'Network Number': network_number, 'Network Mask': network_mask}
                )

        return result


class InventoryHardware(CommandFullTextParser):
    def parse_command_output(self, text):
        # import pdb
        # pdb.set_trace()
        result = []
        shelf = {}
        mta = []
        slots = {}

        for line in text.splitlines():
            regex = re.compile(r'^\s*Shelf:(?P<shelf_number>\d+)\s+Slots:(?P<shelf_slots>\d+)\s+Hardware:(?P<shelf_hardware>\S+)\s+Serial#:(?P<shelf_serial_number>\S+)\s*$')
            match = regex.match(line)
            if match:
                shelf.update(match.groupdict())

            regex = re.compile(r'^\s*MTA Slot 1 Type:\s*(?P<mta_type>\S+)\s+Rev Type:\s*(?P<mta_rev_type>\d+)\s+Serial#:(?P<mta_serial_number>\d+)\s+PartNum:\s*(?P<mta_part_num>\S+)\s+Rev:(?P<mta_part_rev>\S*)\s*$')
            match = regex.match(line)
            if match:
                mta.append(match.groupdict())

            regex = re.compile(r'^\s*MTA Slot 2 Type:\s*(?P<mta_type>\S+)\s+Rev Type:\s*(?P<mta_rev_type>\d+)\s+Serial#:(?P<mta_serial_number>\d+)\s+PartNum:\s*(?P<mta_part_num>\S+)\s+Rev:(?P<mta_part_rev>\S*)\s*$')
            match = regex.match(line)
            if match:
                mta.append(match.groupdict())

            regex = re.compile(r'^\s*(?P<slot>\d{1,2})\s+(?P<server_hwtype>\S+)\s+(?P<server_hwtype_rev>\d+|N/A)\s+(?P<server_part_number>\S+)\s+(?P<server_part_number_rev>\S+)\s+(?P<server_serial_number>\S+)\s+(?P<adapter_hwtype>\S+)\s+(?P<adapter_hwtype_rev>\S+)\s+(?P<adapter_part_number>\S+)\s+(?P<adapter_part_number_rev>\S+)\s+(?P<adapter_serial_number>\S+)\s*$')
            match = regex.match(line)
            if match:
                slots[(match.groupdict().get('slot'))] = {'0': match.groupdict()}
                slots[(match.groupdict().get('slot'))]['0'].update({'rear_sub_slot': '1'})

            regex = re.compile(r'^\s*(?P<slot>\d{1,2})\s+(?P<pim>\d{1})\s+(?P<pims_hwtype>\S+)\s+(?P<pims_hwtype_rev>\S+)\s+(?P<pims_part_number>\S+)\s+(?P<pims_part_number_rev>\S+)\s+(?P<pims_serial_number>\S+)\s+(?P<sfp_state>\S+)\s+(?P<sfp_hwtype_rev>\S+)\s+(?P<sfp_part_number>\S+)\s+(?P<sfp_part_number_rev>\S*)\s+(?P<sfp_serial_number>\S+)\s*$')
            match = regex.match(line)
            if match:
                slots[(match.groupdict().get('slot'))].update({match.groupdict().get('pim'): match.groupdict()})

        for shelf_slot, values in slots.items():
            # for each slot generate multiple hardware record lines, currently we can have up to the following records:
            # 1 if there are no pims
            # 3 if there are two pims
            # 2 for slot 1&2 as there are 2 two half cards in the back

            # Build the hardware record
            record_dict = {}
            record_dict.update(shelf)  # add the common shelf common fields
            record_dict.update(values['0'])  # add the server and adapter fields
            result.append(record_dict.copy())

            # add mta slot 1 info when slot equals 1
            if values['0'].get('slot') == '1':
                # <mta_type> <mta_rev_type> <mta_serial_number> <mta_part_num> <mta_part_rev>
                record_dict.update(
                    {
                        'adapter_hwtype': mta[0].get('mta_type'),
                        'adapter_hwtype_rev': mta[0].get('mta_rev_type'),
                        'adapter_part_number': mta[0].get('mta_part_num'),
                        'adapter_part_number_rev': mta[0].get('mta_part_rev'),
                        'adapter_serial_number': mta[0].get('mta_serial_number')
                    }
                )
                record_dict.update({'rear_sub_slot': '2'})
                result.append(record_dict.copy())

            # add mta slot 2 info when slot equals 2
            if values['0'].get('slot') == '2':
                # <mta_type> <mta_rev_type> <mta_serial_number> <mta_part_num> <mta_part_rev>
                record_dict.update(
                    {
                        'adapter_hwtype': mta[1].get('mta_type'),
                        'adapter_hwtype_rev': mta[1].get('mta_rev_type'),
                        'adapter_part_number': mta[1].get('mta_part_num'),
                        'adapter_part_number_rev': mta[1].get('mta_part_rev'),
                        'adapter_serial_number': mta[1].get('mta_serial_number')
                    }
                )
                record_dict.update({'rear_sub_slot': '2'})
                result.append(record_dict.copy())

            # There is a first pim connector
            if '1' in values:
                record_dict.update(values['1'])
                result.append(record_dict.copy())

            # There is a second pim connector
            if '2' in values:
                record_dict.update(values['2'])
                result.append(record_dict.copy())

        return result


class LocalNameServiceAdminParser(RegexFullTextParser):
    # regex = r'^\s*(?P<record_name>\S+)\s+(?P<host_name>\S+)\s+(?P<rec_mode>\S+)\s+(?P<pri>\d+)\s+(?P<ip_address>\S+)\s+(?P<entry_mode>\S+)\s*$'
    regex = r'\s*(?P<record_name>\S+)\s+(?P<host_name>\S+)\s+(?P<rec_mode>\S+)\s+(?P<pri>\d+)\s+(?P<type>\S+)\s+(?P<entry_mode>\S+)\s*\n(?P<dns_zone_name>\S+)\s+(?P<ip_address>\S+)\s*\n'
    regex_mode = re.MULTILINE


class InventorySummary(RegexFullTextParser):
    regex = r'^(?P<shelf_number>\d+)\s+(?P<slot_number>\d+)\s+(?P<server_hw_type>\S+)\s+(?P<server_state>\S+)\s+(?P<adapter_hw_type>\S+)\s+(?P<adapter_state>\S+)\s*$'
    regex_mode = re.MULTILINE


class ServerAdminSummary(RegexFullTextParser):
    regex = r'^(?P<shelf_number>\d+)\s+(?P<slot_number>\d+)\s+(?P<server_hw_type>\S+)\s+(?P<adapter_hw_type>\S+)\s+(?P<server_admin_state>\S+)\s+(?P<mode>\S+)\s+(?P<function>\S+)\s+(?P<redun_type>\S+)\s*$'
    regex_mode = re.MULTILINE


class StMtaAdmin(RegexFullTextParser):
    regex = r'^(?P<shelf_number>\d+)\s+(?P<mta_slot>\S+)\s+(?P<admin_state>\S+)\s+(?P<line_encoding>\S+)\s+(?P<framer_mode>\S+)\s+(?P<channel_bit>\S+)\s*$'
    regex_mode = re.MULTILINE


class StMtaStatus(RegexFullTextParser):
    regex = r'^(?P<shelf_number>\d+)\s+(?P<mta_slot>\S+)\s+(?P<mta_type_rev>\S+)\s+(?P<operational_state>\S+)\s*$'
    regex_mode = re.MULTILINE


# Substitute by a composite separator with parent being the regex that matches the global field?
class SoftswitchAdminParser(CommandFullTextParser):
    def parse_command_output(self, text):
        record_regex = re.compile(r'\s*(?P<Index>\d+)\s*(?P<SoftSwitchName>\S+)\s*(?P<IpAddress>\S+)\s*(?P<Port>\d+)\s*(?P<SubPort>\d+)\s*(?P<Mode>\S+)\s*(?P<State>\S+) *\n')
        matches = record_regex.finditer(text)
        last_match = list(record_regex.finditer(text))[-1].end()
        global_fields = self.parse_global_fields(text[last_match:])

        for match in matches:
            result = match.groupdict()
            result.update(global_fields)
            yield result

    def parse_global_fields(self, text):
        result = {}

        for line in text.splitlines():
            if line.strip() != '':
                global_field = self.parse_global_field(line)
                result.update(global_field)

        return result

    @staticmethod
    def parse_global_field(line):
        separator = NameValueInTwoColumnsSeparator((1, 25), (25, 100))
        return separator.separate(line)


class SoftswitchStatusParser(RegexFullTextParser):
    regex = r'\s*(?P<SoftSwtichName>\S+)\s+(?P<State>\S+)\s+(?P<Congest>\S+)\s+(?P<Completed>\d+)\s+(?P<Retries>\d+)\s+(?P<Failed>\S+)\s*\n'


class E1ProfileParser(RegexFullTextParser):
    regex = r'''
------------------------------------------------------------------------
E1 Profile:                  (?P<E1_Profile>\S+)
------------------------------------------------------------------------
Index:                       (?P<Index>\d+)
Profile State:               (?P<Profile_State>\S+)
Available Channels:          (?P<Available_Channels>\S+)
Line Type:                   (?P<Line_Type>\S+)
Line Coding:                 (?P<Line_Coding>\S+)
Signaling Mode:              (?P<Signaling_Mode>\S+)
Line Build Out:              (?P<Line_Build_Out>\S+)
Idle Code:                   (?P<Idle_Code>\S+)
-----------------------------------------------------------------------
E1 Threshold Configuration
-----------------------------------------------------------------------
15 Minute Intervals:              Minor   Major   Critical   TCA Filter
-----------------------------------------------------------------------
Line Code Violations:             (?P<Line_Code_Violations_15_Minor>\d+)\s+(?P<Line_Code_Violations_15_Major>\d+)\s+(?P<Line_Code_Violations_15_Critical>\d+)\s+(?P<TCA_Filter_Line_Code_Violations_15>\S+)\s*
Line Errored Seconds:             (?P<Line_Errored_Seconds_15_Minor>\d+)\s+(?P<Line_Errored_Seconds_15_Major>\d+)\s+(?P<Line_Errored_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_Line_Errored_Seconds_15>\S+)\s*
Line Severely Errored Seconds:    (?P<Line_Severely_Errored_Seconds_15_Minor>\d+)\s+(?P<Line_Severely_Errored_Seconds_15_Major>\d+)\s+(?P<Line_Severely_Errored_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_Line_Severely_Errored_Seconds_15>\S+)\s*
Path Code Violations:             (?P<Path_Code_Violations_15_Minor>\d+)\s+(?P<Path_Code_Violations_15_Major>\d+)\s+(?P<Path_Code_Violations_15_Critical>\d+)\s+(?P<TCA_Filter_Path_Code_Violations_15>\S+)\s*
Path Errored Seconds:             (?P<Path_Errored_Seconds_15_Minor>\d+)\s+(?P<Path_Errored_Seconds_15_Major>\d+)\s+(?P<Path_Errored_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_Path_Errored_Seconds_15>\S+)\s*
Path Severely Errored Seconds:    (?P<Path_Severely_Errored_Seconds_15_Minor>\d+)\s+(?P<Path_Severely_Errored_Seconds_15_Major>\d+)\s+(?P<Path_Severely_Errored_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_Path_Severely_Errored_Seconds_15>\S+)\s*
SAS Seconds:                      (?P<SAS_Seconds_15_Minor>\d+)\s+(?P<SAS_Seconds_15_Major>\d+)\s+(?P<SAS_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_SAS_Seconds_15>\S+)\s*
Controlled Slip Seconds:          (?P<Controlled_Slip_Seconds_15_Minor>\d+)\s+(?P<Controlled_Slip_Seconds_15_Major>\d+)\s+(?P<Controlled_Slip_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_Controlled_Slip_Seconds_15>\S+)\s*
Unavailable Seconds:              (?P<Unavailable_Seconds_15_Minor>\d+)\s+(?P<Unavailable_Seconds_15_Major>\d+)\s+(?P<Unavailable_Seconds_15_Critical>\d+)\s+(?P<TCA_Filter_Unavailable_Seconds_15>\S+)\s*
-------------------------------------------------------------------------
24 Hour Intervals:                Minor   Major   Critical   TCA Filter
-------------------------------------------------------------------------
Line Code Violations:             (?P<Line_Code_Violations_24_Minor>\d+)\s+(?P<Line_Code_Violations_24_Major>\d+)\s+(?P<Line_Code_Violations_24_Critical>\d+)\s+(?P<TCA_Filter_Line_Code_Violations_24>\S+)\s*
Line Errored Seconds:             (?P<Line_Errored_Seconds_24_Minor>\d+)\s+(?P<Line_Errored_Seconds_24_Major>\d+)\s+(?P<Line_Errored_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_Line_Errored_Seconds_24>\S+)\s*
Line Severely Errored Seconds:    (?P<Line_Severely_Errored_Seconds_24_Minor>\d+)\s+(?P<Line_Severely_Errored_Seconds_24_Major>\d+)\s+(?P<Line_Severely_Errored_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_Line_Severely_Errored_Seconds_24>\S+)\s*
Path Code Violations:             (?P<Path_Code_Violations_24_Minor>\d+)\s+(?P<Path_Code_Violations_24_Major>\d+)\s+(?P<Path_Code_Violations_24_Critical>\d+)\s+(?P<TCA_Filter_Path_Code_Violations_24>\S+)\s*
Path Errored Seconds:             (?P<Path_Errored_Seconds_24_Minor>\d+)\s+(?P<Path_Errored_Seconds_24_Major>\d+)\s+(?P<Path_Errored_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_Path_Errored_Seconds_24>\S+)\s*
Path Severely Errored Seconds:    (?P<Path_Severely_Errored_Seconds_24_Minor>\d+)\s+(?P<Path_Severely_Errored_Seconds_24_Major>\d+)\s+(?P<Path_Severely_Errored_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_Path_Severely_Errored_Seconds_24>\S+)\s*
SAS Seconds:                      (?P<SAS_Seconds_24_Minor>\d+)\s+(?P<SAS_Seconds_24_Major>\d+)\s+(?P<SAS_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_SAS_Seconds_24>\S+)\s*
Controlled Slip Seconds:          (?P<Controlled_Slip_Seconds_24_Minor>\d+)\s+(?P<Controlled_Slip_Seconds_24_Major>\d+)\s+(?P<Controlled_Slip_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_Controlled_Slip_Seconds_24>\S+)\s*
Unavailable Seconds:              (?P<Unavailable_Seconds_24_Minor>\d+)\s+(?P<Unavailable_Seconds_24_Major>\d+)\s+(?P<Unavailable_Seconds_24_Critical>\d+)\s+(?P<TCA_Filter_Unavailable_Seconds_24>\S+)\s*
-------------------------------------------------------------------------
TCA Reporting:                    Minor/Critical   DS1 OOS
-------------------------------------------------------------------------
                                  (?P<TCA_Reporting_MinorCritical>\S+)\s+(?P<TCA_Reporting_DS1_OOS>\S+)\s*'''[1:]


class Ss7NodeStatusParser(CommandFullTextParser):
    @staticmethod
    def parse_active_table(table):
        regex = re.compile(r'\s*(?P<Active_CE>\S+)\s+(?P<Active_Host_Name>\S+)\s+(?P<Active_Ip_Address>\d+.\d+.\d+.\d+)\s+(?P<Active_Link_State>\S+)\s+(?P<Active_Link_Mode>\S+)')
        for match in regex.finditer(table):
            yield match

    @staticmethod
    def parse_standby_table(table):
        regex = re.compile(r'\s*(?P<Standby_CE>\S+)\s+(?P<Standby_Host_Name>\S+)\s+(?P<Standby_Ip_Address>\d+.\d+.\d+.\d+)\s+(?P<Standby_Link_State>\S+)\s+(?P<Standby_Link_Mode>\S+)')
        for match in regex.finditer(table):
            yield match

    def parse_tables(self, tables):
        end_first_table = tables.find('Standby Management Server Module [--] SS7 Gateway TCP Connections Map:')
        active_table = tables[:end_first_table]
        standby_table = tables[end_first_table:]

        for result in self.parse_active_table(active_table):
            yield result

        for result in self.parse_standby_table(standby_table):
            yield result

    def parse_record(self, record):

        global_record_regex_str = r'''SS7 Node (?P<SS7_Node_Name>\S+) Status\s*Index:\s+(?P<Index>\d+)\s*Admin. State:\s+(?P<Admin_State>\S+)\s*Mode:\s+(?P<Mode>\S+)\s*ISUP\S* Status:\s+(?P<ISUP_Status>\S+)\s*(SS7 Gateway Name:\s+)?(?P<SS7_Gateway_Name>\S+)?\s*(SS7 Alt Gateway Name:\s+)?(?P<SS7_Alt_Gateway_Name>\S+)?\s*(SS7 Gateway Socket Type:\s+)?(?P<SS7_Gateway_Socket_Type>\S+)?\s*(Primary CE:\s+)?(?P<Primary_CE>\S+)?\s*
'''
        global_record_regex = re.compile(global_record_regex_str)
        print(record)
        global_matches = global_record_regex.finditer(record)
        global_match = list(global_matches)[0]
        global_fields = global_match.groupdict()
        print(global_fields)
        tables = record[global_match.end()+1:]
        print('table_content: %s' % tables)
        # there can be no tables
        if len(tables) == 0:
            yield global_fields
        else:
            for line in self.parse_tables(tables):
                result = line.groupdict()
                result.update(global_fields)
                yield result

    def parse_command_output(self, text):
        start_record = 0
        while start_record != -1:
            start_record = text.find('SS7 Node', start_record)
            end_record = text.find('SS7 Node', start_record+1)

            record = text[start_record:end_record]
            start_record = end_record

            if start_record != -1:
                for result in self.parse_record(record):
                    yield result


class TrunkGroupReportsParser(CommandFullTextParser):
    separator = FullTextRegexSeparator(r'(?P<CommandOutput>.*)')

    def parse_command_output(self, text):
        if len(text) != 0:
            first_line, rest = text.split('\n', 1)
            report_date = first_line.split(',')[2]
            reader = csv.DictReader(StringIO(rest[2:]))
            for line in reader:
                line.update({'Date': report_date})
                yield line
