import operator as op
import subprocess

import lexical_analysis
from lexer import ID, Token
from lexical_analysis import display_tokens, tokens, types
from semantic_analysis import semantic_analysis
from syntax_analysis import build_tree

OPERATIONS = dict()
OPERATIONS["+"] = lambda env, *x: obs(env, op.add, *x)
OPERATIONS["-"] = lambda env, *x: obs(env, op.sub, *x)
OPERATIONS["*"] = lambda env, *x: obs(env, op.mul, *x)
OPERATIONS["/"] = lambda env, *x: obs(env, op.truediv, *x)
OPERATIONS["//"] = lambda env, *x: obs(env, op.floordiv, *x)
OPERATIONS["%"] = lambda env, *x: obs(env, op.mod, *x)
OPERATIONS["="] = lambda env, *x: obs(env, op.eq, *x)
OPERATIONS["/="] = lambda env, *x: obs(env, op.ne, *x)
OPERATIONS[">"] = lambda env, *x: obs(env, op.gt, *x)
OPERATIONS["<"] = lambda env, *x: obs(env, op.lt, *x)
OPERATIONS[">="] = lambda env, *x: obs(env, op.ge, *x)
OPERATIONS["<="] = lambda env, *x: obs(env, op.le, *x)
OPERATIONS["~"] = lambda env, *x: obs(env, op.ne, *x)
OPERATIONS["setq"] = lambda env, *x: define_new_variable(env, *x)
OPERATIONS["defun"] = lambda env, *x: define_function(env, *x)
OPERATIONS["if"] = lambda env, *x: compare(env, *x)
OPERATIONS["write"] = lambda env, *x: write(env, *x)
OPERATIONS["print"] = lambda env, *x: write_line(env, *x)
OPERATIONS["readint"] = lambda env, *x: read_integer(env, *x)


class Procedure(object):
    def __init__(self, params, *body):
        self.params, self.body = params, body

    def __call__(self, env, *args):
        if len(args) != len(self.params):
            msg = "Too many args! Expected %s, given %s" % (len(self.params), len(args))
            msg += " in line {}, column {}".format(args[0].col, args[0].row)
            raise TypeError(msg)

        for i, par in enumerate(self.params):
            env[par.value] = execute(args[i], env)

        magic = False
        while True:
            if magic:
                for i, par in enumerate(self.params):
                    env[par.value] = args[i]

            length = len(self.body) - 1
            for i, expr in enumerate(self.body):
                if i < length:  # если это не последнее выражение
                    result = execute(expr, env)
                    magic = True
                    if magic and result:
                        return result
                else:
                    if isinstance(env[expr[0].value], Procedure):
                        proc = env[expr[0].value]
                        self.params = proc.params
                        self.body = proc.body
                        args = [execute(i, env) for i in expr[1:]]
                        magic = True
                    else:
                        result = execute(expr, env)
                        return result


def testing_work(tree):
    result = subprocess.run(
        ["g++", "main_1.cpp", "-o", "main_1"], stderr=subprocess.PIPE
    )
    if result.returncode == 1:
        raise Exception(result.stderr.decode("utf-8"))
    subprocess.run(["chmod", "+x", "main_1"])
    result = subprocess.run(["./main_1"], stdout=subprocess.PIPE)
    print(result.stdout.decode("utf-8"))


def obs(env, fun, *args):
    result = execute(args[0], env)
    for i in args[1:]:
        result = fun(result, execute(i, env))
    return result


def define_function(env, *args):
    name, params, *body = args
    proc = Procedure(params, *body)
    if name.value not in env:
        env[name.value] = proc
    else:
        msg = 'Function "%s" already exists!' % name.value
        msg += "in line {}, column {}".format(name.col, name.row)
        raise Exception(msg)


def compare(env, *args):
    if execute(args[0], env):
        return execute(args[1], env)
    elif len(args) == 3:
        return execute(args[2], env)


def write(env, *args):
    from sys import stdout

    stdout.write(str(execute(args[0], env)))
    stdout.flush()


def write_line(env, *args):
    from sys import stdout

    stdout.write("%s\n" % str(execute(args[0], env)))
    stdout.flush()


def read_integer(env, *args):
    i = 0
    env[args[i].value] = int(input())

    from sys import stdout

    if isinstance(args[i].value, str):
        stdout.write(str(execute(args[0], env)))
        stdout.flush()


def define_new_variable(env, *args):
    i = 0
    while i < len(args):
        env[args[i].value] = execute(args[i + 1], env)
        i += 2


def execute(expr, env):
    if isinstance(expr, Token):
        if expr.tag == ID and expr.value in env:
            return env[expr.value]
        else:
            return expr.value
    else:
        first, *second = expr
        if first.value in env and callable(env[first.value]):
            return env[first.value](env, *second)
        else:
            msg = 'Function "%s" not exists!' % first.value
            msg += "in line {}, column {}".format(first.col, first.row)
            raise Exception(msg)


if __name__ == "__main__":
    display_tokens()
    with open("main_1.cpp", "r") as file:
        tree = build_tree(file.read())

    print(tree)
    semantic_analysis(tree)
    testing_work(tree)
