"""
The verb module contains the Verb class and helper functions
"""
import io
from token import STRING, NEWLINE, NAME, OP, INDENT, DEDENT

import tokenize

__author__ = 'Nicklas Börjesson'


def parse_documentation(_token, _process_tokens):
    """
    Parse a documentation section
    :param _token: The current token
    :param _process_tokens: An instance of the ProcessTokens class
    :return The ending token
    """
    _documentation = ""
    if _token[0] == STRING and _token[1][0:3] == '"""':
        _documentation = _token[1][3:-3]
        _token = _process_tokens.next()
        if _token[0] in [NEWLINE, tokenize.NL]:
            _token = _process_tokens.next()
    elif _token[0] == tokenize.COMMENT:
        while _token[1][0:1] == "#":
            _documentation += _token[1][1:] + "\n"
            _token = _process_tokens.next()
            if _token[0] == tokenize.NL:
                # Skip ending \n
                _token = _process_tokens.next()

    return _token, _documentation


class Verb(object):
    """ A verb is any instruction, assignment, flow control, function call. """

    # The identifier that
    identifier = None

    # The title of the verb type
    type_title = None
    # The verb type
    type = None

    # The title of the verb type
    type_description = None

    # Should be by default expanded
    expanded = None

    # The parameters
    parameters = None

    # Assignments
    assignments = None
    # The operator, if there is an assignment
    assignment_operator = None
    # A list with the order of the assignments
    assignment_order = None

    #: The documentation of the verb
    documentation = None

    # A list of children
    children = None

    # The row on which the verb was found in the source, should be None if any verb has changed
    row = None

    # The raw list of tokens for this verb(only), not set if the verb is changed
    raw = None

    # A list of tokens containing whitespace
    lead_in_whitespace = None

    # The token index where the definition of the verb begins, including whitespace
    _token_begin = None

    # The token index where the definition of the verb ends
    _token_end = None

    # The tree Id of the verb(used by the UI tree)
    id = None

    #: The allowed child types of the verb (used by the UI)
    _allowedChildTypes = None

    # A list with the order of the parameters.
    parameter_order = None

    def __init__(self):
        """
        Initialize the verb and the function map
        """
        self.parameters = {}
        self.assignments = {}
        self.children = []
        self.expanded = False

        self.to_shortcuts = {
            "keyword": self.tokenize_keyword,
            "assign": self.tokenize_assignment,
            "call": self.tokenize_call,
            "documentation": self.tokenize_documentation
        }

    def to_json(self):
        """
        Generate a MBE schemaTree-compatible JSON-style dictionary
        :return A dictionary
        """
        _result = {"id": self.id,
                   "type": self.type,
                   "identifier": self.identifier,
                   "type_title": self.type_title,
                   "type_description": self.type_description,
                   "parameters": self.parameters,
                   "assignments": self.assignments,
                   "assignment_operator": self.assignment_operator,
                   "assignment_order": self.assignment_order,
                   "children": [_curr_child.to_json() for _curr_child in self.children],
                   "row": self.row,
                   "raw": self.raw,
                   "lead_in_whitespace": self.lead_in_whitespace,
                   "token_begin": self._token_begin,
                   "token_end": self._token_end,
                   "allowedChildTypes": self._allowedChildTypes,
                   "expanded": self.expanded,
                   "documentation": self.documentation,
                   "parameter_order": self.parameter_order}
        return _result

    @staticmethod
    def from_json(_json):
        """
        Populate from a JSON-style dictionary
        :param _json A JSON-style dictionary
        :return A populated Verb instance
        """
        _result = Verb()
        _result.id = _json["id"]
        _result.type = _json["type"]
        _result.identifier = _json["identifier"]
        _result.type_title = _json["type_title"]
        _result.type_description = _json["type_description"]
        _result.parameters = _json["parameters"]
        _result.assignments = _json["assignments"]
        _result.assignment_operator = _json["assignment_operator"]
        _result.assignment_order = _json["assignment_order"]
        _result.children = [Verb.from_json(_curr_child) for _curr_child in _json["children"]]
        _result.row = _json["row"]
        _result.raw = _json["raw"]
        _result.lead_in_whitespace = _json["lead_in_whitespace"]
        _result._token_begin = _json["token_begin"]
        _result._token_end = _json["token_end"]
        _result._allowedChildTypes = _json["allowedChildTypes"]
        _result.expanded = _json["expanded"]
        _result.documentation = _json["documentation"]
        _result.parameter_order = _json["parameter_order"]
        return _result

    def parse_whitespace(self, _token, _process_tokens):
        """
        Find out if there is any lead-in whitespace, if so, move past and save it in self.lead_in_whitespace

        :param _token: The current token
        :param _process_tokens: An instance of the ProcessTokens class
        :return A tuple with the ending token and the expression
        """
        # Is there some lead-in whitespace?
        self.lead_in_whitespace = []
        while _token[1].strip() == "" and _token[0] != DEDENT:
            self.lead_in_whitespace.append(_token)
            _token = _process_tokens.next()

        return _token

    @staticmethod
    def parse_expression(_token, _process_tokens):
        """
        Extract an expression string from a token list
        :param _token: The current token
        :param _process_tokens: An instance of the ProcessTokens class
        :return The ending token
        """

        # TODO: Check what happens if an expression is nicely formatted over several lines (ORG-104)
        _paren_level = 0
        # Walk through the expression, end if an extra parenthesis, newline or :.
        _expression = ""
        while _token:
            if _token[0] == OP:
                if _token[1] == "(":
                    _paren_level += 1
                elif _token[1] == ")":
                    _paren_level -= 1
                elif _token[1] == ":":
                    # The expression ended with a ;, we must be part of a flow control stmt, handled in caller
                    break
                elif _paren_level == 0 and _token[1] == ",":
                    # A comma in the root level of the expression means the end of that expression.
                    break
            elif _token[0] == NEWLINE:
                # Done
                break

            if _paren_level < 0:
                break

            _expression += _token[1]
            _token = _process_tokens.next()

        return _token, _expression

    def parse_function_call(self, _token, _process_tokens):
        """
        Parse a function call
        :param _token: The current TokenInfo instance
        :param _process_tokens: A list of tokens
        :return The ending token
        """

        # Parse the identifier for information
        _identifier_parts = self.identifier.split(".")
        _namespace = ".".join(_identifier_parts[0:-1])
        _function_name = _identifier_parts[-1]

        # Move past (
        _token = _process_tokens.next()

        try:
            _curr_definition = _process_tokens.definitions[_namespace]["functions"][_function_name]
        except KeyError:
            # Handle calls to undefined functions

            _param_counter = 1
            self.parameter_order = []
            # Loop tokens
            while _token:
                _token, _expression = self.parse_expression(_token, _process_tokens)
                if _token[0] == NAME:
                    _token = _process_tokens.next()
                    if _token[1] == "=":
                        _token = _process_tokens.next()
                        _token, _expression = self.parse_expression(_token, _process_tokens)

                if _token[1] == ")":
                    if _param_counter > 1:
                        self.parameters["parameter_" + str(_param_counter)] = _expression
                        self.parameter_order.append("parameter_" + str(_param_counter))
                    else:
                        self.parameters["parameter"] = _expression
                        self.parameter_order.append("parameter")

                    _token = _process_tokens.next()
                    if _token[0] == NEWLINE:
                        _token = _process_tokens.next()
                    return _token
                else:

                    self.parameters["parameter_" + str(_param_counter)] = _expression
                    self.parameter_order.append("parameter_" + str(_param_counter))
                    _param_counter += 1
                    _token = _process_tokens.next()
            raise Exception("Function definition reached end of file!")

        # Handle call to *defined* functions
        # Parse parameters
        self.parameter_order = []
        for _curr_parameter in _curr_definition["parameters"]:
            if "output" not in _curr_parameter or _curr_parameter["output"] != True:
                # Each parameter is an expression
                _token, _expression = self.parse_expression(_token, _process_tokens)
                self.parameters[_curr_parameter["key"]] = _expression
                self.parameter_order.append(_curr_parameter["key"])
                # Pass any commas or right parenthesis
                _token = _process_tokens.next()

        # Move past ending newline
        if _token[0] == NEWLINE:
            _token = _process_tokens.next()
        return _token

    def parse_block(self, _token, _process_tokens):
        """
        Parse a block

        :param _token: The current token
        :param _process_tokens: A
        :return The ending token
        """
        # This is a new block of code. Recurse

        if _token[0] == OP and _token[1] == ":":
            # Find indent
            _token = _process_tokens.next()
            if _token[0] == tokenize.COMMENT:
                # Add any inline documentation
                _token, _documentation = parse_documentation(_token, _process_tokens)
                if self.documentation:
                    self.documentation += _documentation
                else:
                    self.documentation = _documentation

            if _token[0] == DEDENT:
                self.identifier = "whitespace before dedent"
                return _token
            elif _token[0] == NEWLINE:
                _token = _process_tokens.next()
            else:
                raise Exception("Mismatch: a block \":\" must be followed by a new line: " + str(_token))
            if _token[0] == INDENT:
                _token = _process_tokens.next()

                # Recursively parse into block until verb returns a dedent
                while _token and _token[0] != DEDENT:
                    _verb = Verb()
                    _token = _verb.from_tokens(_token, _process_tokens)
                    self.children.append(_verb)
                return _token
            else:
                raise Exception("Mismatch: a block must have an indent to be a block: " + str(_token))
        else:
            raise Exception("Mismatch: token should be a block: " + str(_token))

    def parse_parameters(self, _token, _process_tokens):
        """
        Parse a parameter
        :param _token: First token
        :param _process_tokens: A Tokens instance
        :return The ending token
        """
        if _token[0] == OP and _token[1] == "(":
            # Find parameters (local names)
            self.parameter_order = []
            _token = _process_tokens.next()
            while _token:
                if _token[0] == NAME:
                    _param_name = _token[1]
                    self.parameter_order.append(_param_name)
                    _token = _process_tokens.next()
                    if _token[1] == "=":
                        _token = _process_tokens.next()
                        _token, _expression = self.parse_expression(_token, _process_tokens)
                        self.parameters[_param_name] = _expression
                    elif _token[1] == ",":
                        self.parameters[_param_name] = ""
                        _token = _process_tokens.next()
                    elif _token[1] == ")":
                        self.parameters[_param_name] = ""
                        break
                    else:
                        raise Exception(
                            "parse_parameters: Unexpected token: " + str(_token[1]) + " - full token: " + str(_token))

                elif _token[1] == ")":
                    break

        # Move past )
        _token = _process_tokens.next()
        return _token

    def parse_keywords(self, _token, _process_tokens):
        """
        Parse a section beginning with a keyword
        :param _token: First token
        :param _process_tokens: A Tokens instance
        :return The ending token
        """
        # This is only called when it is certain that it is a keyword

        self.identifier = _token[1]
        _definition = _process_tokens.keywords[self.identifier]
        self.type_title = _definition["meta"]["title"]
        self.type = "keyword"
        self.type_description = _definition["meta"]["description"]
        if "expanded" in _definition:
            self.expanded = _definition["expanded"]
        _parts = _definition["parts"]

        # Look through the parts of the definitions
        for _curr_part_idx in range(0, len(_parts)):
            _curr_part = _parts[_curr_part_idx]
            if _curr_part["kind"] == "keyword":
                if _token[1] in _curr_part["values"]:
                    _token = _process_tokens.next()
            elif _curr_part["kind"] == "python-reference":
                # Assemble identifier
                _curr_identifier = ""
                while _token:
                    _curr_identifier += _token[1]
                    _token = _process_tokens.next()
                    if _token[1] != ".":
                        # Anything other than a . following a name means the end of the identifier
                        break
                    else:
                        _curr_identifier += "."
                        _token = _process_tokens.next()

                self.parameters[_curr_part["key"]] = _curr_identifier

            elif _curr_part["kind"] == "expression":
                _token, _expression = self.parse_expression(_token, _process_tokens)
                self.parameters[_curr_part["key"]] = _expression

            elif _curr_part["kind"] == "block":
                self._allowedChildTypes = ["keyword", "assign", "call"]
                _token = self.parse_block(_token, _process_tokens)
            elif _curr_part["kind"] == "parameters":
                _token = self.parse_parameters(_token, _process_tokens)

        if _token[0] in [NEWLINE, DEDENT, tokenize.NL]:
            _token = _process_tokens.next()
        return _token

    def parse_identifier(self, _token, _process_tokens):
        """
        Parse any identifier
        :param _token: First token
        :param _process_tokens: A Tokens instance
        :return The ending token
        """
        _identifier = ""
        # TODO: Implement custom code (PROD-31)
        if _token[1] in _process_tokens.keywords:
            return self.parse_keywords(_token, _process_tokens)
        else:
            # What remains is either an assignment or a function call with or without outputs

            self.assignments = {}
            self.assignment_order = []
            self.parameter_order = []
            _assignment_counter = 1

            # Find any assignments
            while _token:
                _tokenstring = _token[1]
                if _token[0] == OP:
                    if _tokenstring == ",":
                        self.assignments["assignment_" + str(_assignment_counter)] = _identifier
                        self.assignment_order.append("assignment_" + str(_assignment_counter))
                        _assignment_counter += 1
                        _identifier = ""
                        _token = _process_tokens.next()
                        continue
                    # TODO: Handle "[", assignments to expressions (ORG-104)
                    elif _tokenstring in ["=", "+="]:
                        self.type = "assign"
                        # This is an assignment, add the last assignment
                        self.assignment_operator = _tokenstring
                        self.assignments["assignment_" + str(_assignment_counter)] = _identifier
                        self.assignment_order.append("assignment_" + str(_assignment_counter))
                        # Move past the operand
                        _token = _process_tokens.next()
                        _identifier = ""

                        # Remember position
                        _expression_start = _process_tokens.position

                        # The expression may still be a plain function call, move forward, build identifier and check
                        while _token[0] == NAME or (_token[0] == OP and _token[1] == "."):
                            _identifier += _token[1]
                            _token = _process_tokens.next()

                        if _token[0] == OP and _token[1] == "(":
                            # This is a function call, handle
                            self.type = "call"
                            self.identifier = _identifier
                            return self.parse_function_call(_token, _process_tokens)
                        else:
                            # Move back to start of expression
                            _token = _process_tokens[_expression_start]
                            # It is a pure assignment parse the expressions, handle that
                            _expression_counter = 1
                            while _token:
                                _token, _expression = self.parse_expression(_token, _process_tokens)
                                # There are multiple expressions for multiple outputs
                                self.parameters["expression_" + str(_expression_counter)] = _expression
                                self.parameter_order.append("expression_" + str(_expression_counter))
                                if _token[1] == "," or _expression_counter > 1:
                                    if _token[0] == NEWLINE:
                                        break
                                    _expression_counter += 1
                                    _token = _process_tokens.next()
                                else:
                                    break

                            if _token[0] == NEWLINE:
                                _token = _process_tokens.next()

                            self.type_title = _process_tokens.keywords["@assign"]["meta"]["title"]
                            self.type_description = _process_tokens.keywords["@assign"]["meta"]["description"]
                            self.type = "assign"
                            self.identifier = "@assign"
                            return _token

                    elif _tokenstring == "(":
                        self.identifier = _identifier
                        # It is not an assignment, bot a direct function call, handle that
                        self.type = "call"
                        return self.parse_function_call(_token, _process_tokens)

                _identifier += _tokenstring
                _token = _process_tokens.next()

            # EOF
            return _token

    def from_tokens(self, _token, _process_tokens, _documentation=None):
        """
        Populate self from tokens
        :param _token: First token
        :param _process_tokens: A Tokens instance
        :param _documentation: Documentation
        :return The ending token
        """
        self.id = str(_process_tokens.position)
        self._allowedChildTypes = []
        self._token_begin = _process_tokens.position

        # Test there is another token
        if _token:
            # Is there any lead-in whitespace?
            _token = self.parse_whitespace(_token, _process_tokens)

        # Special Case after a dedent; Documentation might have been defined previously
        if _documentation and len(self.lead_in_whitespace) == 0:
            self.documentation = _documentation
        if _token:
            # Is there any documentation?
            _token, self.documentation = parse_documentation(_token, _process_tokens)
            if _token[0] in [tokenize.NL, DEDENT]:
                if self.documentation:
                    self.identifier = "Documentation"
                else:
                    self.identifier = "Newline"
                self.type = "documentation"
                return _token

        if _token:
            # Set the row on which the token is found, used for stepping
            self.row = _token[2][0]

            # Is there an identifier?
            _token = self.parse_identifier(_token, _process_tokens)

        # Is the documentation not followed by

        self._token_end = _process_tokens.position
        self.raw = _process_tokens._items[self._token_begin: self._token_end]
        return _token

    def tokenize_documentation(self, _process_tokens):
        """
        Creates tokens from the documentation
        :param _process_tokens: A Tokens instance. Unused, there for function map compatibility
        :return An array of tokens
        """

        if self.documentation:
            return [[STRING, '"""' + self.documentation + '"""'], [NEWLINE, "\n"]]
        else:
            return []

    @staticmethod
    def tokenize_expression(_expression):

        _f = io.BytesIO(_expression.encode(encoding="utf-8", errors='strict'))
        _loc_tokens = tokenize.tokenize(_f.readline)
        _loc_result = []
        for _curr_token in _loc_tokens:
            _loc_result.append([_curr_token[0], _curr_token[1]])
        return _loc_result[1:-1]  # Don't want encoding and endmarker

    def tokenize_keyword(self, _process_tokens):
        # Loop keyword
        _result = []

        _definition = _process_tokens.keywords[self.identifier]
        _curr_part = None
        _parts = _definition["parts"]
        # Look through the parts of the definitions
        for _curr_part_idx in range(0, len(_parts)):
            _curr_part = _parts[_curr_part_idx]
            if _curr_part["kind"] == "keyword":
                for _curr_value in _curr_part["values"]:
                    _result.append([NAME, _curr_value])

            elif _curr_part["kind"] == "python-reference":
                # Assemble identifier
                _ref = self.parameters[_curr_part["key"]]
                _ref_parts = str.split(_ref, ".")
                for _curr_ref_part_idx in range(0, len(_ref_parts)):
                    _result.append([NAME, _ref_parts[_curr_ref_part_idx]])
                    if _curr_ref_part_idx < len(_ref_parts) - 1:
                        _result.append([OP, "."])

            elif _curr_part["kind"] == "expression":
                _result += self.tokenize_expression(self.parameters[_curr_part["key"]])

            elif _curr_part["kind"] == "block":
                _result.append([OP, ":"])
                _result.append([NEWLINE, "\n"])
                _result.append([INDENT, "    "])
                for _curr_child in self.children:
                    _result += _curr_child.to_tokens(_process_tokens)
                _result.append([DEDENT, ""])

            elif _curr_part["kind"] == "parameters":
                _result.append([OP, "("])
                _params = []
                for _curr_param_name in self.parameter_order:
                    _curr_parameter = self.parameters[_curr_param_name]
                    if _curr_param_name[0:10] == "parameter_":
                        _params.append([NAME, _curr_param_name])
                        if _curr_parameter != "":
                            _params += [[OP, "="], [NAME, _curr_parameter]]
                        _params.append([OP, ","])

                _result += _params[0:-1]  # Ignore the last commma
                # ( YOU try to nicely insert an item every third item and not the last)

                _result.append([OP, ")"])

        # Do not add newlines after blocks, they have dedents.
        if _curr_part and _curr_part["kind"] != "block":
            _result.append([NEWLINE, "\n"])
        return _result

    def tokenize_assignment(self, _process_tokens):
        # Loop assignments
        _assignments = []
        _result = []
        for _curr_assignment_name in self.assignment_order:
            _curr_assignment = self.assignments[_curr_assignment_name]
            if _curr_assignment_name[0:11] == "assignment_":
                _assignments += [NAME, _curr_assignment], [OP, ","]
        _result += _assignments[0:-1]

        _result.append([OP, self.assignment_operator])

        # Loop expressions
        _expressions = []
        for _curr_expression_name in self.parameter_order:
            _curr_expression = self.parameters[_curr_expression_name]
            if _curr_expression_name[0:11] == "expression_":
                _expressions += self.tokenize_expression(_curr_expression)
                _expressions.append([OP, ","])
        _result += _expressions[0:-1]

        _result.append([NEWLINE, "\n"])
        return _result

    def tokenize_call(self, _process_tokens):
        # Calls

        # Loop assignments
        _assignments = []
        _result = []
        for _curr_assignment_name in self.assignment_order:
            _curr_assignment = self.assignments[_curr_assignment_name]
            if _curr_assignment_name[0:11] == "assignment_":
                _assignments += [NAME, _curr_assignment], [OP, ","]
        if len(_assignments) > 0:
            _result += _assignments[0:-1]
            _result.append([OP, self.assignment_operator])

        _result.append([NAME, self.identifier])

        _result.append([OP, "("])
        _params = []
        if len(self.parameters) == 1 and "expression" in self.parameters:
            _params += self.tokenize_expression(self.parameters["expression"])
            _params.append([OP, ","])
        else:
            for _curr_parameter_name in self.parameter_order:
                _curr_parameter = self.parameters[_curr_parameter_name]
                _params += self.tokenize_expression(_curr_parameter)
                _params.append([OP, ","])

        _result += _params[0:-1]

        _result.append([OP, ")"])

        _result.append([NEWLINE, "\n"])
        return _result

    def to_tokens(self, _process_tokens):

        # If raw is set, the verb has not been changed.
        if self.raw:
            # No need for tokenization of this verb, return the raw token array
            return self.raw
        else:
            # Initiate with lead_in_whitespace (initiated to [])
            _result = list(self.lead_in_whitespace)

            # Add documentation if present
            _result += self.tokenize_documentation(_process_tokens)
            # Handle by type (function map)
            _new_process_tokens = self.to_shortcuts[self.type](_process_tokens)
            return _result + _new_process_tokens
