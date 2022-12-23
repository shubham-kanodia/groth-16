import ast
import inspect

from ast import Assign, Return
from pprint import pprint

from helpers.polynomial_helper import Polynomial


class Operand:
    def __init__(self, val):
        self.val = val
        if isinstance(val, str):
            self.type = "SYMBOL"
        elif isinstance(val, (int, float)):
            self.type = "CONSTANT"
        else:
            raise Exception("Invalid operand")


class TypeAssignment:
    def __init__(self, symbol_a, symbol_b):
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b


class TypeAddition:
    def __init__(self, symbol_a, symbol_b, target):
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b
        self.target = target

    def r1cs(self, symbols_order):
        a = [0 for _ in symbols_order]
        b = [0 for _ in symbols_order]
        c = [0 for _ in symbols_order]

        if self.symbol_a.type == "SYMBOL":
            a[symbols_order.index(self.symbol_a.val)] = 1
        else:
            a[0] = self.symbol_a.val

        if self.symbol_b.type == "SYMBOL":
            a[symbols_order.index(self.symbol_b.val)] = 1
        else:
            a[0] += self.symbol_b.val

        b[0] = 1

        if self.target.type == "SYMBOL":
            c[symbols_order.index(self.target.val)] = 1
        else:
            c[0] = self.target.val

        return a, b, c


class TypeMultiplication:
    def __init__(self, symbol_a, symbol_b, target):
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b
        self.target = target

    def r1cs(self, symbols_order):
        a = [0 for _ in symbols_order]
        b = [0 for _ in symbols_order]
        c = [0 for _ in symbols_order]

        if self.symbol_a.type == "SYMBOL":
            a[symbols_order.index(self.symbol_a.val)] = 1
        else:
            a[0] = self.symbol_a.val

        if self.symbol_b.type == "SYMBOL":
            b[symbols_order.index(self.symbol_b.val)] = 1
        else:
            b[0] = self.symbol_b.val

        if self.target.type == "SYMBOL":
            c[symbols_order.index(self.target.val)] = 1
        else:
            c[0] = self.target.val

        return a, b, c


class Snark:

    def __init__(self, function):
        self.function = function
        self.gates = []
        self.symbols_count = 0
        self.symbols = []

        self._initialise()

    def mk_symbol(self):
        self.symbols_count += 1
        symbol = f"sym_{self.symbols_count}"

        self.symbols.append(symbol)
        return Operand(symbol)

    def parse_pow(self, left_symbol, n, target_symbol):
        if n == 1:
            self.gates.append(
                TypeMultiplication(
                    Operand(left_symbol),
                    Operand(1),
                    target_symbol
                )
            )
        elif n == 2:
            self.gates.append(
                TypeMultiplication(
                    Operand(left_symbol),
                    Operand(left_symbol),
                    target_symbol
                )
            )
        else:
            new_symbol = self.mk_symbol()
            self.gates.append(
                TypeMultiplication(
                    new_symbol,
                    Operand(left_symbol),
                    target_symbol
                )
            )

            self.parse_pow(left_symbol, n-1, new_symbol)

    def flatten_expression(self, target, value):
        if not isinstance(target, Operand):
            target = Operand(target)

        op_to_class = {
            ast.Add: TypeAddition,
            ast.Mult: TypeMultiplication
        }

        if isinstance(value, ast.BinOp):
            if isinstance(value.op, ast.Pow):
                assert isinstance(value.left, ast.Name)

                self.parse_pow(value.left.id, value.right.n, target)

            elif isinstance(value.left, ast.BinOp) and not isinstance(value.right, ast.BinOp):
                new_symbol = self.mk_symbol()

                self.gates.append(op_to_class[type(value.op)](
                    new_symbol,
                    Operand(value.right.id if hasattr(value.right, "id") else value.right.n),
                    target
                ))

                self.flatten_expression(new_symbol, value.left)

            elif isinstance(value.right, ast.BinOp) and not isinstance(value.left, ast.BinOp):
                new_symbol = self.mk_symbol()

                self.gates.append(op_to_class[type(value.op)](
                    Operand(value.left.id if hasattr(value.left, "id") else value.left.n),
                    Operand(new_symbol),
                    target
                ))

                self.flatten_expression(new_symbol, value.right)

            elif isinstance(value.right, ast.BinOp) and isinstance(value.left, ast.BinOp):
                new_symbol_a = self.mk_symbol()
                new_symbol_b = self.mk_symbol()

                self.gates.append(op_to_class[type(value.op)](
                    Operand(new_symbol_a),
                    Operand(new_symbol_b),
                    target
                ))

                self.flatten_expression(new_symbol_a, value.left)
                self.flatten_expression(new_symbol_b, value.right)

            elif not isinstance(value.right, ast.BinOp) and not isinstance(value.left, ast.BinOp):
                self.gates.append(op_to_class[type(value.op)](
                    Operand(value.left.id if hasattr(value.left, "id") else value.left.n),
                    Operand(value.right.id if hasattr(value.right, "id") else value.right.n),
                    target
                ))

    def _initialise(self):
        source = inspect.getsource(self.function)
        source = "\n".join(source.splitlines()[1:])
        code_ast = ast.parse(source)

        input_arguments = [_.arg for _ in code_ast.body[0].args.args]
        self.symbols.extend(input_arguments)

        ast_nodes = code_ast.body[0].body

        for ast_node in ast_nodes:
            if not isinstance(ast_node, (Assign, Return)):
                raise Exception("Invalid Snark")
            else:
                if isinstance(ast_node, Assign):
                    target_variable = ast_node.targets[0].id
                    value = ast_node.value

                    self.symbols.append(target_variable)
                    self.flatten_expression(target_variable, value)

                elif isinstance(ast_node, ast.Return):
                    target_variable = Operand("~out")

                    self.symbols.append("~out")
                    self.flatten_expression(target_variable, ast_node.value)

        self._calculate_r1cs()

    @staticmethod
    def _r1cs_to_qap(matrix):
        qap = []

        for y in range(len(matrix[0])):
            points = []
            for x in range(len(matrix)):
                points.append((x + 1, matrix[x][y]))

            polynomial = Polynomial.from_points(points)
            qap.append(polynomial.coeffs)

        return qap

    def _calculate_r1cs(self):
        self.symbols = [Operand("~one")] + self.symbols

        A = []
        B = []
        C = []

        for gate in self.gates:
            constraints = gate.r1cs(self.symbols)

            A.append(constraints[0])
            B.append(constraints[1])
            C.append(constraints[2])

        qap_a = self._r1cs_to_qap(A)
        qap_b = self._r1cs_to_qap(B)
        qap_c = self._r1cs_to_qap(C)

    def __call__(self, *args):
        pass


@Snark
def foo(x):
    y = x ** 3
    return x + y + 5


foo(10)