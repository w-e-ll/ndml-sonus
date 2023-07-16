#!/bin/env python

# Start second step parsers
import time

from datetime import datetime


class SecondStepParser:
    def __init__(self, field_parsers):
        self.field_parsers = field_parsers
        
    def parse_dict(self, report, d):
        for field_parser in self.field_parsers:
            for key in d:
                if field_parser.should_parse(report, key):
                    d[key] = field_parser.parse(report, d[key])
    
    @staticmethod
    def create_from_report(report):
        instances = [globals()[klass]() for klass in report.second_step_parsers]
        return SecondStepParser(instances)        


class FieldParser:
    def parse(self, report, field_value):
        raise NotImplementedError()
    
    def should_parse(self, report, field_name):
        raise NotImplementedError()


class Triple8PointCodeParser(FieldParser):
    def parse(self, report, field_value):
        if '-' in field_value:
            try:
                v1, v2, v3 = field_value.split('-')
                new_field_value = int(v1)*(2**16) + int(v2)*(2**8) + int(v3)*(2**0)
                new_field_value = str(new_field_value)
            except:
                new_field_value = field_value
        else:
            new_field_value = field_value
        
        return new_field_value
    
    def should_parse(self, report, field_name):
        return field_name in ['Point_Code']


class LeftPointCodeParser(FieldParser):
    def parse(self, report, field_value):
        try:
            new_field_value = field_value.split('(')[0]
        except IndexError:
            new_field_value = field_value
        return new_field_value
    
    def should_parse(self, report, field_name):
        return field_name in ['Point_Code', 'Own_Point_Code', 'Routeset_DPC', 'ADPC', 'Linkset_ADPC']


class ParenthesisPointCodeParser(FieldParser):
    def parse(self, report, field_value):
        left_parethesis = field_value.find('(')
        right_parethesis = field_value.find(')')
        
        if left_parethesis >= 0 and right_parethesis >= 0:
            new_field_value = field_value[left_parethesis+1:right_parethesis]
        else:
            new_field_value = field_value
        
        return new_field_value
    
    def should_parse(self, report, field_name):
        return field_name in ['Point Code (decimal)']


class ParseException(Exception):
    pass


class UnitNotFoundException(ParseException):
    pass


class TimeParser(FieldParser):
    def _find_unit(self, s):
        i = s.find('Secs')

        if i >= 0:
            unit = 1
        else:
            i = s.find('minu')
            if i >= 0:
                unit = 60
            else:
                i = s.find('(ms)')
                if i >= 0:
                    unit = 1.0/1000
                else:
                    raise UnitNotFoundException()
        
        return unit, i
      
    def parse(self, report, field_value):
        unit, index = self._find_unit(field_value)
        new_field_value = int(field_value[0:index].strip())*unit  
        return new_field_value
    
    def should_parse(self, report, field_name):
        return field_name in [
            'Handshake Interval', 'Secondary Link Oos Delay',
            'Primary Link Oos Delay', 'T29', 'TA      (- | Ta)',
            'TCOT,d  (- | TCOT,d)', 'TEXM,d  (TEXM,d | TEXM,d)'
        ]


class HexadecimalParser(FieldParser):
    def parse(self, report, field_value):
        new_field_value = int(field_value, 16)
        return new_field_value
    
    def should_parse(self, report, field_name):
        cond1 = field_name in ['Idle_Code', 'Idle Code', 'Transmission_Medium'] and \
                report.name in ['e1_all_admin', 'e1_profile_all_admin', 'psx_route']
        cond2 = field_name in ['Options', 'Attributes', 'Attributes2', 'Attributes3', 'Attributes4'] and \
            report.name == 'psx_packet_service_profile'
        cond3 = field_name in ['Attributes', 'Attributes2'] and report.name == 'psx_codec_entry'
        cond4 = field_name in [
            'Ip_Sig_Attributes1', 'Ip_Sig_Attributes2', 'Ip_Sig_Attributes3',
            'Ip_Sig_Attributes4', 'Sip_Call_Forwarding_Mapping', 'Ip_Sig_Attributes5',
            'Ip_Sig_Attributes6', 'Ip_Sig_Attributes7', 'Ip_Sig_Attributes8', ] and \
            report.name == 'psx_ip_signaling_profile'

        return cond1 or cond2 or cond3 or cond4


class RemovePercentParser(FieldParser):
    def parse(self, report, field_value):
        index = field_value.find('%%')
        new_field_value = field_value[0:index]
        return new_field_value
    
    def should_parse(self, report, field_name):
        return field_name.find('ACC L') >= 0 and field_name.find('R Cancel') >= 0


class DateParser(FieldParser):
    def parse_date(self, s):
        try: 
            return datetime.strptime(s, '%m/%d/%y %I:%M:%S %p %Z')
        except AttributeError:  # python 2.4
            ts = time.strptime(s, '%m/%d/%y %I:%M:%S %p %Z')
            return datetime(ts.tm_year, ts.tm_mon, ts.tm_mday, ts.tm_hour, ts.tm_min)
    
    def parse(self, report, field_value):
        date_object = self.parse_date(field_value)
        ORACLE_DATE_FORMAT = '%Y/%m/%d %H:%M:%S'
        return date_object.strftime(ORACLE_DATE_FORMAT)

    def should_parse(self, report, field_name):
        return field_name in ['TIMESTAMP', 'STATDATE']

# End second step parsers
