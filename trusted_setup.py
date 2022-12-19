from helpers.setup_helper import SetupHelper

from actors.setup.participant import Participant
from actors.setup.initial_setup_generator import InitialSetupGenerator


N_PARTICIPANTS = 1

setup_helper = SetupHelper()

initial_setup_generator = InitialSetupGenerator(setup_helper)
participants = [Participant(setup_helper) for _ in range(N_PARTICIPANTS)]

generated_points = initial_setup_generator.act()

for idx, participant in enumerate(participants):
    generated_points = participant.act(generated_points)
    print(f"Participant - {idx} ceremony role complete")

print(generated_points)
