from ndml_sonus.scripts.common_exceptions import ParseException
from ndml_sonus.scripts import sonus_logging


class FieldClashException(ParseException):
    pass


class FieldMerger:
    """
    This class is used to merge dicts. If a key clash is detected then warnings are output.
    """
    @staticmethod
    def merge(source, dest):
        log = sonus_logging.log
        possible_clashes = set(source.keys()).intersection(dest.keys())
        real_clash = False

        if len(possible_clashes) != 0:
            for possible_clash in possible_clashes:
                if source[possible_clash] != dest[possible_clash]:
                    log.critical('Field %s clashes' % possible_clash)
                    log.critical('Value in source = %s' % source[possible_clash])
                    log.critical('Value in destination = %s' % dest[possible_clash])
                    real_clash = True
                else:
                    log.debug('Field %s repeats in the report with value %s.' % (possible_clash, dest[possible_clash]))

            if real_clash:
                log.critical('One or more field clashes happened')
                log.critical('source = %s, dest = %s' % (source, dest))
                raise FieldClashException()
            else:
                dest.update(source)
        else:
            dest.update(source)
