#!/bin/env python
"""
Module to retrieve data for the SONUS
"""

import fnmatch
import os
import socket
import re
import time
import zipfile

from datetime import datetime
from optparse import OptionParser

import paramiko

from ndml_sonus.lib.ndml_utils_tgw import Config


class GetException(Exception):
    pass


class TransportPool(dict):
    pass


class GenericCommandGetter:
    """
    Run CLI commands via transport protocol and save output
    """

    def __init__(self, conf, host, report, prompt_usr='ogin:', prompt_pwd='assword:', prompt_cmd='$ '):
        """
        * prompt_usr: username prompt
        * prompt_pwd: password prompt
        * prompt_cmd: normal prompt after a command
        """
        self.conf = conf
        self.host = host
        self.report = report
        self.prompt_usr = prompt_usr
        self.prompt_pwd = prompt_pwd
        self.prompt_cmd = prompt_cmd

        # Context info to include in all logging messages
        self.context = '%s/%s' % (self.host.name, self.report.name)

    def get(self):
        """
        Retrieves the report data and save to raw file
        """
        self.conf.log.debug('%s: getting data via %s' % (self.context, type(self)))

        # Open output file
        raw_file = self.conf.raw_file_name(self.host, self.report)
        tmp_file = os.path.join(self.conf.tmp_dir, os.path.basename(raw_file))
        fn = open(tmp_file, 'w')

        self._open_transport()
        self._authenticate()
        fn.write(self._exec_commands())
        self._close_transport()

        fn.close()
        if os.path.exists(raw_file):
            os.unlink(raw_file)
        os.rename(tmp_file, raw_file)

    def _open_transport(self):
        """
        Open transport protocol connection to host
        """
        try:
            self.conf.log.info('%s: opening transport' % self.context)
            self.tn = self._get_transport_instance()
            self.conf.log.info('%s: transport open' % self.context)
        except Exception as e:
            self.conf.log.critical('%s: could not open transport: %s' % (self.context, str(e)))
            raise GetException()

    def _get_transport_instance(self):
        raise NotImplementedError()

    def _close_transport(self):
        self.conf.log.debug('%s: closing transport' % self.context)
        self._close_transport_instance(self.tn)
        self.conf.log.info('%s: transport closed' % self.context)

    def _close_transport_instance(self, tn):
        raise NotImplementedError()

    def _authenticate(self):
        raise NotImplementedError()

    def _exec_command(self, cmd):
        raise NotImplementedError()

    def get_commands(self):
        for command in self.report.commands:
            yield command

    def _exec_commands_do(self):
        """
        Executes list of commands for the report.
        Returns produced output.
        """

        self.conf.log.info('********************START _EXEC_COMMANDS_DO*************')
        output = ''
        try:
            commands = self.get_commands()
            for cmd in commands:
                self.conf.log.debug('%s: executing commmand "%s"' % (self.context, cmd))
                cmd_output = self._exec_command(cmd)
                # output += cmd_output.replace('\r\n', '\n')
                output += cmd_output.replace('\r', '')
                self.conf.log.debug('%s: received %d chars' % (self.context, len(output)))
                self.conf.log.debug("Waiting before running new command...")
                time.sleep(3)

            return output

        except EOFError:
            if cmd == 'logout':
                return output
            else:
                self.conf.log.critical(
                    '%s: transport protocol connection closed unexpectedly, received %d chars' % (
                        self.context, len(output)
                    )
                )
                raise GetException()

        except Exception as e:
            self.conf.log.critical('%s: error in getting command output: %s' % (self.context, str(e)))
            self._close_transport()
            raise GetException()

    def _exec_commands(self):
        result = ''
        for instance in self.report.instances:
            self.conf.log.debug('%s: executing yeeey in instance %s' % (self.context, instance))
            self._change_to_instance(instance)
            result += self._exec_commands_do()
            self.conf.log.debug('%s: report finished in instance %s.' % (self.context, instance))

        return result

    def _change_to_instance(self, instance):
        raise NotImplementedError()


class SshGetter(GenericCommandGetter):
    prompt = r'\$'
    pool = TransportPool()

    def __init__(self, *args, **kwargs):
        super(SshGetter, self).__init__(*args, **kwargs)

    def _get_transport_instance(self):
        """
        Open SSH connection to host
        """

        self.conf.log.info('creating connection %s:%s' % (self.host.ip, self.host.port))
        tn_and_chan = self.pool.get((self.host.ip, self.host.port))
        if tn_and_chan and tn_and_chan[0].active:
            self.tn = tn_and_chan[0]
            self.chan = tn_and_chan[1]
            self.conf.log.info('Got instance from pool.')
            self.instance_from_pool = True
        else:
            self.instance_from_pool = False
            self.conf.log.info("Pool doesn't have usable instance. Creating a new one.")
            try:
                self.conf.log.debug('new transport')
                self.tn = paramiko.Transport((self.host.ip, int(self.host.port)))
            except paramiko.SSHException as e:
                msg = "SSHException: %s" % e
                self.conf.log.critical(msg)
                raise GetException(msg)

            except socket.timeout:
                msg = 'Timeout for %s!' % self.host.name
                self.conf.log.critical(msg)
                raise GetException(msg)

            except socket.error as e:
                msg = 'Socket error for %s: %s' % (self.host.name, e)
                self.conf.log.critical(msg)
                raise GetException(msg)

        return self.tn

    def _close_transport_instance(self, tn):
        self.conf.log.debug('Putting back instance %s into the pool' % type(tn))
        self.pool[(self.host.ip, self.host.port)] = (self.tn, self.chan)
        # tn.chan.close()
        # tn.t.close()

    def read_until(self, match):
        """
        Receives from channel until match is found as terminating string
        of the received text.
        """
        out = ''
        reg = re.compile(r'%s\s+?$' % match)
        try:
            while True:
                resp = self.chan.recv(32768).decode('utf-8', 'ignore')
                out += resp
                if reg.search(out):
                    return out
        except socket.timeout:
            msg = 'Timeout waiting for "%s"!' % match
            self.conf.log.critical(msg)
            self.conf.log.debug('received until now: [%s]' % out)
            raise Exception(msg)

    def _exec_command(self, command):
        """
        Issue a command and return its output
        """
        self.conf.log.info('!!!!!!!!!!!!!!!!!!!!!_SSHGETTER_exec_command')
        full_command = 'swmml -n %s -e %s' % (self.current_instance, command)
        self.conf.log.info('sending "%s"' % full_command)
        self.chan.send(full_command + '\n')
        self.conf.log.info('Command sent. Waiting before reading output...')
        time.sleep(2)
        output = self.read_until(self.prompt)
        self.conf.log.info('received %d lines' % len(output.splitlines()))
        self.conf.log.debug('output: [%s]' % output)
        self.got_command_output(command, output)
        return output

    def _change_to_instance(self, instance):
        self.current_instance = instance

    def _authenticate(self):
        if not self.instance_from_pool:
            self.conf.log.debug('connect...')
            self.tn.connect(username=self.host.ssh_usr, password=self.host.ssh_pwd)

            self.conf.log.debug('new channel')
            self.chan = self.tn.open_session()
            self.chan.get_pty()
            self.chan.invoke_shell()
            self.chan.settimeout(30000)

            # self.log.debug('receiving header...')
            # response = self.chan.recv(5000)
            # self.log.debug('header: [%s]' % response)

            self.conf.log.debug('receiving prompt...')
            response = self.chan.recv(1000)
            self.conf.log.debug('response: [%s]' % response)
            self.conf.log.info('connected to %s' % self.host.name)
            self.read_until(self.prompt)
            self.conf.log.info('got prompt %s' % self.host.name)

    @staticmethod
    def clear_pool():
        for tn_and_chan in SshGetter.pool.values():
            tn_and_chan[0].close()


class SshSonusGetter(SshGetter):

    def __init__(self, *args, **kwargs):
        super(SshSonusGetter, self).__init__(*args, **kwargs)

    def got_command_output(self, cmd, output):
        pass

    def _exec_command(self, command):
        """
        Issue a command and return its output
        """
        self.conf.log.info('*****************_STARTING_ SSHSONUS_GETTER_ EXEC_COMMAND')
        self.conf.log.info('switching instance %s' % self.current_instance)
        self.chan.send('select target instance %s\n' % self.current_instance)
        self.prompt = '%s>' % self.current_instance
        self.read_until(self.prompt)

        self.conf.log.info('sending "%s"' % command)
        self.chan.send(command + '\n')
        self.conf.log.info('Command sent. Waiting before reading output...')
        time.sleep(2)
        output = self.read_until(self.prompt)
        self.conf.log.info('received %d lines' % len(output.splitlines()))
        self.conf.log.debug('output: [%s]' % output)
        self.got_command_output(command, output)
        return output

    def _change_to_instance(self, instance):
        self.current_instance = instance

    def _authenticate(self):
        if not self.instance_from_pool:
            self.conf.log.debug('connect to %s@%s:%s...' % (self.host.ssh_usr, self.host.ip, self.host.port))
            self.tn.connect(username=self.host.ssh_usr, password=self.host.ssh_pwd)

            self.conf.log.debug('new channel')
            self.chan = self.tn.open_session()
            self.chan.get_pty()
            self.chan.invoke_shell()
            self.chan.settimeout(30000)

            self.conf.log.debug('receiving prompt...')
            response = self.chan.recv(1000)
            self.conf.log.debug('response: [%s]' % response)
            self.conf.log.info('connected to %s' % self.host.name)
            r = self.read_until(self.conf.read_until)
            self.conf.log.debug('prompt: %s' % r)
            self.conf.log.info('got prompt %s' % self.host.name)

            self.chan.send('ssh ndml@localhost -p 8122\n')
            self.read_until('assword:')
            send_pass = self.conf.send_pass + "\n"
            self.chan.send(send_pass)
            self.read_until('>')

            self.conf.log.info('switching env (port 8122)')


class GenericFileGetter:
    def get(self):
        raise NotImplementedError()


class SftpFileGetter(GenericFileGetter):
    def __init__(self, conf, host, report):
        """
        * prompt_usr: username prompt
        * prompt_pwd: password prompt
        * prompt_cmd: normal prompt after a command
        """
        self.conf = conf
        self.host = host
        self.report = report

        # Context info to include in all logging messages
        self.context = '%s/%s' % (self.host.name, self.report.name)

    def _choose_file_to_download(self, files_available):
        dates = []
        files_available = fnmatch.filter(files_available, 'TrunkGroup-*-*-*-*-*.csv')
        files_available.sort()
        self.conf.log.info('Files available = %s' % files_available)

        if len(files_available) >= 2:  # See explanation above
            for file_available in files_available:
                name, ext = os.path.splitext(file_available)
                (trunkgroup, year, month, day, hour, minute) = name.split('-')
                dates.append(datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute)))

            dates.sort()
            latest_date = dates[-1]
            # Yves & Lukasz switched it to the last date, as reports are generated daily, not hourly anymore
            # old assumption:
            # # getting the latest was bringing us problems with incomplete files! Sonus should guarantee that the file
            # # is complete when it is there, but looks like this isn't the case. then, I am using not the latest one,
            # # but the one before, as it is hourly generated it is not a problem.

            chosen_file = 'TrunkGroup-%d-%d-%d-%d-%d.csv' % (
                latest_date.year, latest_date.month, latest_date.day, latest_date.hour, latest_date.minute
            )
            self.conf.log.info('Chosen file = %s' % chosen_file)
            if chosen_file not in files_available:
                self.conf.log.error(
                    'Chosen file somehow is not in the list of files available. There is an error in the code.'
                )
            return chosen_file
        else:
            self.conf.log.info('No file available to download!')
            return None

    def _download_archive(self, files_available):
        dates = []
        files_available = fnmatch.filter(files_available, f'{self.report.file_name}_*.zip')
        files_available.sort()
        if len(files_available) >= 1:
            for file_available in files_available:
                name, ext = os.path.splitext(file_available)
                file_date = name.split("_")[-1]
                if len(file_date) == 8:
                    year, month, day = file_date[:4], file_date[4:6], file_date[6:8]
                    dates.append(datetime(year=int(year), month=int(month), day=int(day)))
                else:
                    self.conf.log.info('File date has wrong type!')
                    return None

            dates.sort()
            latest_date = dates[-1]
            chosen_file = f'{self.report.file_name}_%d%d%d.zip' % (latest_date.year, latest_date.month, latest_date.day)
            self.conf.log.info('Chosen file = %s' % chosen_file)
            if chosen_file not in files_available:
                self.conf.log.error(
                    'Chosen file somehow is not in the list of files available. There is an error in the code.'
                )
            return chosen_file
        else:
            self.conf.log.info('No file available to download!')
            return None

    def get(self):
        try:
            t = paramiko.Transport((self.host.ip, int(self.host.port)))
            t.connect(username=self.host.ssh_usr, password=self.host.ssh_pwd)
            sftp = paramiko.SFTP.from_transport(t)

            file_to_download = self._download_archive(sftp.listdir(self.report.path))

            if file_to_download and file_to_download.split(".")[-1] == "zip":
                remote_abspath = self.report.path + file_to_download
                self.conf.log.info('File chosen to download stat = %s' % sftp.stat(remote_abspath))

                zip_file = self.conf.zip_file_name(file_to_download)

                self.conf.log.info('Downloading file %s to %s' % (remote_abspath, zip_file))

                sftp.get(remote_abspath, self.conf.zip_file_name(file_to_download))
                self.conf.log.info('File %s downloaded - Local size = %d' % (remote_abspath, os.path.getsize(zip_file)))

            elif file_to_download and file_to_download.split(".")[-1] == "raw":
                remote_abspath = self.report.path + '/' + file_to_download
                self.conf.log.info('File chosen to download stat = %s' % sftp.stat(remote_abspath))

                self.conf.log.info(
                    'Downloading file %s to %s' % (
                        remote_abspath, self.conf.raw_file_name(self.host, self.report)
                    )
                )

                sftp.get(remote_abspath, self.conf.raw_file_name(self.host, self.report))
                self.conf.log.info(
                    'File %s downloaded - Local size = %d' % (
                        remote_abspath, os.path.getsize(self.conf.raw_file_name(self.host, self.report))
                    )
                )
            else:
                self.conf.log.info('No file to download')

            t.close()

        except paramiko.SSHException as e:
            msg = '%s: ssh error: %s' % (self.context, e)
            self.conf.log.error(msg)
            raise GetException(msg)
        except socket.error as e:
            msg = '%s: socket error: %s' % (self.context, e[1])
            self.conf.log.error(msg)
            raise GetException(msg)
        except IOError as e:
            msg = '%s: IOError: %s' % (self.context, e)
            self.conf.log.error(msg)
            raise GetException(msg)


class MultipleCommandsSshGetter(SshSonusGetter):
    def __init__(self, conf, host, report):
        SshSonusGetter.__init__(self, conf, host, report)
        self.commands_and_levels = [(self.commands_and_regexps[0][0], 0)]
        self.current_level = -1

    def get_commands(self):
        self.conf.log.info('!!!!!!!!!!!!!!!!!!STARTING GET_COMMANDS........')
        for command, level in self.commands_and_levels:
            self.current_level = level
            self.conf.log.info('level is %s' % level)
            self.conf.log.info('the command is %s' % command)
            yield command

   # def got_command_output(self, cmd, output):
   #     if 0 <= self.current_level < len(self.commands_and_regexps)-1:
   #         matches = list(re.finditer(self.commands_and_regexps[self.current_level][1], output, re.MULTILINE | re.DOTALL))
   #         for match in matches:
   #             new_command = self.commands_and_regexps[self.current_level+1][0] % match.groupdict()
   #             self.commands_and_levels.append((new_command, self.current_level+1))

    def got_command_output(self, cmd, output):
        self.conf.log.info('************************* STARTING got_command_output*********************************')
        commandlenght = len(self.commands_and_regexps)
        self.conf.log.info('commandlenght is %d' % commandlenght)
        if 0 <= self.current_level < commandlenght-1:
            matches = list(re.finditer(self.commands_and_regexps[self.current_level][1], output, re.MULTILINE | re.DOTALL))
            self.conf.log.info('commandlenght is %d' % commandlenght)
            #  self.conf.log.info('matches is [s%]' % matches)
            for match in matches:
                new_command = self.commands_and_regexps[self.current_level+1][0] % match.groupdict()
                self.conf.log.info('new_command is %s' % new_command)
                self.commands_and_levels.append((new_command, self.current_level+1))


class IpSignalingPeerGroupGetter(MultipleCommandsSshGetter):
    commands_and_regexps = [
        ('find Ip_Signaling_Peer_Group', r'Ip_Signaling_Peer_Group_Id:\s*(?P<Ip_Signaling_Peer_Group_Id>\S+)'),
        ('show Ip_Signaling_Peer_Group Ip_Signaling_Peer_Group_Id %(Ip_Signaling_Peer_Group_Id)s', r'Not used'),
    ]


class IpSignalingPeerGroupDataGetter(MultipleCommandsSshGetter):
    commands_and_regexps = [
        ('find Ip_Signaling_Peer_Group', r'Ip_Signaling_Peer_Group_Id:\s*(?P<Ip_Signaling_Peer_Group_Id>\S+)'),
        ('find Ip_Signaling_Peer_Group_Data Ip_Signaling_Peer_Group_Id %(Ip_Signaling_Peer_Group_Id)s', r'''Ip_Signaling_Peer_Group_Id:\s*(?P<Ip_Signaling_Peer_Group_Id>\S+)\s*
\s*Sequence_Number\s*:\s*(?P<Sequence_Number>\d+)'''),
        ('show Ip_Signaling_Peer_Group_Data Ip_Signaling_Peer_Group_Id %(Ip_Signaling_Peer_Group_Id)s Sequence_Number %(Sequence_Number)s', r'Not used'),
    ]


class PacketServiceProfileGetter(MultipleCommandsSshGetter):
    commands_and_regexps = [
        ('find packet_service_profile', r'Packet_Service_Profile_Id:\s*(?P<Packet_Service_Profile_Id>\S+)'),
        ('show packet_service_profile packet_service_profile_id %(Packet_Service_Profile_Id)s', r'Not used'),
    ]


class CodecEntryGetter(MultipleCommandsSshGetter):
    commands_and_regexps = [
        ('find codec_entry', r'Codec_Entry_Id:\s*(?P<Codec_Entry_Id>\S+)'),
        ('show codec_entry codec_entry_id %(Codec_Entry_Id)s', r'Not used'),
    ]


class IPSignalingProfileGetter(MultipleCommandsSshGetter):
    commands_and_regexps = [
        ('find ip_signaling_profile', r'Ip_Signaling_Profile_Id:\s*(?P<Ip_Signaling_Profile_Id>\S+)'),
        ('show ip_signaling_profile ip_signaling_profile_id %(Ip_Signaling_Profile_Id)s', r'Not used'),
    ]


class InstantiationException(Exception):
    pass


def new(class_name, *args, **kwargs):
    """
    Returns an instance of class: class_name (string).
    Raises InstantiationException if class_name does not match
    a defined class in the local scope.
    """
    try:
        the_class = None
        for part in class_name.split('.'):
            if the_class is None:
                the_class = globals()[part]
            else:
                the_class = the_class.__dict__[part]

        return the_class(*args, **kwargs)
    except KeyError:
        raise InstantiationException('no such class: %s' % class_name)
    except TypeError as e:
        raise InstantiationException('%s: TypeError: %s' % (class_name, str(e)))


class Arguments:
    def __init__(self):
        self.p = OptionParser(usage='usage: %prog [options]')
        self.p.add_option('-c', '--config', action='store',  help='config file for the script', type='string', dest='conf_file')
        self.p.add_option('-o', '--host',   action='append', help='host from which to extract the reports, option can be repeated for multiple hosts. If not specified: all hosts for the specified report(s).', type='string', default=[])
        self.p.add_option('-r', '--report', action='append', help='reports to extract from the host(s), can be repeated. If not specified, extracts all reports in the active_reports config file variable.', type='string', default=[])

    def get_arguments(self):
        (self.opt, self.args) = self.p.parse_args()

        if len(self.args) > 0:
            self.p.error('incorrect number of arguments (remains: %s)' % str(self.args))

        if not self.opt.conf_file:
            self.p.error('please specify the configuration file (--config)')

    def __getattr__(self, attr):
        return getattr(self.opt, attr)


def cleanup():
    SshGetter.clear_pool()


def main():
    args = Arguments()
    args.get_arguments()

    conf = Config(args.conf_file, 'getter')

    # If only one report specified, create pid file specific to this report
    # so other instances of the same script are allowed to run in parallel
    # for other reports.
    if len(args.report) == 1:
        conf.makePid(label=args.report[0])
    else:
        conf.makePid()

    conf.log.info('Get report starting')

    try:
        for report in conf.iter_reports(args.report):
            for host in report.iter_hosts(args.host):

                try:
                    getter = new(report.getter, conf, host, report)
                    conf.log.info("Waiting before creating new connection...")
                    time.sleep(5)
                    getter.get()

                except GetException as e:
                    if conf.devmode:
                        raise e
                    else:
                        conf.log.exception('GetException! Logging and continuing!')
                except Exception as e:
                    conf.log.exception('Getter exception that is not GetException! Exiting!')
                    raise e

    finally:
        conf.delPid()
        conf.log.info('All done')
        cleanup()


if __name__ == '__main__':
    main()
