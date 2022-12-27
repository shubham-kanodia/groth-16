from helpers.elliptic_curve_helper import EllipticCurveHelper
from helpers.polynomial_helper import FQ, Polynomial


class DummyTrustedSetup:
    def _compute_powers_of_tau(self, generator, tau, number_of_elements):
        encrypted_powers_of_secret = [generator]

        for idx in range(0, number_of_elements - 1):
            elem = self.elliptic_curve_helper.multiply(encrypted_powers_of_secret[-1], tau)
            encrypted_powers_of_secret.append(elem)

        return encrypted_powers_of_secret

    def __init__(self, elliptic_curve_helper: EllipticCurveHelper):
        self.N1 = 128  # In original setup set this to 4096
        self.N2 = 16

        self.elliptic_curve_helper = elliptic_curve_helper
        self.zx = None

        # Hidden elements made public for tests
        self.alpha = None
        self.beta = None
        self.tau = None

        # Phase 1 elements
        self.powers_of_tau_in_g1 = None
        self.powers_of_tau_in_g2 = None

        self.powers_of_tau_in_g1_product_alpha = None
        self.powers_of_tau_in_g1_product_beta = None

        self.beta_in_g1 = None
        self.beta_in_g2 = None
        self.alpha_in_g1 = None
        self.delta_in_g1 = None
        self.delta_in_g2 = None
        self.gamma_in_g2 = None

        # Phase 2 elements
        self.li_tau_divided_by_delta = None
        self.li_tau_divided_by_gamma = None
        self.zx_powers_of_tau = None

    def execute_phase_1(self):
        self.alpha = self.elliptic_curve_helper.generate_random_number()
        self.beta = self.elliptic_curve_helper.generate_random_number()
        self.tau = self.elliptic_curve_helper.generate_random_number()

        self.powers_of_tau_in_g1 = self._compute_powers_of_tau(
            self.elliptic_curve_helper.G1,
            self.tau,
            self.N1
        )

        self.powers_of_tau_in_g2 = self._compute_powers_of_tau(
            self.elliptic_curve_helper.G2,
            self.tau,
            self.N2
        )

        self.powers_of_tau_in_g1_product_alpha = [self.elliptic_curve_helper.multiply(_, self.alpha)
                                                  for _ in self.powers_of_tau_in_g1]

        self.powers_of_tau_in_g1_product_beta = [self.elliptic_curve_helper.multiply(_, self.beta)
                                                 for _ in self.powers_of_tau_in_g1]

        self.beta_in_g2 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G2,
            self.beta
        )

        self.beta_in_g1 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G1,
            self.beta
        )

        self.alpha_in_g1 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G1,
            self.alpha
        )

    def compute_li(self, i, qap_a, qap_b, qap_c):
        ai_beta_product = self.elliptic_curve_helper.evaluate_polynomial_at_hiding(qap_a[i],
                                                                                   self.powers_of_tau_in_g1_product_beta
                                                                                   )

        bi_alpha_product = self.elliptic_curve_helper.evaluate_polynomial_at_hiding(qap_b[i],
                                                                                    self.powers_of_tau_in_g1_product_alpha
                                                                                    )

        ci = self.elliptic_curve_helper.evaluate_polynomial_at_hiding(qap_c[i],
                                                                      self.powers_of_tau_in_g1)

        return self.elliptic_curve_helper.add(
            ai_beta_product, self.elliptic_curve_helper.add(bi_alpha_product, ci)
        )

    @staticmethod
    def calculate_zx(n):
        result = Polynomial([1])

        for val in range(1, n + 1):
            result = result * Polynomial([-1 * val, 1])
        return result

    def execute_phase_2(self, qap_a, qap_b, qap_c):
        delta = self.elliptic_curve_helper.generate_random_number()
        gamma = self.elliptic_curve_helper.generate_random_number()

        self.delta_in_g1 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G1, delta
        )

        self.delta_in_g2 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G2, delta
        )

        self.gamma_in_g2 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G2,
            gamma
        )

        li_tau = []
        for i in range(0, len(qap_a)):
            li_tau.append(self.compute_li(i, qap_a, qap_b, qap_c))

        self.li_tau_divided_by_delta = [self.elliptic_curve_helper.multiply(_, (FQ(1) / FQ(delta)).val)
                                        for _ in li_tau[1:]]

        self.li_tau_divided_by_gamma = [self.elliptic_curve_helper.multiply(_, (FQ(1) / FQ(gamma)).val)
                                        for _ in li_tau[:1]]

        self.zx = self.calculate_zx(len(qap_a))
        zx_value_at_tau = self.zx.evaluate(self.tau)

        self.zx_powers_of_tau = [self.elliptic_curve_helper.multiply(_, (zx_value_at_tau / FQ(delta)).val)
                                 for _ in self.powers_of_tau_in_g1]

    def get_prover_key(self):
        return [
            self.alpha_in_g1,
            self.beta_in_g1,
            self.delta_in_g1,
            self.powers_of_tau_in_g1,
            self.li_tau_divided_by_delta,
            self.zx_powers_of_tau,
            self.beta_in_g2,
            self.delta_in_g2,
            self.powers_of_tau_in_g2
        ]

    def get_verifier_key(self):
        return [
            self.alpha_in_g1,
            self.beta_in_g2,
            self.delta_in_g2
        ]
