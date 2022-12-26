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

        # Phase 1 elements
        self.powers_of_tau_in_g1 = None
        self.powers_of_tau_in_g2 = None

        self.powers_of_tau_in_g1_product_alpha = None
        self.powers_of_tau_in_g1_product_beta = None

        self.beta_in_g2 = None

        # Phase 2 elements

    def execute_phase_1(self):
        alpha = self.elliptic_curve_helper.generate_random_number()
        beta = self.elliptic_curve_helper.generate_random_number()
        tau = self.elliptic_curve_helper.generate_random_number()

        self.powers_of_tau_in_g1 = self._compute_powers_of_tau(
            self.elliptic_curve_helper.G1,
            tau,
            self.N1
        )

        self.powers_of_tau_in_g2 = self._compute_powers_of_tau(
            self.elliptic_curve_helper.G2,
            tau,
            self.N2
        )

        self.powers_of_tau_in_g1_product_alpha = [self.elliptic_curve_helper.multiply(_, alpha)
                                                  for _ in self.powers_of_tau_in_g1]

        self.powers_of_tau_in_g1_product_beta = [self.elliptic_curve_helper.multiply(_, beta)
                                                 for _ in self.powers_of_tau_in_g1]

        self.beta_in_g2 = self.elliptic_curve_helper.multiply(
            self.elliptic_curve_helper.G2,
            beta
        )

    def execute_phase_2(self):
        pass
