import gamelib
import random
import json
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
        self.create_collectors()

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

        # for analysis
        self.create_my_hierarchical_defenses()

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
        game_state.suppress_warnings(True)  # Uncomment this line to suppress warnings.

        verbose = 0  # if to report at each round
        # collect information at each round
        self.collect_info(game_state, verbose)

        if game_state.turn_number == 0:
            # 1st round: build defense skeleton
            self.build_skeleton(game_state)
        elif game_state.turn_number == 1:
            # 2nd round: analyze and perform sudden attack
            self.attempt_first_attack(game_state)
        else:
            # adjust strategy based on info collected
            self.execute_my_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def create_collectors(self):
        """ create collectors that gather the information
        :return: None
        """
        # right row
        self.my_current_defenses = {}
        self.enemy_current_defenses = {}
        self.my_current_resources = {}
        self.enemy_current_resources = {}
        self.my_current_health = None
        self.enemy_current_health = None

        # last round
        self.my_previous_defenses = {}
        self.enemy_previous_defenses = {}
        self.my_previous_resources = {}
        self.enemy_previous_resources = {}
        self.my_previous_health = None
        self.enemy_previous_health = None

        # for regional defense
        self.my_regions = [[0, 1], [1, 1], [2, 1], [3, 1], [1, 0], [2, 0]]
        self.my_regional_defense_summary = {}
        self.enemy_regions = [[0, 0], [1, 0], [2, 0], [3, 0], [1, 1], [2, 1]]
        self.enemy_regional_defense_summary = {'permeability': {}, 'defense': {}}

        self.front_regional_defense_level = [0, 0, 0, 0]  # level-0 defense as init
        self.regional_complete_defenses = {}
        self.regional_defenses_addon_v0 = {}
        self.regional_defenses_addon_v1 = {}
        self.regional_defenses_addon_v2 = {}
        self.defense_v0 = {}
        self.defense_v1 = {}
        self.defense_v2 = {}
        self.defense_v3 = {}
        self.defense_v4 = {}
        self.defense_v5 = {}

    def create_my_hierarchical_defenses(self):
        """ a complete recipe of my defense architecture
            and we describe it in two ways:
            1. in terms of different regions
            2. in terms of priorities
        :return: None
        """
        """must have (essential)"""
        # init
        for region in self.my_regions:
            self.regional_complete_defenses[str(region)] = {}
            self.regional_complete_defenses[str(region)][FILTER] = []
            self.regional_complete_defenses[str(region)][ENCRYPTOR] = []
            self.regional_complete_defenses[str(region)][DESTRUCTOR] = []

        # [0, 1]
        self.regional_complete_defenses['[0, 1]'][FILTER] += \
            [[0, 13], [1, 13], [2, 12], [3, 12], [4, 11], [5, 10], [5, 12]]
        self.regional_complete_defenses['[0, 1]'][DESTRUCTOR] += \
            [[6, 11]]

        # [1, 1]
        self.regional_complete_defenses['[1, 1]'][FILTER] += \
            [[7, 11], [8, 11],
             [11, 9],
             [10, 12], [12, 12], [13, 12],
             [10, 13], [11, 13], [13, 13]]
        self.regional_complete_defenses['[1, 1]'][ENCRYPTOR] += \
            [[11, 8], [12, 8], [13, 8]]
        self.regional_complete_defenses['[1, 1]'][DESTRUCTOR] += \
            [[10, 9],
             [11, 12],
             [12, 13]]

        # [2, 1]
        self.regional_complete_defenses['[2, 1]'][FILTER] += \
            [[20, 11], [19, 11],
             [16, 9],
             [17, 12], [15, 12], [14, 12],
             [17, 13], [16, 13], [14, 13]]
        self.regional_complete_defenses['[2, 1]'][ENCRYPTOR] += \
            [[14, 8], [15, 8], [16, 8]]
        self.regional_complete_defenses['[2, 1]'][DESTRUCTOR] += \
            [[17, 9],
             [16, 12],
             [15, 13]]

        # [3, 1]
        self.regional_complete_defenses['[3, 1]'][FILTER] += \
            [[27, 13], [26, 13], [25, 12], [24, 12], [23, 11], [22, 10], [22, 12]]
        self.regional_complete_defenses['[3, 1]'][DESTRUCTOR] += \
            [[21, 11]]

        # [1, 0]
        # nothing

        # [2, 0]
        # nothing

        """may have (auxiliary)"""
        # init
        for region in self.my_regions:
            self.regional_defenses_addon_v0[str(region)] = {}
            self.regional_defenses_addon_v1[str(region)] = {}
            self.regional_defenses_addon_v2[str(region)] = {}
            self.regional_defenses_addon_v0[str(region)][FILTER] = []
            self.regional_defenses_addon_v0[str(region)][ENCRYPTOR] = []
            self.regional_defenses_addon_v0[str(region)][DESTRUCTOR] = []
            self.regional_defenses_addon_v1[str(region)][FILTER] = []
            self.regional_defenses_addon_v1[str(region)][ENCRYPTOR] = []
            self.regional_defenses_addon_v1[str(region)][DESTRUCTOR] = []
            self.regional_defenses_addon_v2[str(region)][FILTER] = []
            self.regional_defenses_addon_v2[str(region)][ENCRYPTOR] = []
            self.regional_defenses_addon_v2[str(region)][DESTRUCTOR] = []

        # [0, 1]
        self.regional_defenses_addon_v0['[0, 1]'][DESTRUCTOR] += \
            [[1, 12], [2, 13]]
        self.regional_defenses_addon_v1['[0, 1]'][DESTRUCTOR] += \
            [[2, 11]]
        self.regional_defenses_addon_v2['[0, 1]'][DESTRUCTOR] += \
            [[3, 13]]

        # [1, 1]
        self.regional_defenses_addon_v0['[1, 1]'][DESTRUCTOR] += \
            [[6, 10]]  # fake!
        self.regional_defenses_addon_v1['[1, 1]'][DESTRUCTOR] += \
            [[9, 13]]
        self.regional_defenses_addon_v2['[1, 1]'][DESTRUCTOR] += \
            [[9, 9]]

        # [2, 1]
        self.regional_defenses_addon_v0['[2, 1]'][DESTRUCTOR] += \
            [[21, 10]]  # fake!
        self.regional_defenses_addon_v1['[2, 1]'][DESTRUCTOR] += \
            [[18, 13]]
        self.regional_defenses_addon_v2['[2, 1]'][DESTRUCTOR] += \
            [[18, 9]]

        # [3, 1]
        self.regional_defenses_addon_v0['[3, 1]'][DESTRUCTOR] += \
            [[26, 12], [25, 13]]
        self.regional_defenses_addon_v1['[3, 1]'][DESTRUCTOR] += \
            [[25, 11]]
        self.regional_defenses_addon_v2['[3, 1]'][DESTRUCTOR] += \
            [[24, 13]]

        # [1, 0]
        self.regional_defenses_addon_v0['[1, 0]'][DESTRUCTOR] += \
            [[8, 7]]  # fake
        self.regional_defenses_addon_v1['[1, 0]'][DESTRUCTOR] += \
            []
        self.regional_defenses_addon_v2['[1, 0]'][DESTRUCTOR] += \
            []

        # [2, 0]
        self.regional_defenses_addon_v0['[2, 0]'][DESTRUCTOR] += \
            [[19, 7]]  # fake
        self.regional_defenses_addon_v1['[2, 0]'][DESTRUCTOR] += \
            []
        self.regional_defenses_addon_v2['[2, 0]'][DESTRUCTOR] += \
            []

        """in terms of priorities"""
        # v0: skeleton
        self.defense_v0[FILTER] = [[0, 13], [1, 13], [2, 12], [3, 12], [4, 11],
                                   [27, 13], [26, 13], [25, 12], [24, 12], [23, 11],
                                   [5, 10], [22, 10]]
        self.defense_v0[DESTRUCTOR] = [[6, 11], [21, 11], [10, 9], [17, 9]]

        # v1
        self.defense_v1[FILTER] = [[7, 11], [8, 11], [20, 11], [19, 11]]

        # v2
        self.defense_v2[FILTER] = [[10, 12], [11, 13], [12, 12], [13, 12],
                                   [14, 12], [15, 12], [16, 13], [17, 12]]
        self.defense_v2[DESTRUCTOR] = [[11, 12], [16, 12]]

        # v3
        self.defense_v3[FILTER] = [[11, 9], [16, 9]]

        # v4
        self.defense_v4[FILTER] = [[10, 13], [13, 13], [14, 13], [17, 13]]
        self.defense_v4[ENCRYPTOR] = [[13, 8], [14, 8]]
        self.defense_v4[DESTRUCTOR] = [[12, 13], [15, 13]]

        # v5
        self.defense_v5[ENCRYPTOR] = [[12, 9], [13, 9], [14, 9], [15, 9],
                                      [5, 11], [22, 11]]

    def collect_info(self, game_state, verbose=0):
        """ collect information of last battle
        :param game_state: current game state
        :param verbose: if to print out the info
        :return: None
        """
        # assign last round values to previous
        self.my_previous_defenses = self.my_current_defenses
        self.enemy_previous_defenses = self.enemy_current_defenses
        self.my_previous_resources = self.my_current_resources
        self.enemy_previous_resources = self.enemy_current_resources
        self.my_previous_health = self.my_current_health
        self.enemy_previous_health = self.enemy_current_health

        # collect new data: health
        self.my_current_health = game_state.my_health
        self.enemy_current_health = game_state.enemy_health

        # collect new data: resources
        self.my_current_resources['BITS'] = game_state.get_resource(game_state.BITS)
        self.my_current_resources['CORES'] = game_state.get_resource(game_state.CORES)
        self.enemy_current_resources['BITS'] = game_state.get_resource(game_state.BITS, 1)
        self.enemy_current_resources['CORES'] = game_state.get_resource(game_state.CORES, 1)

        # collect new data: defenses
        self.my_current_defenses = {FILTER: {}, ENCRYPTOR: {}, DESTRUCTOR: {}}
        self.enemy_current_defenses = {FILTER: {}, ENCRYPTOR: {}, DESTRUCTOR: {}}

        for i in range(game_state.ARENA_SIZE):
            for j in range(game_state.HALF_ARENA):
                # if it is a valid grid on our side
                if game_state.game_map.in_arena_bounds([i, j]):
                    for unit in game_state.game_map[i, j]:
                        self.my_current_defenses[unit.unit_type][str([i, j])] = unit.stability

        for i in range(game_state.ARENA_SIZE):
            for j in range(game_state.HALF_ARENA, game_state.ARENA_SIZE):
                # if it is a valid grid on enemy's side
                if game_state.game_map.in_arena_bounds([i, j]):
                    for unit in game_state.game_map[i, j]:
                        self.enemy_current_defenses[unit.unit_type][str([i, j])] = unit.stability

        if verbose:
            self.display_current_situation(game_state)

    def display_current_situation(self, game_state):
        """ print out current defenses, resources, health
        :return:
        """
        gamelib.debug_write("data @ Round %d ... !!!!!!!" % game_state.turn_number)
        gamelib.debug_write("==================================================")
        gamelib.debug_write("my health: %d, enemy health %d .." % (self.my_current_health, self.enemy_current_health))
        gamelib.debug_write("==================================================")
        gamelib.debug_write("my resources: %f bits, %f cores .." % (self.my_current_resources['BITS'],
                                                                    self.my_current_resources['CORES']))
        gamelib.debug_write("enemy resources: %f bits, %f cores .." % (self.enemy_current_resources['BITS'],
                                                                       self.enemy_current_resources['CORES']))
        gamelib.debug_write("==================================================")
        gamelib.debug_write("My Defenses: ")
        gamelib.debug_write(self.my_current_defenses)
        gamelib.debug_write("Enemy Defenses: ")
        gamelib.debug_write(self.enemy_current_defenses)
        gamelib.debug_write("==================================================o")

    def build_skeleton(self, game_state):
        """ strategy at the first round: build up basic skeleton defense
        :param game_state: game state
        :return: None
        """
        # add one filter to block attacks only in the first round
        game_state.attempt_spawn(FILTER, [13, 7])
        game_state.attempt_remove([14, 7])

        # deploy skeleton destructors
        for destructor_location in self.defense_v0[DESTRUCTOR]:
            game_state.attempt_spawn(DESTRUCTOR, destructor_location)

        # deploy skeleton filters as many as we can
        for filter_location in self.defense_v0[FILTER]:
            game_state.attempt_spawn(FILTER, filter_location)

    def check_my_region(self, game_state, location):
        """ check the given location is in which region of enemy's territory
        possible regions are [0, 1], [1, 1], [2, 1], [3, 1], [1, 0], [2, 0]
        :param game_state: current game state
        :param location: [x, y]
        :return: None or a list: [row, col] represents the region
        """
        if not isinstance(location, list) or len(location) != 2:
            gamelib.debug_write("an invalid argument in check_which_region()!")
            return None

        x, y = location
        if not game_state.game_map.in_arena_bounds(location) or y >= game_state.game_map.HALF_ARENA:
            return None

        return [int(x/7), int(y/7)]

    def check_enemy_region(self, game_state, location):
        """ check the given location is in which region of my territory
        possible regions are [0, 0], [1, 0], [2, 0], [3, 0], [1, 1], [2, 1]
        :param game_state: current game state
        :param location: [x, y]
        :return: None or a list: [row, col] represents the region
        """
        if not isinstance(location, list) or len(location) != 2:
            gamelib.debug_write("an invalid argument in check_which_region()!")
            return None

        x, y = location
        if not game_state.game_map.in_arena_bounds(location) or y < game_state.game_map.HALF_ARENA:
            return None

        return [int(x/7), int((y - game_state.game_map.HALF_ARENA)/7)]

    def collect_enemy_regional_defense(self, game_state):
        """ analyze enemy defense skeleton at the first round in general
        we divide the enemy's territory into 6 parts (evenly) and compute
        the defensive power (DESTRUCTOR) and the permeability (FILTER &
        DESTRUCTOR & ENCRYPTOR) in each.
        :param game_state: game state
        :return: None
        """
        # init
        for region in self.enemy_regions:
            self.enemy_regional_defense_summary['permeability'][str(region)] = 0
            self.enemy_regional_defense_summary['defense'][str(region)] = 0

        # loop through filters
        for filter_location in self.enemy_current_defenses[FILTER].keys():
            key = str(self.check_enemy_region(game_state, json.loads(filter_location)))
            self.enemy_regional_defense_summary['permeability'][key] += 1

        # loop through encryptors
        for encryptor_location in self.enemy_current_defenses[ENCRYPTOR].keys():
            key = str(self.check_enemy_region(game_state, json.loads(encryptor_location)))
            self.enemy_regional_defense_summary['permeability'][key] += 1

        # loop through destructors
        for destructor_location in self.enemy_current_defenses[DESTRUCTOR].keys():
            key = str(self.check_enemy_region(game_state, json.loads(destructor_location)))
            self.enemy_regional_defense_summary['permeability'][key] += 1
            # hard-coded
            affected_locations = game_state.game_map.get_locations_in_range(json.loads(destructor_location), 3.5)
            for location in affected_locations:
                key2 = self.check_enemy_region(game_state, location)
                if key2 is not None:
                    self.enemy_regional_defense_summary['defense'][str(key2)] += 1

    def attempt_first_attack(self, game_state):
        """ find a good strategy to perform sudden attack,
        the goal is to maximize the damage and gain advantage
        in the beginning (8.3 BITS)
        :param game_state: game state
        :return: which type of attack to perform:
                 0(attack left edge),
                 1(attack right edge),
                 -1 (no attack).
        """

        """attack from corner with PINGs?"""
        # find the best starting point
        possible_start_locations = [[13, 0], [12, 1], [14, 0], [15, 1]]
        predicted_damages = []
        for start_location in possible_start_locations:
            if start_location[0] < game_state.HALF_ARENA:
                path_to_enemy = game_state.find_path_to_edge(start_location, game_state.game_map.TOP_RIGHT)
            else:
                path_to_enemy = game_state.find_path_to_edge(start_location, game_state.game_map.TOP_LEFT)
            # if the path is too long, it suffers too much risks
            if len(path_to_enemy) > 32:
                predicted_damages.append(float('inf'))
                continue
            else:
                damage = 0
            for each_step in path_to_enemy:
                x, y = each_step
                if y < game_state.HALF_ARENA - 3:
                    # no threat
                    continue
                else:
                    locations_around = game_state.game_map.get_locations_in_range(each_step, 3.5)  # hard-coded
                    for location in self.enemy_current_defenses[DESTRUCTOR]:
                        if json.loads(location) in locations_around:
                            damage += (4 * 2)
            predicted_damages.append(damage)

        # threshold the damage
        min_damage = min(predicted_damages)
        min_index = predicted_damages.index(min_damage)
        num_of_units = game_state.number_affordable(PING)
        predicted_attack = int((num_of_units * 15 - min_damage) / 15.)  # hard-coded

        if predicted_attack >= 5:
            # launch the attack now!
            start_location = possible_start_locations[min_index]
            game_state.attempt_spawn(PING, start_location, num_of_units)
            if start_location[0] < game_state.HALF_ARENA:
                # attack right corner
                return 0
            else:
                # attack left corner
                return 1

        """attack enemy defenses using EMPs & scrambler?"""
        EMP_start_locations = [[3, 10], [13, 0], [24, 10], [14, 0]]
        scrambler_start_locations = [[4, 9], [12, 1], [23, 9], [15, 1]]
        predicted_damages_to_enemy = []
        for start_location in EMP_start_locations:
            if start_location[0] < game_state.HALF_ARENA:
                path_to_enemy = game_state.find_path_to_edge(start_location, game_state.game_map.TOP_RIGHT)
            else:
                path_to_enemy = game_state.find_path_to_edge(start_location, game_state.game_map.TOP_LEFT)
            # shouldn't move towards enemy's territory directly
            if len(path_to_enemy) < 3 or path_to_enemy[1][1] >= game_state.HALF_ARENA - 3 or path_to_enemy[2][1] >= game_state.HALF_ARENA - 3:
                predicted_damages_to_enemy.append(-1.)
                continue
            else:
                damage = 0
            for each_step in path_to_enemy:
                locations_around = game_state.game_map.get_locations_in_range(each_step, 5.5)  # hard-coded
                for location in locations_around:
                    if location[1] >= game_state.HALF_ARENA and game_state.contains_stationary_unit(location):
                        damage += (3 * 4)
            predicted_damages_to_enemy.append(damage)

        max_damage = max(predicted_damages_to_enemy)
        max_index = predicted_damages_to_enemy.index(max_damage)

        # launch EMP attack now!
        if max_damage > 0:
            EMP_start_location = EMP_start_locations[max_index]
            scrambler_start_location = scrambler_start_locations[max_index]
            game_state.attempt_spawn(EMP, EMP_start_location, 2)
            game_state.attempt_spawn(EMP, scrambler_start_location, 2)
            if EMP_start_location[0] < game_state.HALF_ARENA:
                # attack right
                return 0
            else:
                # attack left
                return 1

        # otherwise, save the bits and no attack
        return -1

    def execute_my_strategy(self, game_state):
        """ adaptive strategy
        :param game_state: game state
        :return: None
        """
        # calculate the damages at each part
        left_corner_damage, right_corner_damage, \
        mid_left_damage, mid_right_damage = \
            self.calculate_my_regional_damages(game_state)
        damages = [left_corner_damage, mid_left_damage,
                   mid_right_damage, right_corner_damage]

        self.attempt_attack(game_state, damages)
        self.deploy_defense(game_state, damages)

    def calculate_my_regional_damages(self, game_state):
        """ calculate the regional damage to tell which part need
            to be strengthened in particular
        :param game_state: current game state
        :return: mean damages at left/right corner, mid-left/mid-right
        """
        n0 = 1e-5
        n1 = 1e-5
        n2 = 1e-5
        n3 = 1e-5
        left_corner_damage = 0.
        right_corner_damage = 0.
        mid_left_damage = 0.
        mid_right_damage = 0.

        # FILTER
        prev_only_filter_locations = list(set(self.my_previous_defenses[FILTER].keys()) -
                                          set(self.my_current_defenses[FILTER].keys()))
        cur_only_filter_locations = list(set(self.my_current_defenses[FILTER].keys()) -
                                         set(self.my_previous_defenses[FILTER].keys()))
        common_filter_locations = list(set(self.my_current_defenses[FILTER].keys()).
                                       intersection(set(self.my_previous_defenses[FILTER].keys())))

        # filters that being destroyed
        for location in prev_only_filter_locations:
            filter_damage = self.my_previous_defenses[FILTER][location]
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += filter_damage
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += filter_damage
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += filter_damage
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += filter_damage
                n3 += 1.

        # new filters that being disrupted
        for location in cur_only_filter_locations:
            cur_filter_stability = self.my_current_defenses[FILTER][location]
            # hard-coded
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += (60. - cur_filter_stability)
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += (60. - cur_filter_stability)
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += (60. - cur_filter_stability)
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += (60. - cur_filter_stability)
                n3 += 1.

        # old filters that being disrupted
        for location in common_filter_locations:
            prev_filter_stability = self.my_previous_defenses[FILTER][location]
            cur_filter_stability = self.my_current_defenses[FILTER][location]
            if prev_filter_stability - cur_filter_stability >= 0:
                filter_damage = prev_filter_stability - cur_filter_stability
            else:
                filter_damage = prev_filter_stability + (60. - cur_filter_stability) # hard-coded
            # hard-coded
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += filter_damage
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += filter_damage
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += filter_damage
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += filter_damage
                n3 += 1.

        # DESTRUCTOR
        prev_only_destructor_locations = list(set(self.my_previous_defenses[DESTRUCTOR].keys()) -
                                              set(self.my_current_defenses[DESTRUCTOR].keys()))
        cur_only_destructor_locations = list(set(self.my_current_defenses[DESTRUCTOR].keys()) -
                                             set(self.my_previous_defenses[DESTRUCTOR].keys()))
        common_destructor_locations = list(set(self.my_current_defenses[DESTRUCTOR].keys()).
                                           intersection(set(self.my_previous_defenses[DESTRUCTOR].keys())))

        # destructors that being destroyed
        for location in prev_only_destructor_locations:
            destructor_damage = self.my_previous_defenses[DESTRUCTOR][location]
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += destructor_damage
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += destructor_damage
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += destructor_damage
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += destructor_damage
                n3 += 1.

        # new destructors that being disrupted
        for location in cur_only_destructor_locations:
            cur_destructor_stability = self.my_current_defenses[DESTRUCTOR][location]
            # hard-coded
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += (75. - cur_destructor_stability)
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += (75. - cur_destructor_stability)
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += (75. - cur_destructor_stability)
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += (75. - cur_destructor_stability)
                n3 += 1.

        # old destructors that being disrupted
        for location in common_destructor_locations:
            prev_destructor_stability = self.my_previous_defenses[DESTRUCTOR][location]
            cur_destructor_stability = self.my_current_defenses[DESTRUCTOR][location]
            if prev_destructor_stability - cur_destructor_stability >= 0:
                destructor_damage = prev_destructor_stability - cur_destructor_stability
            else:
                destructor_damage = prev_destructor_stability + (75. - cur_destructor_stability)  # hard-coded
            # hard-coded
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += destructor_damage
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += destructor_damage
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += destructor_damage
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += destructor_damage
                n3 += 1.

        # ENCRYPTOR
        prev_only_encryptor_locations = list(set(self.my_previous_defenses[ENCRYPTOR].keys()) -
                                             set(self.my_current_defenses[ENCRYPTOR].keys()))
        cur_only_encryptor_locations = list(set(self.my_current_defenses[ENCRYPTOR].keys()) -
                                            set(self.my_previous_defenses[ENCRYPTOR].keys()))
        common_encryptor_locations = list(set(self.my_current_defenses[ENCRYPTOR].keys()).
                                          intersection(set(self.my_previous_defenses[ENCRYPTOR].keys())))

        # encryptors that being destroyed
        for location in prev_only_encryptor_locations:
            encryptor_damage = self.my_previous_defenses[ENCRYPTOR][location]
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += encryptor_damage
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += encryptor_damage
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += encryptor_damage
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += encryptor_damage
                n3 += 1.

        # new encryptors that being disrupted
        for location in cur_only_encryptor_locations:
            cur_encryptor_stability = self.my_current_defenses[ENCRYPTOR][location]
            # hard-coded
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += (30. - cur_encryptor_stability)
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += (30. - cur_encryptor_stability)
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += (30. - cur_encryptor_stability)
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += (30. - cur_encryptor_stability)
                n3 += 1.

        # old encryptors that being disrupted
        for location in common_encryptor_locations:
            prev_encryptor_stability = self.my_previous_defenses[ENCRYPTOR][location]
            cur_encryptor_stability = self.my_current_defenses[ENCRYPTOR][location]
            if prev_encryptor_stability - cur_encryptor_stability >= 0:
                encryptor_damage = prev_encryptor_stability - cur_encryptor_stability
            else:
                encryptor_damage = prev_encryptor_stability + (30. - cur_encryptor_stability)  # hard-coded
            # hard-coded
            if self.check_my_region(game_state, json.loads(location)) == [0, 1]:
                left_corner_damage += encryptor_damage
                n0 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [1, 1]:
                mid_left_damage += encryptor_damage
                n1 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [2, 1]:
                mid_right_damage += encryptor_damage
                n2 += 1.
            elif self.check_my_region(game_state, json.loads(location)) == [3, 1]:
                right_corner_damage += encryptor_damage
                n3 += 1.

        return left_corner_damage/n0, right_corner_damage/n3, mid_left_damage/n1, mid_right_damage/n2

    def deploy_defense(self, game_state, damages):
        """ deploy defense for this round
        :param game_state: game state
        :param damages: regional damages (mean) in the front row
        :return: None
        """
        # if to save the cores for next round
        SAVE_CORES = False

        # deal with the emergencies first
        # (better not to have them)
        # eg. is there a part the the enemy is attacking particularly?

        # set damage threshold to identify weakness
        mean_damage_threshold = 10

        # sort the indices according to damages
        ordered_indices = sorted(range(len(damages)), reverse=True, key=damages.__getitem__)
        front_regional_keys = ['[0, 1]', '[1, 1]', '[2, 1]', '[3, 1]']
        gamelib.debug_write('damages at each region:' + str(damages))
        gamelib.debug_write('ordered indices are:' + str(ordered_indices))

        # deploy regional defenses accordingly
        for i in ordered_indices:
            if damages[i] >= mean_damage_threshold:
                if self.front_regional_defense_level[i] < 3:
                    # increase defense level by one
                    self.front_regional_defense_level[i] += 1
                    # first, we fix skeleton destructors
                    for destructor_location in self.regional_complete_defenses[front_regional_keys[i]][DESTRUCTOR]:
                        game_state.attempt_spawn(DESTRUCTOR, destructor_location)
                    # we add extra defenses from this point
                    # Note: currently we only have DESTRUCTOR
                    # level 1 add-on
                    if self.front_regional_defense_level[i] >= 1:
                        for destructor_location in self.regional_defenses_addon_v0[front_regional_keys[i]][DESTRUCTOR]:
                            if game_state.number_affordable(DESTRUCTOR) > 0:
                                game_state.attempt_spawn(DESTRUCTOR, destructor_location)
                            else:
                                SAVE_CORES = True

                    # we fix skeleton filters here if we don't need to save cores for the next round
                    for filter_location in self.regional_complete_defenses[front_regional_keys[i]][FILTER]:
                        if not SAVE_CORES:
                            game_state.attempt_spawn(FILTER, filter_location)

                    # level 2 add-on
                    if self.front_regional_defense_level[i] >= 2:
                        for destructor_location in self.regional_defenses_addon_v1[front_regional_keys[i]][DESTRUCTOR]:
                            if game_state.number_affordable(DESTRUCTOR) > 0:
                                game_state.attempt_spawn(DESTRUCTOR, destructor_location)
                            else:
                                SAVE_CORES = True

                    # level 3 add-on
                    if self.front_regional_defense_level[i] >= 3:
                        for destructor_location in self.regional_defenses_addon_v2[front_regional_keys[i]][DESTRUCTOR]:
                            if game_state.number_affordable(DESTRUCTOR) > 0:
                                game_state.attempt_spawn(DESTRUCTOR, destructor_location)
                            else:
                                SAVE_CORES = True
            else:
                # that means, no server damage
                break

        if SAVE_CORES:
            # don't spend existing cores, save for the next round!
            return

        gamelib.debug_write('front defenses level:' + str(self.front_regional_defense_level))

        # after we take care of the emergencies, we can strengthen
        # the defense in general in terms of the priorities

        # for v0: we deal with destructors first, then filters
        for location in self.defense_v0[DESTRUCTOR]:
            game_state.attempt_spawn(DESTRUCTOR, location)
        for location in self.defense_v0[FILTER]:
            game_state.attempt_spawn(FILTER, location)

        # for v1: key filters that lead the way
        for location in self.defense_v1[FILTER]:
            game_state.attempt_spawn(FILTER, location)

        # for v2: filters first, then destructors
        for location in self.defense_v2[FILTER]:
            game_state.attempt_spawn(FILTER, location)
        for location in self.defense_v2[DESTRUCTOR]:
            game_state.attempt_spawn(DESTRUCTOR, location)

        # for v3: only filters
        for location in self.defense_v3[FILTER]:
            game_state.attempt_spawn(FILTER, location)

        # v4: encryptors first, then filters and destructors
        for location in self.defense_v4[ENCRYPTOR]:
            game_state.attempt_spawn(ENCRYPTOR, location)
        for location in self.defense_v4[FILTER]:
            game_state.attempt_spawn(FILTER, location)
        for location in self.defense_v4[DESTRUCTOR]:
            game_state.attempt_spawn(DESTRUCTOR, location)

        # v5:
        for location in self.defense_v5[ENCRYPTOR]:
            game_state.attempt_spawn(ENCRYPTOR, location)

        # add all add-on DESTRUCTOR
        for region in self.regional_defenses_addon_v0.keys():
            for location in self.regional_defenses_addon_v0[region][DESTRUCTOR]:
                game_state.attempt_spawn(DESTRUCTOR, location)

    def attempt_attack(self, game_state, damages):
        """attempt attack for this round
        :param game_state: game state
        :param damages: regional damages (mean) in the front row
        :return: None
        """
        # sort the regional damage
        ordered_indices = sorted(range(len(damages)), reverse=True, key=damages.__getitem__)
        front_regional_keys = ['[0, 1]', '[1, 1]', '[2, 1]', '[3, 1]']
        my_health_damage_threshold = 5.
        low_defense_threshold = 50
        low_permeability_threshold = 8

        # is there an essential damage to my health?
        # if true, we attempt attack that edge with huge EMPs.
        #   - if we have insufficient bits, we will add a filter
        #   - if we have sufficient bits, we will use EMPs + scrambler to defend
        # if false, we will leave it, and our attack will be based on other info
        if self.my_previous_health - self.my_current_health >= my_health_damage_threshold:
            # this draws our attention, we will try to figure it out
            if front_regional_keys[ordered_indices[0]] in ['[0, 1]', '[1, 1]']:
                # left part damage
                if self.my_current_resources['BITS'] >= 10:
                    # sufficient bits: deploy effective EMP-oriented attack
                    game_state.attempt_spawn(EMP, [24, 10], 3)
                    num_of_scramblers = game_state.number_affordable(SCRAMBLER)
                    game_state.attempt_spawn(SCRAMBLER, [23, 9], num_of_scramblers)
                else:
                    # insufficient bits: manually set some defenses
                    if front_regional_keys[ordered_indices[0]] == '[0, 1]':
                        # left corner attacked, try to overwrite the filter spot with destructor
                        if game_state.can_spawn(DESTRUCTOR, [0, 13]):
                            game_state.attempt_spawn(DESTRUCTOR, [0, 13])
                        else:
                            game_state.attempt_spawn(DESTRUCTOR, [1, 13])
                    else:
                        # mid-left attacked, add a filter to block the way
                        if game_state.can_spawn(DESTRUCTOR, [9, 12]):
                            game_state.attempt_spawn(DESTRUCTOR, [9, 12])
                            game_state.attempt_remove([9, 12])
                        else:
                            game_state.attempt_spawn(FILTER, [9, 12])
                            game_state.attempt_remove([9, 12])

            else:
                # right part damage
                if self.my_current_resources['BITS'] >= 10:
                    # deploy effective EMP-oriented attack
                    game_state.attempt_spawn(EMP, [3, 10], 3)
                    num_of_scramblers = game_state.number_affordable(SCRAMBLER)
                    game_state.attempt_spawn(SCRAMBLER, [4, 9], num_of_scramblers)
                else:
                    # insufficient bits: manually set some defenses
                    if front_regional_keys[ordered_indices[0]] == '[3, 1]':
                        # right corner attacked, try to overwrite the filter spot with destructor
                        if game_state.can_spawn(DESTRUCTOR, [27, 13]):
                            game_state.attempt_spawn(DESTRUCTOR, [27, 13])
                        else:
                            game_state.attempt_spawn(DESTRUCTOR, [26, 13])
                    else:
                        # mid-right attacked, add a filter to block the way
                        if game_state.can_spawn(DESTRUCTOR, [18, 12]):
                            game_state.attempt_spawn(DESTRUCTOR, [18, 12])
                            game_state.attempt_remove([18, 12])
                        else:
                            game_state.attempt_spawn(FILTER, [18, 12])
                            game_state.attempt_remove([18, 12])

        else:
            # ok -- no worries now, we should pay more attention to better attack our enemies
            if self.my_current_resources['BITS'] < 7:
                return

            # collect enemy regional defense info
            self.collect_enemy_regional_defense(game_state)
            left_corner_defense = self.enemy_regional_defense_summary['defense']['[0, 0]']
            left_corner_permeability = self.enemy_regional_defense_summary['permeability']['[0, 0]']
            right_corner_defense = self.enemy_regional_defense_summary['defense']['[3, 0]']
            right_corner_permeability = self.enemy_regional_defense_summary['permeability']['[3, 0]']

            # direction of attack
            if left_corner_defense + left_corner_permeability < right_corner_defense + right_corner_permeability:
                attack_direction = 0  # attack left
                corner_defense = left_corner_defense
                corner_permeability = left_corner_permeability
            else:
                attack_direction = 1  # attack right
                corner_defense = right_corner_defense
                corner_permeability = right_corner_permeability

            # type of attack
            if corner_defense <= low_defense_threshold and corner_permeability <= low_permeability_threshold:
                attack_type = 0  # use PINGs
            else:
                attack_type = 1  # use EMPs + scrambler

            # build one filter to block the way
            if attack_direction:
                game_state.attempt_spawn(FILTER, [9, 12])
                game_state.attempt_remove([9, 12])
            else:
                game_state.attempt_spawn(FILTER, [18, 12])
                game_state.attempt_remove([18, 12])

            # deploy attack
            primary_position = [[24, 10], [3, 10]]
            auxiliary_position = [[23, 9], [4, 9]]
            if attack_type:
                # use EMPs + scrambler
                if self.my_current_resources['BITS'] < 8:
                    game_state.attempt_spawn(EMP, primary_position[attack_direction], 2)
                    game_state.attempt_spawn(SCRAMBLER, auxiliary_position[attack_direction], 1)
                elif self.my_current_resources['BITS'] < 9:
                    game_state.attempt_spawn(EMP, primary_position[attack_direction], 2)
                    game_state.attempt_spawn(SCRAMBLER, auxiliary_position[attack_direction], 2)
                elif self.my_current_resources['BITS'] < 10:
                    game_state.attempt_spawn(EMP, primary_position[attack_direction], 2)
                    game_state.attempt_spawn(SCRAMBLER, auxiliary_position[attack_direction], 3)
                elif self.my_current_resources['BITS'] < 11:
                    game_state.attempt_spawn(EMP, primary_position[attack_direction], 3)
                    game_state.attempt_spawn(SCRAMBLER, auxiliary_position[attack_direction], 1)
                elif self.my_current_resources['BITS'] < 12:
                    game_state.attempt_spawn(EMP, primary_position[attack_direction], 3)
                    game_state.attempt_spawn(SCRAMBLER, auxiliary_position[attack_direction], 2)
                else:
                    # we trust in a troop of PINGs instead
                    num_of_unit = game_state.number_affordable(PING)
                    game_state.attempt_spawn(PING, primary_position[attack_direction], num_of_unit)
            else:
                # use PINGs
                num_of_unit = game_state.number_affordable(PING)
                game_state.attempt_spawn(PING, primary_position[attack_direction], num_of_unit)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
