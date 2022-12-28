from unittest import TestCase
from unittest.mock import MagicMock

from helpers.snark_helper import Snark
from helpers.polynomial_helper import Polynomial
from fields.field import FQ


class TestSnarkHelper(TestCase):
    function_source = '''@Snark\ndef foo(x):\n\ty = x ** 3\n\treturn x + y + 5'''

    source_parser = MagicMock()
    source_parser.get_source.return_value = function_source

    snark_helper = Snark(MagicMock(), source_parser)

    def test_hx(self):
        test_witness = [1, 3, 27, 9, 35, 30]

        hx = self.snark_helper.calculate_hx(test_witness)
        zx = self.snark_helper.trusted_setup.zx

        A = Polynomial.sum([Polynomial([FQ(test_witness[idx])]) * poly
                            for idx, poly in enumerate(self.snark_helper.qap_a)])

        B = Polynomial.sum([Polynomial([FQ(test_witness[idx])]) * poly
                            for idx, poly in enumerate(self.snark_helper.qap_b)])

        C = Polynomial.sum([Polynomial([FQ(test_witness[idx])]) * poly
                            for idx, poly in enumerate(self.snark_helper.qap_c)])

        left = A * B - C
        right = hx * zx

        self.assertEqual(len(left.coeffs), len(right.coeffs))

        for coeff_1, coeff_2 in zip(left.coeffs, right.coeffs):
            self.assertTrue(coeff_1.val == coeff_2.val)

    def test_lx(self):
        qap_a = self.snark_helper.qap_a
        qap_b = self.snark_helper.qap_b
        qap_c = self.snark_helper.qap_c

        trusted_setup = self.snark_helper.trusted_setup
        ech = self.snark_helper.ech

        for idx in range(len(qap_a)):
            result_in_g1 = self.snark_helper.trusted_setup.compute_li(idx, qap_a, qap_b, qap_c)

            evaluation = trusted_setup.beta * qap_a[idx].evaluate(trusted_setup.tau) + \
                         trusted_setup.alpha * qap_b[idx].evaluate(trusted_setup.tau) + \
                         qap_c[idx].evaluate(trusted_setup.tau)

            evaluation_in_g1 = ech.multiply(ech.G1, evaluation)

            self.assertTrue(ech.eq(result_in_g1, evaluation_in_g1))

    def _get_first_element_of_proof(self, test_witness):
        trusted_setup = self.snark_helper.trusted_setup

        elem_1 = trusted_setup.alpha
        elem_2 = self.snark_helper.r * trusted_setup.delta
        A_tau = sum([test_witness[idx].val * self.snark_helper.qap_a[idx].evaluate(trusted_setup.tau)
                     for idx in range(len(self.snark_helper.qap_a))])

        return elem_1 + elem_2 + A_tau

    def test_proof_A(self):
        test_witness = [1, 3, 27, 9, 35, 30]

        test_witness = [FQ(_) for _ in test_witness]
        proof = self.snark_helper._generate_proof(test_witness)

        A = self._get_first_element_of_proof(test_witness)
        A_in_g1 = self.snark_helper.ech.g1_encrypt(A)

        self.assertTrue(self.snark_helper.ech.eq(proof[0], A_in_g1))

    def _get_second_element_of_proof(self, test_witness):
        trusted_setup = self.snark_helper.trusted_setup

        elem_1 = trusted_setup.beta
        elem_2 = self.snark_helper.s * trusted_setup.delta
        B_tau = sum([test_witness[idx].val * self.snark_helper.qap_b[idx].evaluate(trusted_setup.tau)
                     for idx in range(len(self.snark_helper.qap_b))])

        return elem_1 + elem_2 + B_tau

    def test_proof_B(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        proof = self.snark_helper._generate_proof(test_witness)

        B = self._get_second_element_of_proof(test_witness)
        B_in_g2 = self.snark_helper.ech.g2_encrypt(B)

        self.assertTrue(self.snark_helper.ech.eq(proof[1], B_in_g2))
