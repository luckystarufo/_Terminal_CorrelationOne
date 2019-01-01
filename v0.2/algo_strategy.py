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

        self.my_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def my_strategy(self, game_state):
        """
        :param game_state: state of the game
        :return: None
        """
        """
        1. Then Build Defenses
        """
        self.build_defences(game_state)

        """
        2. Deploy Information Units to Attack.
        """
        self.deploy_attackers(game_state)

    def build_defences(self, game_state):
        """
        Build Up defences in terms of priorities (by intuition)
        """
        """
        1st priority: skeleton DESTRUCTORs 
        """
        skeleton_destructor_locations = [[24, 13], [1, 12], [12, 9], [18, 9], [6, 9]]
        for location in skeleton_destructor_locations:
            if game_state.can_spawn(DESTRUCTOR, location):
                game_state.attempt_spawn(DESTRUCTOR, location)

        """
        2nd priority: attacking ENCRYPTER (top right)
        """
        if game_state.can_spawn(ENCRYPTOR, [24, 12]):
            game_state.attempt_spawn(ENCRYPTOR, [24, 12])

        """
        3rd priority: backup DESTRUCTOR
        """
        if game_state.can_spawn(DESTRUCTOR, [12, 5]):
            game_state.attempt_spawn(DESTRUCTOR, [12, 5])

        """
        4th priority: strengthen the corner defense (second defense group)
        """
        corner_extra_destructor_locations = [[25, 13], [2, 12]]
        for location in corner_extra_destructor_locations:
            if game_state.can_spawn(DESTRUCTOR, location):
                game_state.attempt_spawn(DESTRUCTOR, location)

        """
        5th priority: critical FILTERs
        """
        critical_filter_locations = [[0, 13], [3, 12], [22, 10], [23, 11], [21, 9]]
        for location in critical_filter_locations:
            if game_state.can_spawn(FILTER, location):
                game_state.attempt_spawn(FILTER, location)

        """
        6th priority: FILTERs of channel walls
        """
        channel_wall_locations = [[13, 1], [14, 2], [15, 3], [16, 4], [17, 5], [18, 6], [19, 7], [20, 8]]
        for location in channel_wall_locations:
            if game_state.can_spawn(FILTER, location):
                game_state.attempt_spawn(FILTER, location)

        """
        7th priority: critical FILTERs (second group)
        """
        critical_filter_locations = [[4, 11], [5, 10], [20, 9], [19, 9]]
        for location in critical_filter_locations:
            if game_state.can_spawn(FILTER, location):
                game_state.attempt_spawn(FILTER, location)

        """
        8th priority: attacking ENCRYPTER enhancement (top right)
        """
        if game_state.can_spawn(ENCRYPTOR, [23, 12]):
            game_state.attempt_spawn(ENCRYPTOR, [23, 12])
        if game_state.can_spawn(ENCRYPTOR, [23, 13]):
            game_state.attempt_spawn(ENCRYPTOR, [23, 13])

        """
        9th priority: enhance left top defense
        """
        if game_state.can_spawn(DESTRUCTOR, [2, 11]):
            game_state.attempt_spawn(DESTRUCTOR, [2, 11])

        """
        10th priority: critical FILTERs (third group)
        """
        critical_filter_locations = [[7, 9], [8, 9], [9, 9], [10, 9], [11, 9]]
        critical_filter_locations += [[13, 9], [14, 9], [15, 9], [16, 9], [17, 9]]
        for location in critical_filter_locations:
            if game_state.can_spawn(FILTER, location):
                game_state.attempt_spawn(FILTER, location)

        # if you still have cores, save it for next!

    def deploy_attackers(self, game_state):
        """
        Deploy Attackers
        """
        # if game_state.get_resource(game_state.BITS) < 5:
        #     return
        if game_state.get_resource(game_state.BITS) < 8:
            return

        if game_state.can_spawn(PING, [13, 0], 8):
            game_state.attempt_spawn(PING, [13, 0], 8)

        # elif game_state.get_resource(game_state.BITS) < 6:
        #     if game_state.can_spawn(PING, [13, 0], 5):
        #         game_state.attempt_spawn(PING, [13, 0], 5)
        # elif game_state.get_resource(game_state.BITS) < 7:
        #     if game_state.can_spawn(EMP, [23, 9], 2):
        #         game_state.attempt_spawn(EMP, [23, 9], 2)
        # else:
        #     if game_state.can_spawn(EMP, [23, 9], 1):
        #         game_state.attempt_spawn(EMP, [23, 9], 1)
        #     num_pings = int(game_state.get_resource(game_state.BITS))
        #     if game_state.can_spawn(PING, [13, 0], num_pings):
        #         game_state.attempt_spawn(PING, [13, 0], num_pings)

        # add scramblers randomly
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_RIGHT)
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        while game_state.get_resource(game_state.BITS) >= game_state.type_cost(SCRAMBLER) \
                and len(deploy_locations) > 0:
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            game_state.attempt_spawn(SCRAMBLER, deploy_location)

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
