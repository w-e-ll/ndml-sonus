#!/bin/env python
import re

from ndml_sonus.scripts.field_merger import FieldMerger

# Separators are simple objects that are used to separate one or more lines 
# from a report into a dict with one entry:  {'name: 'value'}.
# name is the name of a parameter being represented on the report (like 
# the ip address of a network element). Usually the report has 
# FieldName : FieldValue
# but that is not always the case. Each of the classes here know how to separate
# the name from the value.

# For more details about what kind of output the class is able to separate, see
# comment above the class definition


# Start Separators
class AbstractSeparator:
    def separate(self, text):
        raise NotImplementedError()
    
    def matches(self, text):
        raise NotImplementedError()
    

class RegexSeparator(AbstractSeparator):
    def __init__(self, regex):
        self.separator_regex = re.compile(regex)
        
    def separate(self, text):

        return self.separator_regex.match(text).groupdict()
    
    def matches(self, text):
        return self.separator_regex.match(text)


class FullTextRegexSeparator(AbstractSeparator):
    def __init__(self, regex, mode=re.DOTALL):
        self.separator_regex = re.compile(regex, mode)
        self.regex_str = regex
        
    def separate(self, text):
        for match in self.separator_regex.finditer(text):
            yield match.groupdict()
    
    def matches(self, text):
        return len(self.separator_regex.findall(text)) > 0


class SingleColumnSeparator(AbstractSeparator):
    """
    SingleColumnSeparator is probably the most important separator. Most of the
    parameter definitions are just something in the form:
    FieldName : FieldValue
    but this class can also deal with many other cases like
    FieldName : FieldValue1 FieldValue2 with spaces
    FieldName :      FieldValue, with starting or trailing spaces
    FieldName:FieldValue (without spaces after the comma)
    All these cases appear. If you modify this class, make sure to keep this
    behavior working.
    """
    def separate(self, line):
        name, value = [s.strip() for s in line.split(':', 1)]
        return {name: value}
    
    def matches(self, line):
        return line.count(': ') == 1

# The same of a simple single column separator, but this one keeps state to
# output nested lines
# Example
# Foo
#    Bar : 1
#    Baz : 2
# this separator will output
# {'Foo Bar' : '1'} and {'Foo Baz' : '2' }
# used in a few reports.


class NestingSingleColumnSeparator(SingleColumnSeparator):
    def __init__(self):
        SingleColumnSeparator.__init__(self)
        self.last_non_nested_line = ' '*50 + 'x'
        self.parent_line = ' '*50 + 'x'

    @staticmethod
    def number_of_whitespaces_in_the_beginning(s1):
        return len(s1.rstrip()) - len(s1.strip())

    def is_line_nested(self, line, parent_line):
        if len(line) > 0:
            result = self.number_of_whitespaces_in_the_beginning(line) > self.number_of_whitespaces_in_the_beginning(parent_line)
        else:
            result = False
        
        return result
    
    def separate(self, line):
        result = SingleColumnSeparator.separate(self, line)
        if self.is_line_nested(line, self.parent_line):
            # print 'Outputting dict with nested key = ' + self.last_non_nested_line + ' ' + result.keys()[0]
            result = {self.last_non_nested_line + ' ' + list(result.keys())[0]: list(result.values())[0]}
            
        return result
        
    def matches(self, line):
        result = SingleColumnSeparator.matches(self, line)
        
        if not self.is_line_nested(line, self.parent_line):
            stripped_line = line.strip()
            if len(stripped_line) > 0:
                if stripped_line[-1] == ':':
                    last_non_nested_line = stripped_line[:-1]
                else:
                    last_non_nested_line = stripped_line
                
                self.last_non_nested_line = last_non_nested_line
                self.parent_line = line
                
        return result


class FixedColumnSeparator(AbstractSeparator):
    """
    This is a separator that can separate lines with more than one parameter
    Example:
    FieldName1 : FieldValue1               FieldName2 : FieldValue2
    this class only separates the columns and passes each part to another
    single-column separator. Also a very important parser, being used in many
    places.
    The single-column separator can be modified with the klass attribute.
    If you don't need nesting in your report, but need to parse many columns, you
    should use the SimpleFixedColumnSeparator, which is much simpler and easier to
    debug.
    """
    klass = NestingSingleColumnSeparator
    
    def __init__(self, columns):
        AbstractSeparator.__init__(self)
        self.columns = columns
        self.separators = [self.klass() for _ in self.columns]
        self.field_merger = FieldMerger()
        
    def separate(self, line):
        result = {}
        
        for idx, column in enumerate(self.columns):
            column_start, column_end = column
            
            if len(line) < column_end:
                column_end = len(line)
            
            partial_line = line[column_start: column_end]
            separator = self.separators[idx]
            
            if separator.matches(partial_line):
                new_field = separator.separate(partial_line)
                self.field_merger.merge(new_field, result)
                
        return result
    
    def matches(self, line):
        # return line.count(':') >= len(self.columns)
        return True


class SimpleFixedColumnSeparator(FixedColumnSeparator):
    """
    This is another very important parser. Should be used for multiple columns
    but only if nesting is not needed.
    See comments on base class.
    """

    klass = SingleColumnSeparator
    
    def matches(self, line):
        return len(self.separate(line)) >= len(self.columns)


class NoMatchException(Exception):
    pass


class SpacedValueSeparator(AbstractSeparator):
    """
    I am not sure if this class is being used. Used to separate
    FieldName              FieldValue
    """
    def separate(self, line):
        split_line = line.strip().split('  ')
        
        split_line = [x.strip() for x in split_line if len(x.strip()) != 0]
        
        if len(split_line) == 2:
            return {split_line[0]: split_line[1]}
        else:
            raise NoMatchException()
        
    def matches(self, line):
        try:
            self.separate(line)
            result = True
        except NoMatchException:
            result = False
            
        return result

# I am not sure if this class is being used. Used to separate
# FieldName              FieldValue
# but this one you explicitly say what is the start and end character of the
# name and value.


class NameValueInTwoColumnsSeparator(AbstractSeparator):
    def __init__(self, name_column, value_column):
        self.name_column = name_column
        self.value_comumn = value_column
    
    def separate(self, line):
        name_column_start,  name_column_end = self.name_column
        value_column_start, value_column_end = self.value_comumn
        
        name = line[name_column_start:  name_column_end].strip()
        value = line[value_column_start: value_column_end].strip()

        return {name: value}
    
    def matches(self, line):
        return len(self.separate(line).keys()[0]) > 0


class CompositeSeparator(AbstractSeparator):
    """
    A separator that contains another separator.
    Used to parse reports with hierarchical data
    Example
    Foobar FieldValue1
       FoobarChild FieldValue2
       FoobarChild FieldValue3
       FoobarChild FieldValue4
    To use this separator, you need to provide the parent separator, a child
    separator and the field name that will be "piped" from the parent to the child.
    This separator yields many lines. One for each result in the most internal
    separator.

    For the example given above, three dicts are yielded
    FieldValue1, FieldValue2
    FieldValue1, FieldValue3
    FieldValue1, FieldValue4
    The parent separator is considered to be some "global" information, common to
    all child nodes.
    """
    def __init__(self, parent_separator, field_to_pass, child_separator):
        self.parent_separator = parent_separator
        self.field_to_pass = field_to_pass
        self.child_separator = child_separator
        AbstractSeparator.__init__(self)
    
    def separate(self, text):
        global_fields_list = list(self.parent_separator.separate(text))
        
        for global_fields in global_fields_list:
        
            text_to_pass = global_fields.pop(self.field_to_pass)
            child_fields_list = list(self.child_separator.separate(text_to_pass))
            
            for child_fields in child_fields_list:
                global_fields_copy = global_fields.copy()
                global_fields_copy.update(child_fields)
                yield global_fields_copy
    
    def matches(self, text):
        return self.parent_separator.matches(text)

# End Separators
