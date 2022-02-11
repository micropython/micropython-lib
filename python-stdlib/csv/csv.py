# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Alec Delaney
#
# SPDX-License-Identifier: MIT
"""
`csv`
================================================================================

Library for working with CSV files

* Author(s): Alec Delaney
"""

import re


class reader:
    """Basic CSV reader class that behaves like CPython's ``csv.reader()``

    :param csvfile: The open file to read from
    :type csvfile: io.TextIOWrapper
    :param str delimiter: (Optional) The CSV delimiter, default is comma (,)
    :param str quotechar: (Optional) The CSV quote character for encapsulating special characters
        including the delimiter, default is double quotation mark (")
    """

    def __init__(
        self, csvfile, delimiter = ",", quotechar = '"'
    ) -> None:

        self.file_interator = csvfile
        self.delimiter = delimiter
        self.quotechar = quotechar
        self._re_exp = "(\\{0}.+?\\{0}),|([^{1}]+)".format(quotechar, delimiter)

    def __iter__(self):
        return self

    def __next__(self):
        csv_value_list = []
        row_string = self.file_interator.__next__()

        while len(row_string) != 0:
            if row_string.startswith(self.delimiter):
                csv_value_list.append("")
                row_string = row_string[1:]
                continue

            next_match = re.match(self._re_exp, row_string)
            matches = next_match.groups()
            if matches[0] is None:
                latest_match = matches[1].strip("\r\n").strip("\n")
                csv_value_list.append(
                    latest_match.replace(self.quotechar * 2, self.quotechar)
                )
            else:
                latest_match = matches[0].strip("\r\n").strip("\n")
                csv_value_list.append(
                    latest_match[1:-1].replace(self.quotechar * 2, self.quotechar)
                )

            if len(row_string) != 0:  # If anything is left in the list...
                row_string = row_string[len(latest_match) :]
                if row_string == self.delimiter:
                    csv_value_list.append("")
                    row_string = row_string[1:]
                elif (
                    row_string == "\r\n"
                    or row_string == "n"
                ):
                    row_string = ""
                row_string = row_string[1:]

        return csv_value_list


class writer:
    """Basic CSV writer class that behaves like CPython's ``csv.writer()``

    :param csvfile: The open CSVfile to write to
    :type csvfile: io.TextIOWrapper
    :param str delimiter: (Optional) The CSV delimiter, default is comma (,)
    :param str quotechar: (Optional) The CSV quote character for encapsulating special characters
        including the delimiter, default is double quotation mark (")
    """

    def __init__(
        self, csvfile, delimiter = ",", quoterchar = '"'
    ):

        self.file_iterator = csvfile
        self.delimiter = delimiter
        self.quotechar = quoterchar
        self.newlinechar = "\r\n"

    def writerow(self, seq):
        """Write a row to the CSV file

        :param seq: The list of values to write, which must all be str or be able to
            be cast to str
        :type seq: Sequence[Any]
        """

        str_seq = [str(entry) for entry in seq]
        doub_quote_seq = [
            entry.replace(self.quotechar, self.quotechar * 2) for entry in str_seq
        ]
        quoted_seq = [self._apply_quotes(entry) for entry in doub_quote_seq]
        parsed_str = (self.delimiter).join(quoted_seq)
        self.file_iterator.write(parsed_str + self.newlinechar)

    def writerows(self, rows):
        """Write multiple rows to the CSV file

        :param rows: An iterable item that yields multiple rows to write (e.g., list)
        :type rows: Iterable[Sequence[Any]]
        """
        for row in rows:
            self.writerow(row)

    def _apply_quotes(self, entry):
        """Apply the quote character to entries as necessary

        :param str entry: The entry to add the quote charcter to, if needed
        """

        return (
            (self.quotechar + entry + self.quotechar)
            if self.delimiter in entry
            else entry
        )


# Ported from CPython's csv.py:
class DictReader:
    """CSV reader that maps rows to a dict according to given or inferred fieldnames,
    it also accepts the delimiter and quotechar keywords

    :param f: The open file to read from
    :type f: io.TextIOWrapper
    :param fieldnames: (Optional) The fieldnames for each of the columns, if none is given,
        it will default to the whatever is in the first row of the CSV file
    :type fieldnames: Sequence[str]
    :param str restkey: (Optional) A key name for values that have no key (row is larger than
        the length of fieldnames), default is None
    :param restval: (Optional) A default value for keys that have no values (row is small
        than the length of fieldnames, default is None
    :type restval: Any
    """

    def __init__(
        self,
        f,
        fieldnames = None,
        restkey = None,
        restval = None,
        **kwargs
    ):

        self.fieldnames = fieldnames
        self.restkey = restkey
        self.restval = restval
        self.reader = reader(f, **kwargs)
        self.line_num = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.line_num == 0:
            if self.fieldnames is None:
                self.fieldnames = next(self.reader)
        row = next(self.reader)

        row_dict = dict(zip(self.fieldnames, row))
        length_fn = len(self.fieldnames)
        length_row = len(row)
        if length_fn < length_row:
            row_dict[self.restkey] = row[length_fn:]
        elif length_fn > length_row:
            for key in self.fieldnames[length_row:]:
                row_dict[key] = self.restval
        self.line_num += 1
        return row_dict


# Ported from CPython's csv.py
class DictWriter:
    """CSV writer that uses a dict to write the rows according fieldnames, it also accepts the
    delimiter and quotechar keywords

    :param f: The open file to write to
    :type f: io.TextIOWrapper
    :param fieldnames: The fieldnames for each of the comlumns
    :type fieldnames: Sequence[str]
    :param str restval: A default value for keys that have no values
    :param str extrasaction: The action to perform if a key is encountered when parsing the dict
        that is not included in the fieldnames parameter, either "raise" or "ignore".  Ignore
        raises a ValueError, and "ignore" simply ignore that key/value pair.  Default behavior
        is "raise"
    """

    def __init__(
        self,
        f,
        fieldnames,
        restval = "",
        extrasaction = "raise",
        **kwargs
    ):
        self.fieldnames = fieldnames  # list of keys for the dict
        self.restval = restval  # for writing short dicts
        if extrasaction.lower() not in ("raise", "ignore"):
            raise ValueError(
                "extrasaction " "(%s)" " must be 'raise' or 'ignore'" % extrasaction
            )
        self.extrasaction = extrasaction
        self.writer = writer(f, **kwargs)

    def writeheader(self):
        """Writes the header row to the CSV file"""
        self.writerow(dict(zip(self.fieldnames, self.fieldnames)))

    def _dict_to_tuple(self, rowdict):
        if self.extrasaction == "raise":
            wrong_fields = []
            for field in rowdict.keys():
                if field not in self.fieldnames:
                    wrong_fields.append(field)
            if wrong_fields:
                raise ValueError(
                    "dict contains fields not in fieldnames: "
                    + ", ".join([repr(x) for x in wrong_fields])
                )
        return (rowdict.get(key, self.restval) for key in self.fieldnames)

    def writerow(self, rowdict):
        """Writes a row to the CSV file

        :param rowdict: The row to write as a dict, with keys of the DictWriter's
            fieldnames parameter; values must be str or be able to be cast to str
        :type rowdict: Dict[str, Any]
        """
        return self.writer.writerow(self._dict_to_tuple(rowdict))

    def writerows(self, rowdicts):
        """Writes multiple rows to the CSV files

        :param rowdicts: An iterable item that yields multiple rows to write;
            values in those rows must be str or be able to be cast to str
        :type rowdicts: Iterable[Dict[str, Any]]
        """
        return self.writer.writerows(map(self._dict_to_tuple, rowdicts))