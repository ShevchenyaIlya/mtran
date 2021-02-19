import re
from operator import add, mul, sub, truediv

from lexical_analysis import types
from syntax_analysis import build_tree

data = """
void reverseArray(int arr[], int start, int end)
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
   {
       cout << arr[i];
       cout << " ";
   }
   cout << endl;
}

int main()
{
    int arr[] = {1, 2, 3, 4, 5, 6};

    int n = sizeof(arr) / sizeof(arr[0]);

    printArray(arr);

    reverseArray(arr, 0, n - 1);

    cout << "Reversed array is";
    cout << endl;

    printArray(arr, n);

    int a = 10;
    int b = 10 - 14;
    if (a < b)
    {
        int t = 10;
    }
    else {
        int t = 15;
    }

    cout << t;

    return 0;
}
"""

operations = "+-*/"
operation_resolver = {"+": add, "-": sub, "*": mul, "/": truediv}
condition_resolver = ["<", ">", "<=", ">=", "==", "!="]
variables = {}
functions = {}


def parse_function_args(node):
    function_arguments = {}

    for part in node.parts:
        is_array = False

        if isinstance(part, str):
            break

        if len(part.parts) > 2:
            is_array = True

        function_arguments[part.parts[1]] = {
            "type": part.parts[0],
            "is_array": is_array,
        }

    return function_arguments


def parse_tree(tree):
    try:
        tree_type = tree.type
        parts = tree.parts
    except AttributeError:
        return tree

    if tree_type == "func_declaration":
        functions[parts[1]] = {
            "return": parts[0],
            "args": parse_function_args(parts[2]),
            "additional_args": {},
        }
        return

    if tree_type == "init":
        if len(parts) > 3:
            value = parts[3:]
        else:
            value = None

        functions[list(functions.keys())[-1]]["additional_args"][parts[1]] = {
            "type": parts[0],
            "value": value,
        }
        return

    if tree_type == "condition":
        cond = [
            *functions[list(functions.keys())[-1]]["args"],
            *list(functions[list(functions.keys())[-1]]["additional_args"].keys()),
        ]

        first = parse_tree(parts[0])
        second = parse_tree(parts[2])
        possible_types = list(types.keys())
        if (
            parts[1] in condition_resolver
            and (first in cond or type(first).__name__ in possible_types)
            and (second in cond or type(second).__name__ in possible_types)
        ):
            first_temp = functions[list(functions.keys())[-1]]["args"].get(
                parts[0], False
            ) or functions[list(functions.keys())[-1]]["additional_args"].get(
                parts[0], False
            )
            second_temp = functions[list(functions.keys())[-1]]["args"].get(
                parts[2], False
            ) or functions[list(functions.keys())[-1]]["additional_args"].get(
                parts[2], False
            )

            if not first_temp:
                first_temp = type(first).__name__
            else:
                first_temp = first_temp["type"]

            if not second_temp:
                second_temp = type(second).__name__
            else:
                second_temp = second_temp["type"]

            if first_temp == second_temp:
                return

        raise TypeError("Wrong operand types in condition")

    if tree_type == "var_call":
        cond = [
            *functions[list(functions.keys())[-1]]["args"],
            *list(functions[list(functions.keys())[-1]]["additional_args"].keys()),
        ]
        if parts[0] in cond and (parts[1] in cond or parts[1].type == "arg"):
            arg = parse_tree(parts[1])
            if arg in cond or isinstance(arg, int):
                return arg
            else:
                raise ValueError(f"Forbidden argument type in call {arg}")
        else:
            raise NameError(f"Unknown variable name {parts[0]} or {parts[1]}")

    if tree_type == "func_call":
        function = parts[0]
        if function == "cout":
            output_value = parse_tree(parts[1].parts[1])
            try:
                if output_value.type == "var_call":
                    output_type = functions[list(functions.keys())[-1]]["args"].get(
                        output_value.parts[0], False
                    ) or functions[list(functions.keys())[-1]]["additional_args"].get(
                        output_value.parts[0], False
                    )
                    if output_type["type"] in ["int", "char", "string"]:
                        return
                    else:
                        raise ValueError(
                            f"Output operator can't display value {output_type}"
                        )
            except AttributeError:
                if (
                    isinstance(output_value, (int, float, str))
                    or output_value == "endl"
                ):
                    return
        elif function in functions.keys():
            arguments = parts[1].parts

            if len(arguments) != len(functions[function]["args"]):
                raise Exception(
                    f"Wrong count of arguments passing to function {function}"
                )

            for index, arg in enumerate(arguments):
                try:
                    arg = parse_tree(arg.parts[1])
                except Exception:
                    arg = parse_tree(arg)

                argument = get_type(arg)

                if (
                    argument
                    != functions[function]["args"][
                        list(functions[function]["args"].keys())[index]
                    ]["type"]
                ):
                    raise ValueError(
                        f"Wrong argument type passing to function {function}"
                    )
            return

    if tree_type == "assign":
        assign_arguments = []
        for part in parts:
            if part == "=":
                continue

            try:
                if part.type == "var_call":
                    argument = get_type(part.parts[0])

                    assign_arguments.append(argument)
            except AttributeError:
                arg = parse_tree(part)
                argument = get_type(arg)

                assign_arguments.append(argument)

        if not (
            len(assign_arguments) == 2
            and assign_arguments[0] == assign_arguments[1]
            or len(assign_arguments) == 1
        ):
            raise ValueError(
                f"Can't convert {assign_arguments[1]} to {assign_arguments[0]}"
            )

    if tree_type == "modal_function":
        if parts[0] == "return":
            argument = parse_tree(parts[1])
            try:
                if eval(functions[list(functions.keys())[-1]]["return"]) == type(
                    argument
                ):
                    return
                else:
                    raise ValueError("Incorrect return value from function")
            except ValueError as exc:
                raise ValueError(exc)
            except Exception:
                raise ValueError(
                    "Using return statement in function than return 'void'"
                )

        return

    if tree_type == "arg":
        arg = parts[0]
        try:
            if arg.type == "var_call":
                return arg
        except Exception:
            pass

        if isinstance(arg, int):
            return arg
        elif isinstance(arg, float):
            return arg
        elif len(parts) == 1 and re.match(r"(\".*\")|(\'.*\')", arg):
            return arg
        return

    if tree_type in operations:
        first = parse_tree(parts[0])
        second = parse_tree(parts[1])
        if type(first) != type(second):
            raise TypeError(
                "Types mismatch: {0} and {1}".format(type(first), type(second))
            )
        if tree_type == "/" and second == 0:
            raise ZeroDivisionError("Unacceptable operation: division by zero")
        return operation_resolver[tree_type](first, second)

    for part in parts:
        if part != "=":
            parse_tree(part)


def get_type(value):
    argument = functions[list(functions.keys())[-1]]["args"].get(
        value, False
    ) or functions[list(functions.keys())[-1]]["additional_args"].get(value, False)
    if not argument:
        argument = type(value).__name__
    else:
        argument = argument["type"]

    return argument


def check_inits():
    for func in functions:
        additional_args = functions[func]["additional_args"]
        for key, value in additional_args.items():
            value_type = value["value"]
            try:
                if value_type[0].type == "var_call":
                    argument = get_type(value_type[0].parts[0])
                elif value_type[0].type == "arg":
                    arg = parse_tree(value_type[0])
                    argument = get_type(arg)
            except (AttributeError, TypeError):
                pass

            if value_type is not None and argument != value["type"]:
                raise ValueError(
                    f"Wrong initialization of variable: type {argument} can't initialize variable '{key}'"
                )


def semantic_analysis(tree):
    parse_tree(tree)

    # if not functions.get("main", False):
    #     raise Exception(
    #         "Program should have starting point as function with name 'main'"
    #     )

    check_inits()
    print(functions)


if __name__ == "__main__":
    tree = build_tree(data)
    semantic_analysis(tree)
