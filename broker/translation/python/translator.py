import json
from token import ENDMARKER, INDENT, DEDENT, NEWLINE, NAME, NUMBER, OP, STRING
from tokenize import TokenInfo, NL
import tokenize
import token
from io import BytesIO
import os

from .verb import Verb, parse_documentation

__author__ = 'nibo'
script_dir = os.path.dirname(__file__)

core_language = [os.path.join(script_dir, "system.json"), os.path.join(script_dir, "internal.json")]

class ProcessTokens(object):
    """
    This class hold the list of tokens output by tokenize, used when parsing
    """

    _items = None
    # A list of keywords used to resolve python keywords and structures
    keywords = None

    # A list of definitions used to resolve function definitions
    definitions = None

    # A dict of aliases; "alias" : "namespace.functionname"
    aliases = None
    # The encoding of the file
    encoding = None

    # The documentation of the file
    documentation = None

    # The current position
    position = None

    # A position/verb-map, used to generate a line/doc-map
    position_map = None

    # The non-local namespaces referred to by the process
    namespaces = None

    # The parsed tokens
    tokens = None

    def __init__(self, _token_list=None, _keywords=None, _definitions=None):
        if _keywords:
            self.keywords = _keywords
        else:
            self.keywords = self.load_keywords()

        if _definitions:
            self.definitions = _definitions

        if _token_list:
            self._items = _token_list
            self.position = 0

        self.position_map = {}
        self.namespaces = []


    def first(self):
        """
        Returns the first item
        :return the first token:
        """
        if self._items or len(self._items) == 0:
            return None
        else:
            return self._items[0]

    def next(self):
        """
        Returns the next item
        :return the next token:
        """
        self.position += 1
        if self.position < len(self._items):
            return self._items[self.position]
        else:
            return None

    def add(self, _item):
        """
        Add an item
        :param _item:
        :return:
        """
        self._items.push(_item)
        self.position += 1

    def __iter__(self):
        return self._items

    def __getitem__(self, index):
        self.position = index
        return self._items[index]

    def save(self, _filename):
        """
        Save the data
        :param _filename:
        :return:
        """
        with open(_filename, "w") as _file:
            _file.write(tokenize.untokenize(self._items))
        raise Exception("ProcessTokens.save is not yet implemented")

    def parse_file(self, _filename):
        """
        Parse a file into verbs
        :param _filename:
        :return:
        """
        # Load all tokens
        with open(_filename, "r", encoding="utf-8") as _file:
            _tokens = tokenize.tokenize(BytesIO(_file.read().encode('utf-8')).readline)
        self._items = []

        for _token in _tokens:
            self._items.append(_token)

        if len(self._items) == 0:
            raise Exception("The file " + _filename + " doesn't have any content.")

        self.position = -1

        _token = self.next()

        # First load encoding
        self.encoding = _token[1]

        _token = self.next()
        if _token:
            # Then load process documentation
            _token, self.documentation = parse_documentation(_token, self)
        else:
            return []

        _verbs = []

        while _token and _token[0] != token.ENDMARKER:
            _verb = Verb()
            print("parsing " + str(_token))
            _token = _verb.from_tokens(_token=_token, _process_tokens=self)
            print("parsed " + str(_verb))
            _verbs.append(_verb)

        return _verbs

    def encode_process(self, _verbs, _filename):
        """
        This function converts all verbs to tokens, untokenizes them and writes to an output file

        : _verbs A list of verbs
        : _filename Output filename
        """

        # Init the line map and
        _line_map = {}

        # First tokenize the file documentation
        if self.documentation:
            self.tokens = [[59, 'utf-8', [0, 0], [0, 0], ''], [STRING, '"""' + self.documentation + '"""'], [NEWLINE, "\n"]]
            # add the documentation mapping
            _line_map[1] = {"identifier": "file", "documentation": self.documentation}

        else:
            self.tokens = [[59, 'utf-8', [0, 0], [0, 0], '']]

        # Loop all verbs
        for _verb in _verbs:
            print(_verb.identifier)
            _verb.to_tokens(self)

        # For some reason the last command should not be ended with a newline...
        if self.tokens[-1][0] == NEWLINE:
            self.tokens.pop()
        self.tokens.append([ENDMARKER, ""])

        # We will ignore the zeroth row, it is the encoding token which is not included as part of the text content
        # but as a part of the the tokenizers tokenization process. I.E. not round trip.
        _curr_row = 1
        _curr_col = 0
        _indents = 0
        _indent_length = 4

        # Loop all tokens to and fill out the data needed make them work as part of a larger set of tokens and
        # satisfy the tokenizer with proper TokenInfo instances.
        for _curr_token_idx in range(1, len(self.tokens)):
            _curr_token = self.tokens[_curr_token_idx]

            # Handle indents and dedents
            if _curr_token[0] == INDENT:
                _indents += 1
            elif _curr_token[0] == DEDENT:
                _indents -= 1

            _curr_value = _curr_token[1]

            # If its not the first thing on a line, It might need to be preceeded by a space
            if _curr_col - (_indent_length * _indents) > 0:
                # Its a textual token, and not the first on the row
                if _curr_token[0] in [NAME, NUMBER, STRING] and _curr_token_idx > 0:
                    # Add space if not preceeded by these
                    if self.tokens[_curr_token_idx - 1][1] not in [".", "(", '"""']:
                        _curr_col += 1
                # Add space if it is an operator and not one of these
                if (_curr_token[0] in [OP]) and (_curr_token[1] not in [".", ")", ",", "(", ":"]):
                    _curr_col += 1
                # Then there should be no indent string
                _curr_indent_string = ""
            else:
                # It it is the first thing, add indent string
                _curr_indent_string = (" " * (_indent_length * _indents))

            # The commands has only one row
            if _curr_token[0] in [NEWLINE, NL, DEDENT, INDENT]:
                _rows = [_curr_token[1]]
                # Indents gets the entire row as value, so they has to be reset to just an indent.
                if _curr_token[0] == INDENT:
                    _curr_value = " " * _indent_length
                    # it *is* the indent string, so don't add it
                    _curr_indent_string = ""
            else:
                # Only non-commands should be checked for multiline strings
                _rows = str.split(_curr_value, "\n")

            # Add number of rows or value, it might be multiline
            _end_row = _curr_row + len(_rows) - 1

            # Special rules applies to DEDENT, it has to have zero columns
            if _curr_token[0] in [DEDENT]:
                # Set end row as that will be passed on to the next token.
                _end_col = _indent_length * _indents
                self.tokens[_curr_token_idx] = TokenInfo(type=_curr_token[0], string=_curr_value,
                                                     start=(_curr_row, 0), end=(_end_row, 0),
                                                     line=_curr_indent_string + _curr_value)
            else:
                # Always set NL to starting in 0
                if _curr_token[0] == NL and self.tokens[_curr_token_idx - 1][0] in [NEWLINE, NL]:
                    _curr_value = "\n"
                    _curr_col = 0
                    _end_col = 1
                elif _end_row > _curr_row:
                    # It is multiline, end column should be fetched from last row
                    _end_col = _indent_length * _indents + len(_rows[-1])
                else:
                    # Add the length of the current line to the current end column
                    _end_col = _curr_col + len(_curr_indent_string + _curr_value)
                if _curr_token_idx in self.position_map:
                    _line_map[_curr_row] = self.position_map[_curr_token_idx]

                # Create the TokenInfo instance
                self.tokens[_curr_token_idx] = TokenInfo(type=_curr_token[0], string=_curr_value,
                                                     start=(_curr_row, _curr_col), end=(_end_row, _end_col),
                                                     line=_curr_indent_string + _curr_value)

            # Pass on to the next token
            _curr_row = _end_row
            _curr_col = _end_col

            # NEWLINE or NL?
            if _curr_token[0] in [NEWLINE, NL]:
                # Reset indents
                _curr_col = _indent_length * _indents
                # Goto next row
                _curr_row += 1

        # Write the result to the file
        with open(_filename, "w", encoding="utf-8") as _file:
            _string = tokenize.untokenize(self.tokens)
            _file.write(_string.decode('utf-8'))

        return self.namespaces, _line_map

    @staticmethod
    def load_keywords():
        """
        Load keywords
        :return:
        """
        with open(os.path.join(script_dir, "keywords.json"), "r") as _file:
            return json.load(_file)


    @staticmethod
    def verbs_to_json(_verbs):
        """
        Converts a list of verbs to a JSON-style dictionary
        :param _verbs: The list of verbs
        :return: A JSON-style dictionary
        """
        _result = []
        for _curr_verb in _verbs:
            _result.append(_curr_verb.to_json())
        return _result

    @staticmethod
    def json_to_verbs(_json):
        """
        Converts a JSON-style dictionary to a list of verbs
        :param _json: A JSON-style dictionary
        :return: A list of verbs
        """
        _result = []

        for _curr_verb in _json:
            _result.append(Verb.from_json(_curr_verb))

        return _result


    def add_to_namespaces(self, _identifier):
        """
        Parses the namespace from identifier and adds it to namespaces if not present
        :param _identifier: The identifier
        :return:
        """
        _identifier_parts = _identifier.split(".")
        if len(_identifier_parts) > 1:
            if _identifier_parts[0] not in self.namespaces:
                self.namespaces.append(_identifier_parts[0])


    def add_verb_to_position_map(self, _verb):
        """
        Adds a mapping to the map for the next position
        :param _verb: The verb to map
        """
        if _verb.documentation:
            self.position_map[len(self.tokens)] = {"identifier": _verb.identifier, "documentation": _verb.documentation}
        else:
            self.position_map[len(self.tokens)] = {"identifier": _verb.identifier, "documentation": "Undocumented"}

