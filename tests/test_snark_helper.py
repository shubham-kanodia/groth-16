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

    def get_w_dot_li_in_g1(self, witness):
        ech = self.snark_helper.ech
        trusted_setup = self.snark_helper.trusted_setup

        w_dot_li_in_g1 = ech.add_points(
            [ech.multiply(trusted_setup.li_tau_divided_by_delta[idx - 1], witness[idx].val)
             for idx in range(1, len(trusted_setup.li_tau_divided_by_delta) + 1)]
        )
        return w_dot_li_in_g1

    def calculate_l_tau_delta_inverse_from_original_values(self, test_witness):
        trusted_setup = self.snark_helper.trusted_setup
        ech = self.snark_helper.ech

        alpha, beta, tau = trusted_setup.alpha, trusted_setup.beta, trusted_setup.tau

        li_tau = [beta * self.snark_helper.qap_a[idx].evaluate(tau) +
                  alpha * self.snark_helper.qap_b[idx].evaluate(tau) +
                  self.snark_helper.qap_c[idx].evaluate(tau)
                  for idx in range(len(self.snark_helper.qap_a))]

        l_tau = sum([test_witness[idx].val * li_tau[idx] for idx in range(1, len(li_tau))])

        delta_inverse = (FQ(1) / FQ(trusted_setup.delta)).val

        return ech.g1_encrypt(delta_inverse * l_tau)

    def test_w_dot_li_component(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        ech = self.snark_helper.ech

        actual_value = self.get_w_dot_li_in_g1(test_witness)
        expected_value = self.calculate_l_tau_delta_inverse_from_original_values(test_witness)

        self.assertTrue(ech.eq(
            actual_value, expected_value
        ))

    def get_zx_hx_by_delta_component(self, test_witness):
        trusted_setup = self.snark_helper.trusted_setup
        ech = self.snark_helper.ech

        hx = self.snark_helper.calculate_hx(test_witness)

        delta_inverse = (FQ(1) / FQ(trusted_setup.delta)).val
        product_of_hx_zx_by_delta_with_original_values = trusted_setup.zx.evaluate(trusted_setup.tau) * \
                                                         hx.evaluate(trusted_setup.tau) * delta_inverse

        return ech.g1_encrypt(product_of_hx_zx_by_delta_with_original_values)

    def test_zx_hx_by_delta_component(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        hx = self.snark_helper.calculate_hx(test_witness)

        product_of_hx_zx = self.snark_helper.ech.add_points([
            self.snark_helper.ech.multiply(self.snark_helper.trusted_setup.zx_powers_of_tau[idx], coeff.val)
            for idx, coeff in enumerate(hx.coeffs)
        ])

        expected_value = self.get_zx_hx_by_delta_component(test_witness)
        self.assertTrue(
            self.snark_helper.ech.eq(
                expected_value,
                product_of_hx_zx
            )
        )

    def test_r_s_delta_component(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        trusted_setup = self.snark_helper.trusted_setup
        ech = self.snark_helper.ech

        self.snark_helper._generate_proof(test_witness)

        r, s, delta = self.snark_helper.r, self.snark_helper.s, trusted_setup.delta

        evaluation_from_original_values = ech.g1_encrypt(FQ(-1).val * r * s * delta)
        evaluation_from_hidings = ech.multiply(trusted_setup.delta_in_g1, FQ(-1 * r).val * s)

        ech.eq(
            evaluation_from_original_values,
            evaluation_from_hidings
        )

    def _get_third_element_of_proof(self, test_witness):
        alpha, beta, tau = self.snark_helper.trusted_setup.alpha, self.snark_helper.trusted_setup.beta, \
                           self.snark_helper.trusted_setup.tau

        A = self._get_first_element_of_proof(test_witness)
        B = self._get_second_element_of_proof(test_witness)

        elem_2 = self.snark_helper.s * A
        elem_3 = self.snark_helper.r * B
        elem_4 = FQ(-1).val * self.snark_helper.r * self.snark_helper.s * self.snark_helper.trusted_setup.delta

        li_tau = [beta * self.snark_helper.qap_a[idx].evaluate(tau) +
                  alpha * self.snark_helper.qap_b[idx].evaluate(tau) +
                  self.snark_helper.qap_c[idx].evaluate(tau)
                  for idx in range(len(self.snark_helper.qap_a))]

        l_tau = sum([test_witness[idx].val * li_tau[idx] for idx in range(1, len(li_tau))])
        h_tau = self.snark_helper.calculate_hx(test_witness).evaluate(tau)
        z_tau = self.snark_helper.trusted_setup.zx.evaluate(tau)

        delta_inverse = (FQ(1) / FQ(self.snark_helper.trusted_setup.delta)).val

        elem_1 = (l_tau + h_tau * z_tau) * delta_inverse

        return elem_1 + elem_2 + elem_3 + elem_4

    def test_proof_C(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        proof = self.snark_helper._generate_proof(test_witness)

        C = self._get_third_element_of_proof(test_witness)
        C_in_g1 = self.snark_helper.ech.g1_encrypt(C)

        # Check the second element of proof is s.A
        self.assertTrue(self.snark_helper.ech.eq(C_in_g1, proof[2]))

    def verify(self, proof, public_inputs):
        ech = self.snark_helper.ech
        trusted_setup = self.snark_helper.trusted_setup

        product_for_public_inputs = ech.multiply(
            trusted_setup.li_tau_divided_by_gamma[0],
            public_inputs[0].val
        )

        left = ech.pairing(proof[0], proof[1])

        right_1 = ech.pairing(trusted_setup.alpha_in_g1, trusted_setup.beta_in_g2)
        right_2 = ech.pairing(product_for_public_inputs, trusted_setup.gamma_in_g2)
        right_3 = ech.pairing(proof[2], trusted_setup.delta_in_g2)

        return right_1, right_2, right_3, left

    def test_l_tau_delta_inverse(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        trusted_setup = self.snark_helper.trusted_setup
        ech = self.snark_helper.ech

        alpha, beta, tau = trusted_setup.alpha, trusted_setup.beta, trusted_setup.tau

        li_tau = [beta * self.snark_helper.qap_a[idx].evaluate(tau) +
                  alpha * self.snark_helper.qap_b[idx].evaluate(tau) +
                  self.snark_helper.qap_c[idx].evaluate(tau)
                  for idx in range(len(self.snark_helper.qap_a))]

        l_tau = sum([test_witness[idx].val * li_tau[idx] for idx in range(1, len(li_tau))])

        self.assertTrue(
            ech.pairing(
                self.get_w_dot_li_in_g1(test_witness),
                trusted_setup.delta_in_g2
            ) == ech.pairing(
                ech.g1_encrypt(l_tau),
                ech.G2
            )
        )

    def test_raw_computation(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        _ = self.snark_helper._generate_proof(test_witness)

        trusted_setup = self.snark_helper.trusted_setup
        ech = self.snark_helper.ech
        (beta, alpha, tau) = trusted_setup.beta, trusted_setup.alpha, trusted_setup.tau

        A = self._get_first_element_of_proof(test_witness)
        B = self._get_second_element_of_proof(test_witness)

        left = A * B

        right_1 = trusted_setup.alpha * trusted_setup.beta

        li_tau = [beta * self.snark_helper.qap_a[idx].evaluate(tau) +
                  alpha * self.snark_helper.qap_b[idx].evaluate(tau) +
                  self.snark_helper.qap_c[idx].evaluate(tau)
                  for idx in range(len(self.snark_helper.qap_a))]

        right_2 = li_tau[0] * test_witness[0].val
        right_3 = self._get_third_element_of_proof(test_witness) * trusted_setup.delta

        self.assertTrue(FQ(left).val == FQ(right_1 + right_2 + right_3).val)

        # Check pairing based computation
        gamma_inverse = (FQ(1) / FQ(trusted_setup.gamma)).val
        left_pairing = ech.pairing(ech.g1_encrypt(FQ(A).val), ech.g2_encrypt(FQ(B).val))

        right_pairing_1 = ech.pairing(ech.g1_encrypt(alpha), ech.g2_encrypt(beta))
        right_pairing_2 = ech.pairing(ech.g1_encrypt(right_2 * gamma_inverse), ech.g2_encrypt(trusted_setup.gamma))
        right_pairing_3 = ech.pairing(
            ech.g1_encrypt(self._get_third_element_of_proof(test_witness)),
            ech.g2_encrypt(trusted_setup.delta)
        )

        self.assertTrue(left_pairing == (right_pairing_1 * right_pairing_2 * right_pairing_3))

    def test_verification(self):
        test_witness = [1, 3, 27, 9, 35, 30]
        test_witness = [FQ(_) for _ in test_witness]

        proof = self.snark_helper._generate_proof(test_witness)
        self.assertTrue(self.snark_helper.verify(proof, test_witness[:1]))
