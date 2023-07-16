class ParseException(Exception):
class ParseException(Exception):
    pass


class ExportException(ParseException):
    """
    More specific parsing exception, for problems detected 
    during the export of the data
    """
    pass
