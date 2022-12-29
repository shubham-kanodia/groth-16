import ast
import inspect

from ast import Assign, Return
from pprint import pprint

from helpers.polynomial_helper import Polynomial
from helpers.elliptic_curve_helper import EllipticCurveHelper
from helpers.dummy_trusted_setup import DummyTrustedSetup

from fields.field import FQ

from helpers.utils import *


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


class SourceParser:
    @staticmethod
    def get_source(function):
        return inspect.getsource(function)


class Snark:

    def __init__(self, function, source_parser=SourceParser()):
        self.function = function
        self.source_parser = source_parser
        self.gates = []
        self.symbols_count = 0
        self.symbols = []

        self.ech = EllipticCurveHelper()
        self.trusted_setup = DummyTrustedSetup(self.ech)

        self.trusted_setup.execute_phase_1()
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

            self.parse_pow(left_symbol, n - 1, new_symbol)

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
        source = self.source_parser.get_source(self.function)

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
        self.execute_trusted_setup_phase_2()

    def execute_trusted_setup_phase_2(self):
        self.trusted_setup.execute_phase_2(self.qap_a, self.qap_b, self.qap_c)

    @staticmethod
    def _r1cs_to_qap(matrix):
        qap = []

        for y in range(len(matrix[0])):
            points = []
            for x in range(len(matrix)):
                points.append((FQ(x + 1), FQ(matrix[x][y])))

            polynomial = Polynomial.from_points(points)
            qap.append(polynomial)

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

        self.qap_a = self._r1cs_to_qap(A)
        self.qap_b = self._r1cs_to_qap(B)
        self.qap_c = self._r1cs_to_qap(C)

    def verify_witness(self, witness):

        for x in range(1, self.qap_a[0].degree + 2):
            A = [FQ(poly.evaluate(x)) for poly in self.qap_a]
            B = [FQ(poly.evaluate(x)) for poly in self.qap_b]
            C = [FQ(poly.evaluate(x)) for poly in self.qap_c]

            eq_result = dot(witness, A) * dot(witness, B) - dot(witness, C)
            assert (eq_result.val == 0)

    def calculate_hx(self, witness):
        A = Polynomial.sum([Polynomial([witness[idx]]) * poly
                            for idx, poly in enumerate(self.qap_a)])

        B = Polynomial.sum([Polynomial([witness[idx]]) * poly
                            for idx, poly in enumerate(self.qap_b)])

        C = Polynomial.sum([Polynomial([witness[idx]]) * poly
                            for idx, poly in enumerate(self.qap_c)])

        hx = (A * B - C) / self.trusted_setup.zx
        return hx

    def _generate_proof(self, witness):
        # Verify witness
        self.verify_witness(witness)

        self.r = self.ech.generate_random_number()
        self.s = self.ech.generate_random_number()

        w_dot_A_in_g1 = self.ech.add_points([self.ech.multiply(
            self.ech.evaluate_polynomial_at_hiding(self.qap_a[idx], self.trusted_setup.powers_of_tau_in_g1),
            witness[idx].val
        ) for idx in range(len(self.qap_a))])

        A_in_g1 = self.ech.add_points([
            self.trusted_setup.alpha_in_g1,
            w_dot_A_in_g1,
            self.ech.multiply(self.trusted_setup.delta_in_g1, self.r)
        ])

        w_dot_B_in_g2 = self.ech.add_points([self.ech.multiply(
            self.ech.evaluate_polynomial_at_hiding(self.qap_b[idx], self.trusted_setup.powers_of_tau_in_g2),
            witness[idx].val
        ) for idx in range(len(self.qap_b))])

        w_dot_B_in_g1 = self.ech.add_points([self.ech.multiply(
            self.ech.evaluate_polynomial_at_hiding(self.qap_b[idx], self.trusted_setup.powers_of_tau_in_g1),
            witness[idx].val
        ) for idx in range(len(self.qap_b))])

        B_in_g2 = self.ech.add_points([
            self.trusted_setup.beta_in_g2,
            w_dot_B_in_g2,
            self.ech.multiply(self.trusted_setup.delta_in_g2, self.s)
        ])

        B_in_g1 = self.ech.add_points([
            self.trusted_setup.beta_in_g1,
            w_dot_B_in_g1,
            self.ech.multiply(self.trusted_setup.delta_in_g1, self.s)
        ])

        w_dot_li_in_g1 = self.ech.add_points(
            [self.ech.multiply(self.trusted_setup.li_tau_divided_by_delta[idx - 1], witness[idx].val)
             for idx in range(1, len(self.trusted_setup.li_tau_divided_by_delta) + 1)]
        )

        hx = self.calculate_hx(witness)
        product_of_hx_zx = self.ech.add_points([
            self.ech.multiply(self.trusted_setup.zx_powers_of_tau[idx], coeff.val)
            for idx, coeff in enumerate(hx.coeffs)
        ])

        C_in_g1 = self.ech.add_points([
            w_dot_li_in_g1,
            product_of_hx_zx,
            self.ech.multiply(A_in_g1, self.s),
            self.ech.multiply(B_in_g1, self.r),
            self.ech.multiply(self.trusted_setup.delta_in_g1, FQ(-1).val * self.r * self.s)
        ])

        return [A_in_g1, B_in_g2, C_in_g1]

    def verify(self, proof, public_inputs):
        product_for_public_inputs = self.ech.multiply(
            self.trusted_setup.li_tau_divided_by_gamma[0],
            public_inputs[0].val
        )

        left = self.ech.pairing(proof[0], proof[1])

        right_1 = self.ech.pairing(self.trusted_setup.alpha_in_g1, self.trusted_setup.beta_in_g2)
        right_2 = self.ech.pairing(product_for_public_inputs, self.trusted_setup.gamma_in_g2)
        right_3 = self.ech.pairing(proof[2], self.trusted_setup.delta_in_g2)

        right = right_1 * right_2 * right_3

        return left == right

    def __call__(self, *args):
        witness = [1, 3, 27, 9, 35, 31]
        # witness = [1, 3, 13, 9]
        witness = [FQ(_) for _ in witness]

        proof = self._generate_proof(witness)
        self.verify(proof, witness[:1])


# @Snark
# def foo(x):
#     y = x ** 3
#     return x + y + 5
#
#     # return x ** 2 + 4
#
#
# foo(3)