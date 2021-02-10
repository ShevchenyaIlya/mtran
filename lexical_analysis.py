import re

import texttable as tt
from ply import lex
from ply.lex import TOKEN

tokens = (
    "FUNCDECL",
    "LPAR",
    "RPAR",
    "COMMA",
    "LCURL",
    "RCURL",
    "LCUADR",
    "RCUADR",
    "CUSTOM_FUNC",
    "EQUAL",
    "SEMICOLON",
    "NUMBER",
    "VARIABLE_TYPE",
    "ID",
    "BUILD_IN",
    "PLUSMINUS",
    "DIVMUL",
    "STRING",
    "IF",
    "ELSE",
    "DEQUAL",
    "RETURN",
    "GT",
    "LT",
    "GE",
    "LE",
    "MOD",
    "NOTEQUAL",
    "WHILE",
    "FOR",
    "CONTINUE",
    "BREAK",
)


types = {
    "int": "VARIABLE_TYPE",
    "float": "VARIABLE_TYPE",
    "double": "VARIABLE_TYPE",
    "char": "VARIABLE_TYPE",
    "void": "VARIABLE_TYPE",
}


reserved = {
    "if": "IF",
    "else": "ELSE",
    "auto": "VARIABLE_TYPE",
    "while": "WHILE",
    "for": "FOR",
    "break": "BREAK",
    "continue": "CONTINUE",
    "return": "RETURN",
    "sizeof": "BUILD_IN",
    "cout": "BUILD_IN",
    "endl": "BUILD_IN",
}

identifier = r"[a-zA-Z]\w*"

t_LCUADR = r"\["
t_RCUADR = r"\]"
t_LPAR = r"\("
t_RPAR = r"\)"
t_COMMA = r","
t_LCURL = r"\{"
t_RCURL = r"\}"
t_DEQUAL = r"\=\="
t_GE = r"\>\="
t_LE = r"\<\="
t_GT = r"\>"
t_LT = r"\<"
t_MOD = r"\%"
t_NOTEQUAL = r"!\="
t_EQUAL = r"\="
t_SEMICOLON = r";"
t_PLUSMINUS = r"\+|\-"
t_DIVMUL = r"/|\*"
t_STRING = r'("(\\.|[^"])*")|(\'(\\.|[^\'])*\')'

t_ignore = " \r\t\f"


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_NUMBER(t):
    r"[0-9.]+"
    try:
        t.value = int(t.value)
    except BaseException:
        try:
            t.value = float(t.value)
        except BaseException:
            t.value = None
    return t


class TypeDefine:
    type_define = False


@TOKEN(identifier)
def t_ID(t):
    if TypeDefine.type_define:
        TypeDefine.type_define = False
        if t.lexer.lexdata[t.lexpos + len(t.value)] == "(":
            reserved[t.value] = "CUSTOM_FUNC"
            t.type = "FUNCDECL"
        else:
            t.type = "ID"
    else:
        if t.lexer.lexdata[t.lexpos + len(t.value)] == "(":
            if (value := reserved.get(t.value, None)) is None:
                print("error")
            else:
                t.type = value
        else:
            if (res := types.get(t.value, "ID")) == "VARIABLE_TYPE":
                TypeDefine.type_define = True

            t.type = res if t.value not in reserved else reserved[t.value]

    return t


def t_error(t):
    print("Illegal character '%s' at line %d" % (t.value[0], t.lineno))
    t.lexer.skip(1)


data = """void reverseArray(int arr[], int start, int end)
{
    while (start < end)
    {
        int temp = arr[start];
        arr[start] = arr[end];
        arr[end] = temp;
        start++;
        end--;
    }
}

void printArray(int arr[], int size)
{
   for (int i = 0; i < size; i++)
       cout << arr[i];
       cout << " ";
   }
   cout << endl;
}

int main()
{
    int arr[] = {1, 2, 3, 4, 5, 6};
    int n = sizeof(arr) / sizeof(arr[0]);

    printArray(arr, n);

    reverseArray(arr, 0, n - 1);

    cout << "Reversed array is";
    cout << endl;

    printArray(arr, n);

    if (a < b)
    {
        int t = 10;
    }
    else {
        int t = 15;
    }

    return 0;
}"""


lexer = lex.lex(reflags=re.UNICODE | re.DOTALL)

if __name__ == "__main__":
    tab = tt.Texttable()
    headings = ["Value (token)", "Tag", "Row", "Column"]
    tab.header(headings)
    lexer.input(data)

    character_number, line_number = 0, 0
    while True:
        tok = lexer.token()

        if not tok:
            break

        if line_number < tok.lineno:
            character_number = tok.lexpos
            line_number = tok.lineno

        tab.add_row(
            (
                tok.value,
                tok.type,
                tok.lineno,
                tok.lexpos - character_number + len(str(tok.value)),
            )
        )
    s = tab.draw()
    print(s)
