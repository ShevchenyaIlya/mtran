from lexer_constants import *


class Parser(object):
    """
    class Parser

    """

    def __init__(self):
        self.tokens = None

    def _node(self, pos):
        """
        return new node and pos

        """
        possible_values = {
            "{": "}",
            "(": ")",
        }

        node = list()
        try:
            while self.tokens[pos].value not in possible_values.values():
                delimiter = self.tokens[pos]
                if delimiter.value in possible_values.keys():
                    new_node, pos = self._node(pos + 1)
                    node.append(
                        [delimiter.value, new_node, possible_values[delimiter.value]]
                    )
                else:
                    if delimiter.value in [
                        *ARITHMETIC_OPERATIONS,
                        *OVERRIDE_OPERATION,
                        *COMPARE_SIGNS,
                        ",",
                    ]:
                        node.append([self.tokens[pos]])
                    elif delimiter.tag in [WHILE, FOR, IF]:
                        node.extend([self.tokens[pos], ["condition:"]])
                    else:
                        node.append(self.tokens[pos])
                pos += 1
        except BaseException:
            msg = 'Parser error! Missing symbol ")"'
            msg += " in line {}, column {}".format(19, 28)
            raise Exception(msg)

        return node, pos

    def build(self, tokens):
        """
        return ast

        """
        ast = list()
        if tokens:
            pos = 0
            self.tokens = tokens
            ast.append("program: ")
            while pos < len(tokens):
                if tokens[pos].value == "{":
                    node, pos = self._node(pos + 1)
                    pos += 1
                    ast.append([node])
                else:
                    if tokens[pos].tag == TYPE:
                        pos_copy = pos
                        if tokens[pos + 1].tag == FUNC_DECLARATION:
                            node, pos = self._node(pos + 3)
                            ast.append(
                                [
                                    "function declaration:",
                                    tokens[pos_copy].value,
                                    tokens[pos_copy + 1].value,
                                    ["args:", "(", node, ")"],
                                    "body:",
                                ]
                            )
                            pos += 1
                            continue

                    msg = (
                        'Parser error! Expected "{" but given "%s"' % tokens[pos].value
                    )
                    msg += " in line {}".format(tokens[pos].row)
                    raise Exception(msg)
            ast.append("end program")

        return ast
