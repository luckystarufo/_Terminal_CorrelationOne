import gamelib
import random
import math
import warnings
from sys import maxsize

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

Additional functions are made available by importing the AdvancedGameState 
class from gamelib/advanced.py as a replcement for the regular GameState class 
in game.py.

You can analyze action frames by modifying algocore.py.

The GameState.map object can be manually manipulated to create hypothetical 
board states. Though, we recommended making a copy of the map to preserve 
the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        random.seed()

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Uncomment this line to suppress warnings.

        self.extremer_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def extremer_strategy(self, game_state):
        """
        :param game_state: state of the game
        :return: None
        """
        """
        1. Build Offensive Channel (refer to BLACKBEARD)
        """
        self.build_offensive_channel(game_state)

        """
        2. Then Build Normal Defenses
        """
        self.build_normal_defences(game_state)

        """
        3. Deploy Normal Information Units to Attack.
        """
        self.deploy_channel_attackers(game_state)

    def build_offensive_channel(self, game_state):
        """
        create a channel to attack the corner
        """
        front_destructor_locations = [[23, 13], [24, 13]]
        for location in front_destructor_locations:
            if game_state.can_spawn(DESTRUCTOR, location):
                game_state.attempt_spawn(DESTRUCTOR, location)

        front_encrypter_locations = [[25, 13], [24, 12], [23, 11]]
        for location in front_encrypter_locations:
            if game_state.can_spawn(ENCRYPTOR, location):
                game_state.attempt_spawn(ENCRYPTOR, location)

        filter_locations = [[22, 10], [21, 9], [20, 8], [19, 7], [18, 6], [17, 5],
                            [16, 4], [15, 3], [14, 2]]
        for location in filter_locations:
            if game_state.can_spawn(FILTER, location):
                game_state.attempt_spawn(FILTER, location)

        # backup destructor
        if game_state.can_spawn(DESTRUCTOR, [13, 1]):
            game_state.attempt_spawn(DESTRUCTOR, [13, 1])

        # strengthened encrypter
        if game_state.can_spawn(ENCRYPTOR, [23, 12]):
            game_state.attempt_spawn(ENCRYPTOR, [23, 12])

    def build_normal_defences(self, game_state):
        """
        defenses that protect us in general
        """
        # destructor at the top left corner
        if game_state.can_spawn(DESTRUCTOR, [1, 12]):
            game_state.attempt_spawn(DESTRUCTOR, [1, 12])
        # destructors in the middle
        if game_state.can_spawn(DESTRUCTOR, [11, 9]):
            game_state.attempt_spawn(DESTRUCTOR, [11, 9])
        if game_state.can_spawn(DESTRUCTOR, [7, 9]):
            game_state.attempt_spawn(DESTRUCTOR, [7, 9])
        if game_state.can_spawn(DESTRUCTOR, [15, 9]):
            game_state.attempt_spawn(DESTRUCTOR, [15, 9])
        # destructor at the back (second barrier)
        if game_state.can_spawn(DESTRUCTOR, [11, 5]):
            game_state.attempt_spawn(DESTRUCTOR, [11, 5])

        # firewalls: in the form of filters
        firewall_locations = [[0, 13], [2, 13], [3, 12], [4, 11], [5, 10], [6, 9]]
        firewall_locations += [[8, 9], [9, 9], [10, 9]]
        firewall_locations += [[12, 9], [13, 9], [14, 9]]
        firewall_locations += [[16, 9], [17, 9], [18, 9]]
        for location in firewall_locations:
            if game_state.can_spawn(FILTER, location):
                game_state.attempt_spawn(FILTER, location)

        # another destructor as a surprise to welcome our enemy!
        if game_state.can_spawn(DESTRUCTOR, [14, 6]):
            game_state.attempt_spawn(DESTRUCTOR, [14, 6])

    def deploy_channel_attackers(self, game_state):
        """
        deploy the attackers (eg. pings) inside the channel
        """
        """
        First lets check if we have 8 bits, if we don't we lets wait for 
        a turn where we do.
        """
        if game_state.get_resource(game_state.BITS) < 8:
            return

        """
        Now lets send out Pings in 2 groups to hopefully score
        """
        if game_state.can_spawn(PING, [13, 0], 4):
            game_state.attempt_spawn(PING, [13, 0], 4)
        if game_state.can_spawn(PING, [14, 0], 4):
            game_state.attempt_spawn(PING, [14, 0], 4)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
