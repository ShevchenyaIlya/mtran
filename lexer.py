import copy
from parser import Parser

import texttable as tt

from lexer_constants import *


class Token:
    """
    docstring for Token

    """

    def __init__(self, value, tag, row, col):
        self.value = value
        self.tag = tag
        self.row = row
        self.col = col

    def __str__(self):
        return "<{}, {}, {}, {}>".format(self.value, self.tag, self.row, self.col)

    def __repr__(self):
        return self.__str__()


class Lexer(dict):
    """
    docstring for Lexer

    """

    def __init__(self, file, *args):
        super().__init__(*args)
        self.pos, self.row, self.col = 0, 1, 1
        self.skip_end = False
        self.variable_type_defined = False
        self.char = ""
        self.file = open(file, "r")
        self.string = self.file.readline()
        self.errors_list = list()

    def errors(self):
        """
        print all errors

        """
        import sys

        self.file.close()
        sys.stderr.write("Lexer errors:\n")

        for i in self.errors_list:
            sys.stderr.write("\t%s\n" % i)

        sys.stderr.flush()
        exit(1)

    def error(self, text):
        """
        print error

        """
        self.errors_list.append(
            "{} in line {}, column {}".format(text, self.row, self.col)
        )

    def check_end_of_line(self, pos):
        result = True
        while pos > 0 and self.string[pos] == " ":
            pos -= 1

        if self.string[pos] == ";":
            result = False

        return result

    def empty_line(self):
        line = self.string

        for char in line[:-1]:
            if char != " ":
                return False

        return True

    def skip_line(self):
        self.string = self.file.readline()
        self.skip_end = False
        self.col = 1
        self.row += 1
        self.pos = 0

    def next_char(self):
        """
        set next char

        """
        if self.pos < len(self.string):
            self.char = self.string[self.pos]
            if self.char != "\n":
                self.col += 1
                self.pos += 1
            else:
                if self.check_end_of_line(self.pos - 1):
                    if not self.skip_end and not self.empty_line():
                        self.error("Missing end of line: ")

                self.skip_line()
        else:
            self.char = "#0"

    def skip_space(self):
        """
        skip spaces

        """
        while self.char.isspace():
            self.next_char()

    @staticmethod
    def compare_signs(lexeme):
        possible_signs = {
            "=": EQUAL_SIGN,
            "==": EQUAL,
            "!=": NOT_EQUAL,
            "<": LT,
            ">": GT,
            "<=": LE,
            ">=": GE,
        }

        return possible_signs.get(lexeme, None)

    @staticmethod
    def arithmetics_function(lexeme):
        possible_signs = {
            "=": EQUAL_SIGN,
            "==": EQUAL,
            "!=": NOT_EQUAL,
            "<": LT,
            ">": GT,
            "<=": LE,
            ">=": GE,
        }

        return possible_signs.get(lexeme, None)

    @staticmethod
    def logical_operation(lexeme):
        possible_operation = {
            "&&": AND,
            "||": OR,
        }

        return possible_operation.get(lexeme, None)

    def is_build_in_function(self, lexeme):
        possible_func_names = {
            "if": IF,
            "else": ELSE,
            "while": WHILE,
            "for": FOR,
            "break": BREAK,
            "continue": CONTINUE,
            "return": RETURN,
            "printf": FUNC,
            "getchar": FUNC,
            "endl": FUNC,
            "cout": FUNC,
            "sizeof": FUNC,
        }

        if not self.variable_type_defined:
            return possible_func_names.get(lexeme, None)
        else:
            self.error(f"Undefined function type: {lexeme}")

    def is_function(self):
        if self.string[self.pos - 1] == "(":
            self.variable_type_defined = False
            return True

        return False

    def number_conversion(self, lexeme=""):
        """
        Parsing numbers: float or integer, catch incorrect number input
        :param lexeme: str
        :return: Token
        """
        if self.char.isdigit():
            count = 0
            sign = 1 if lexeme == "+" or lexeme == "" else -1

            while self.char.isdigit() or self.char == ".":
                if self.char == ".":
                    count += 1

                lexeme += self.char
                self.next_char()

            if count > 1:
                self.error('Incorrect format of number: "%s"' % lexeme)
                return None
            else:
                return Token(
                    sign * (int(lexeme)) if count == 0 else sign * (float(lexeme)),
                    NUMBER,
                    self.row,
                    self.col,
                )

    def check_names(self, lexeme):
        """
        Parsing name. Defining functions, variables, build-in functions
        :param lexeme: str
        :return: Token
        """

        token = None

        if self.variable_type_defined:
            if self.is_function():
                self.variable_type_defined = False
                token = Token(lexeme, FUNC_DECLARATION, self.row, self.col)
        else:
            if (func_type := self.is_build_in_function(lexeme)) is not None:
                token = Token(lexeme, func_type, self.row, self.col)
            elif lexeme in VARIABLE_TYPES:
                self.variable_type_defined = True
                token = Token(lexeme, TYPE, self.row, self.col)

        return token

    def check_operation(self, lexeme):
        """
        Parsing different operations
        :param lexeme: str
        :return: Token
        """

        token = None

        if lexeme in ARITHMETIC_OPERATIONS:
            token = Token(lexeme, "ARITHMETIC_OPERATIONS", self.row, self.col)
        elif lexeme in OVERRIDE_OPERATION:
            token = Token(lexeme, "OVERRIDE_OPERATION", self.row, self.col)
        elif (logical_operation := self.logical_operation(lexeme)) is not None:
            token = Token(lexeme, logical_operation, self.row, self.col)
        elif (sign_type := self.compare_signs(lexeme)) is not None:
            token = Token(lexeme, sign_type, self.row, self.col)

        return token

    def processing_bracket(self, bracket, *, skip_end=False):
        """
        Return Token for different types of brackets
        :param bracket: str
        :param skip_end: bool
        :return: Token
        """

        possible_brackets = {
            "(": L_PAR,
            ")": R_PAR,
            "[": L_SQUARE,
            "]": R_SQUARE,
            "{": L_CURL,
            "}": R_CURL,
        }

        if skip_end:
            self.skip_end = True

        return Token(bracket, possible_brackets[bracket], self.row, self.col)

    def check_brackets(self):
        """
        Check which type of brackets is used
        :return: Token
        """

        lexeme = self.char
        token = None

        if lexeme in ("(", ")"):
            token = self.processing_bracket(lexeme, skip_end=True)
        elif lexeme in ("[", "]"):
            token = self.processing_bracket(lexeme)
        elif lexeme in ("{", "}"):
            token = self.processing_bracket(lexeme, skip_end=True)

        self.next_char()

        return token

    def next_token(self):
        """
        Parsing code file and getting tokens
        :return: Token
        """

        self.skip_space()
        lexeme = ""

        if self.char.isalpha() or self.char == "_":
            lexeme = self.char
            self.next_char()

            while self.char.isalpha() or self.char.isdigit():
                lexeme += self.char
                self.next_char()

            if (token := self.check_names(lexeme)) is not None:
                return token

            if not self.variable_type_defined:
                pos = self.pos

                while self.string[pos] == " ":
                    pos += 1

                if self.string[pos] == "(":
                    self.error(f"Undefined function type '{lexeme}'")
                    return None

            self.variable_type_defined = False
            return Token(lexeme, ID, self.row, self.col)

        elif self.char in "+-*%><=^!?&|":
            lexeme, count = self.char, 1
            self.next_char()

            while self.char in "+-*%><=^!?&|":
                lexeme += self.char
                count += 1
                self.next_char()

            if count > 2:
                self.error('Incorrect format of operation: "%s"' % lexeme)
                return None
            else:
                if lexeme in ("-", "+"):
                    sign = lexeme
                    self.next_char()

                    return self.number_conversion(sign)

                elif (token := self.check_operation(lexeme)) is not None:
                    return token

            self.error('Undefined operation: "%s"' % lexeme)

        elif self.char.isdigit():
            return self.number_conversion()

        elif self.char in ("(", ")", "{", "}", "[", "]"):
            return self.check_brackets()

        elif self.char == "#0":
            return Token("EOF", None, self.row, self.col)

        elif self.char == "/":
            lexeme = self.char
            self.next_char()
            if self.char in ("/", "*"):
                return self.skip_comments("\n" if self.char == "/" else "/")

            return Token(lexeme, "ARITHMETIC_OPERATIONS", self.row, self.col)

        elif self.char in ('"', "'"):
            character, count = self.char, 0
            self.next_char()

            while self.char != character:
                count += 1
                condition, lexeme = self.parse_line_end(lexeme)
                if condition:
                    continue

                lexeme += self.char
                self.next_char()

            self.next_char()

            if character == "'":
                if count == 1:
                    return Token(lexeme, CHAR, self.row, self.col)
            elif character == '"':
                return Token(lexeme, STRING, self.row, self.col)

            self.error("Incorrect quotes: '%s'" % lexeme)

        elif self.char in (";", ","):
            lexeme = self.char
            self.next_char()
            return Token(
                lexeme, SEMICOLON if lexeme == ";" else COMMA, self.row, self.col
            )

        elif self.char == "\n":
            self.pos -= 1
            self.col -= 1
            self.next_char()
            return None

        elif self.char in self:
            lexeme = self.char
            self.next_char()
            return Token(lexeme, self[lexeme], self.row, self.col)

        else:
            lexeme = self.char
            self.error('Unknown character: "%s"' % self.char)
            self.next_char()
            return Token(lexeme, UNKNOWN, self.row, self.col)

        return None

    def parse_line_end(self, lexeme):
        """
        Parsing symbol of line end inside C++ char or string types
        :param lexeme: str
        :return: (bool, str)
        """

        if self.char == "\\":
            lexeme += self.char
            self.next_char()
            lexeme += self.char
            self.next_char()

            return True, lexeme

        return False, lexeme

    def skip_comments(self, char):
        """
        Base of condition skipping line content in comment
        :param char: str - comment end character
        :return: Token()
        """

        self.skip_end = True

        while self.char != char:
            self.next_char()

        self.next_char()

        return self.next_token()

    def get_token(self):
        """
        Returning token
        :return: Token
        """

        self.next_char()
        while True:
            result = self.next_token()

            if not result:
                continue

            if result.value == "EOF":
                break

            yield result

    def tokens(self):
        """
        Returning list of parsing tokens
        :return: list
        """

        result = [i for i in self.get_token()]
        return result

    def raw_input(self, user_string):
        """
        Return raw user input
        :param user_string: str
        :return: list
        """

        self.string = user_string
        return self.tokens()


def draw_tags_groups(tokens):
    tokens_copy = copy.deepcopy(tokens)
    tokens_copy.sort(key=lambda x: x.tag)
    tag_names = {*[token.tag for token in tokens_copy]}
    tables = []
    for name in tag_names:
        table = tt.Texttable()
        table.header(["Value", "Row", "Column"])
        for token in filter(lambda x: x.tag == name, tokens_copy):
            table.add_row((token.value, token.row, token.col))

        tables.append((name, table))

    for name, table in tables:
        print("Tag:", name)
        print(table.draw())
        print()


def draw_result_table(tokens):
    tab = tt.Texttable()
    headings = ["Value (token)", "Tag", "Row", "Column"]
    tab.header(headings)

    values = list()
    tags = list()
    rows = list()
    columns = list()

    for token in tokens:
        values.append(token.value)
        tags.append(token.tag)
        rows.append(token.row)
        columns.append(token.col)

    for row in zip(values, tags, rows, columns):
        tab.add_row(row)
    s = tab.draw()
    print(s)


def check_if_main_exist(tokens):
    return list(
        filter(lambda x: x.tag == FUNC_DECLARATION and x.value == "main", tokens)
    )


def syntax_analyzer(ast, tabs):
    for i in ast:
        if isinstance(i, list):
            syntax_analyzer(i, tabs + 1)
        else:
            result, value = tabs * "  |", i.value if not isinstance(i, str) else i
            print("{}{}".format(result, value))


if __name__ == "__main__":
    path = "main_1.cpp"
    lexer = Lexer(path)
    parser = Parser()
    tokens = lexer.tokens()
    if len(check_if_main_exist(tokens)) == 0:
        lexer.error("Program should have function 'main'")

    if lexer.errors_list:
        lexer.errors()

    draw_result_table(tokens)
    draw_tags_groups(tokens)

    ast = parser.build(tokens)
    syntax_analyzer(ast, 2)
