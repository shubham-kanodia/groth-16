from helpers.elliptic_curve_helper import EllipticCurveHelper


class InitialSetupGenerator:
    def __init__(self, elliptic_curve_helper: EllipticCurveHelper):
        self.elliptic_curve_helper = elliptic_curve_helper

    def _generate_secret(self):
        random_number = self.elliptic_curve_helper.generate_random_number()
        return random_number

    def _generate_points(self, secret, generator, length):
        encrypted_powers_of_secret = [generator]

        for idx in range(0, length):
            elem = self.elliptic_curve_helper.multiply(encrypted_powers_of_secret[-1], secret)
            encrypted_powers_of_secret.append(elem)

        return encrypted_powers_of_secret

    def act(self):
        secret = self._generate_secret()

        # Generate G1 * s and G2 * s
        encrypted_powers_of_secret_g1 = self._generate_points(secret, self.elliptic_curve_helper.G1, self.elliptic_curve_helper.N1)
        encrypted_powers_of_secret_g2 = self._generate_points(secret, self.elliptic_curve_helper.G1, self.elliptic_curve_helper.N1)

        return encrypted_powers_of_secret_g1, encrypted_powers_of_secret_g2
