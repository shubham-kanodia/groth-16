from helpers.setup_helper import SetupHelper


class Participant:
    def __init__(self, setup_helper: SetupHelper):
        self.setup_helper = setup_helper

    def act(self, points):
        g1_points = points[0]
        g2_points = points[1]

        # Generate its own secret as participant (t1)
        secret_random_number = self.setup_helper.generate_random_number()

        # Multiple with its own generated secret random number
        encrypted_powers_of_secret_g1 = [
            point * secret_random_number
            for point in g1_points
        ]

        encrypted_powers_of_secret_g2 = [
            point * secret_random_number
            for point in g2_points
        ]

        return encrypted_powers_of_secret_g1, encrypted_powers_of_secret_g2
