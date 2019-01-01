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
        self.collect_info_deploy(game_state, verbose)

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

    def on_action(self, action_state):
        """ This function is called every turn at the action phase I suppose
        """
        verbose = 0  # if to report at each round (you don't want to set it to True)
        action_state_dict = json.loads(action_state)
        self.collect_info_action(action_state_dict, verbose)

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def create_collectors(self):
        """ create collectors that gather the information
        :return: None
        """
        # deploy phase collectors
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

        # action phase collectors
        # analysis of enemy strategy
        self.enemy_blackbeard = 0           # does enemy use blackbeard-alike algorithm?
        self.enemy_madrox = 0               # does enemy use madrox-alike algorithm?
        self.enemy_attack_paths_p1 = {}     # paths on my side
        self.enemy_attack_paths_p2 = {}     # paths on enemy's side
        self.enemy_attack_frames_p1 = {}    # attack frames on my side
        self.enemy_attack_frames_p2 = {}    # attack frames on enemy's side
        self.enemy_attack_breaches = []     # breaches of attacks
        self.enemy_attack_starts_history = []  # history of the starting points of enemy's attacks

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

    def collect_info_deploy(self, game_state, verbose=0):
        """ collect information of last battle (FROM DEPLOY PHASE)
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

    def collect_info_action(self, action_state, verbose=0):
        """ collect information (FROM ACTION PHASE)
        :param action_state: current action state
        :param verbose: if to print out the info
        :return: None
        """
        # unit types (in strings)
        unit_types = [PING, EMP, SCRAMBLER]
        unit_speeds = [2, 4, 4]

        # check the frame id, if it is 0, we need to do extra work
        frame_id = int(action_state['turnInfo'][2])
        if frame_id == 0:
            # we need to renew our collector on frame 0!
            self.enemy_attack_paths_p1 = {PING: {}, EMP: {}, SCRAMBLER: {}}
            self.enemy_attack_paths_p2 = {PING: {}, EMP: {}, SCRAMBLER: {}}
            self.enemy_attack_frames_p1 = {PING: {}, EMP: {}, SCRAMBLER: {}}
            self.enemy_attack_frames_p2 = {PING: {}, EMP: {}, SCRAMBLER: {}}
            self.enemy_attack_breaches = []

        for unit_info in action_state['events']['move']:
            # parse the unit information
            cur_pos, next_pos, _, unit_type_idx, unit_id, player_id = unit_info
            dframe = unit_speeds[unit_type_idx - 3]
            if player_id == 2:
                # this is an information unit from the enemy
                if unit_id not in self.enemy_attack_paths_p1[unit_types[unit_type_idx - 3]].keys():
                    self.enemy_attack_paths_p1[unit_types[unit_type_idx - 3]][unit_id] = []
                    self.enemy_attack_paths_p2[unit_types[unit_type_idx - 3]][unit_id] = [cur_pos]
                    self.enemy_attack_frames_p1[unit_types[unit_type_idx - 3]][unit_id] = []
                    self.enemy_attack_frames_p2[unit_types[unit_type_idx - 3]][unit_id] = [frame_id]
                    if cur_pos not in self.enemy_attack_starts_history:
                        self.enemy_attack_starts_history.append(cur_pos)

                if next_pos[1] < 14:
                    self.enemy_attack_paths_p1[unit_types[unit_type_idx - 3]][unit_id].append(next_pos)
                    self.enemy_attack_frames_p1[unit_types[unit_type_idx - 3]][unit_id].append(frame_id+dframe)
                else:
                    self.enemy_attack_paths_p2[unit_types[unit_type_idx - 3]][unit_id].append(next_pos)
                    self.enemy_attack_frames_p2[unit_types[unit_type_idx - 3]][unit_id].append(frame_id+dframe)

        # breaches on this turn
        for unit_info in action_state['events']['breach']:
            breach_pos, _, _, _, player_id = unit_info
            if player_id == 2 and breach_pos not in self.enemy_attack_breaches:
                self.enemy_attack_breaches.append(breach_pos)

        if verbose:
            self.display_enemy_attack_info()

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

    def display_enemy_attack_info(self):
        """ display the attacking paths that our enemy's
            information unit took in the last round
        :return: None
        """
        # My side
        # PINGs
        gamelib.debug_write("ON PLAYER 1 SIDE:")
        gamelib.debug_write("====================================")
        gamelib.debug_write("PINGs:")
        for ping_id in self.enemy_attack_paths_p1[PING].keys():
            gamelib.debug_write("PING ID: "+ping_id)
            gamelib.debug_write(self.enemy_attack_frames_p1[PING][ping_id])
            gamelib.debug_write(self.enemy_attack_paths_p1[PING][ping_id])
        # EMPs
        gamelib.debug_write("====================================")
        gamelib.debug_write("EMPs:")
        for emp_id in self.enemy_attack_paths_p1[EMP].keys():
            gamelib.debug_write("PING ID: "+emp_id)
            gamelib.debug_write(self.enemy_attack_frames_p1[EMP][emp_id])
            gamelib.debug_write(self.enemy_attack_paths_p1[EMP][emp_id])
        # SCRAMBLERs
        gamelib.debug_write("====================================")
        gamelib.debug_write("SCRAMBLERs:")
        for scrambler_id in self.enemy_attack_paths_p1[SCRAMBLER].keys():
            gamelib.debug_write("PING ID: "+scrambler_id)
            gamelib.debug_write(self.enemy_attack_frames_p1[SCRAMBLER][scrambler_id])
            gamelib.debug_write(self.enemy_attack_paths_p1[SCRAMBLER][scrambler_id])
        gamelib.debug_write("====================================")

        # enemy's side
        gamelib.debug_write("ON PLAYER 2 SIDE:")
        gamelib.debug_write("====================================")
        gamelib.debug_write("PINGs:")
        for ping_id in self.enemy_attack_paths_p2[PING].keys():
            gamelib.debug_write("PING ID: " + ping_id)
            gamelib.debug_write(self.enemy_attack_frames_p2[PING][ping_id])
            gamelib.debug_write(self.enemy_attack_paths_p2[PING][ping_id])
        # EMPs
        gamelib.debug_write("====================================")
        gamelib.debug_write("EMPs:")
        for emp_id in self.enemy_attack_paths_p2[EMP].keys():
            gamelib.debug_write("PING ID: " + emp_id)
            gamelib.debug_write(self.enemy_attack_frames_p2[EMP][emp_id])
            gamelib.debug_write(self.enemy_attack_paths_p2[EMP][emp_id])
        # SCRAMBLERs
        gamelib.debug_write("====================================")
        gamelib.debug_write("SCRAMBLERs:")
        for scrambler_id in self.enemy_attack_paths_p2[SCRAMBLER].keys():
            gamelib.debug_write("PING ID: " + scrambler_id)
            gamelib.debug_write(self.enemy_attack_frames_p2[SCRAMBLER][scrambler_id])
            gamelib.debug_write(self.enemy_attack_paths_p2[SCRAMBLER][scrambler_id])
        gamelib.debug_write("====================================")
        gamelib.debug_write("BREACHES AT THIS ROUND:")
        gamelib.debug_write(self.enemy_attack_breaches)
        gamelib.debug_write("====================================")

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
        info = self.analyze_enemy_strategy(game_state)

        if self.enemy_blackbeard:
            # blackbeard-alike
            self.deploy_strategy_for_blackbeard(game_state, info)

        if self.enemy_madrox:
            # madrox-alike
            self.deploy_strategy_for_madrox(game_state, info)

        if not self.enemy_blackbeard and not self.enemy_madrox:
            # classify as normal strategy
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

    def analyze_enemy_strategy(self, game_state):
        """ analyze enemy's strategy (identify madrox & blackbeard)
            in particular
        :param game_state: current game_state
        :return: a dict of information
        """
        # we set to normal as default
        default_dict = {}

        # find out if enemy use blackbeard-alike algorithm
        channel_length_threshold = 10
        gamelib.debug_write("=====================================")
        gamelib.debug_write("TRY TO IDENTIFY BLACKBEARD ...")
        blackbeard_dict = self.detect_blackbeard(game_state, channel_length_threshold)
        default_dict['blackbeard'] = blackbeard_dict
        self.enemy_blackbeard = blackbeard_dict['is_blackbeard']
        if self.enemy_blackbeard:
            gamelib.debug_write("BLACKBEARD DETECTED !!!!")

        # find if enemy use madrox-alike algorithm
        wall_length_threshold = 12
        gamelib.debug_write("=====================================")
        gamelib.debug_write("TRY TO IDENTIFY MADROX ...")
        madrox_dict = self.detect_madrox(game_state, wall_length_threshold)
        default_dict['madrox'] = madrox_dict
        self.enemy_madrox = madrox_dict['is_madrox']
        if self.enemy_madrox:
            gamelib.debug_write("MADROX DETECTED !!!!")
        gamelib.debug_write("=====================================")

        return default_dict

    def detect_blackbeard(self, game_state, len_threshold):
        """ detect blackbeard-alike algorithm
        :param game_state: game state
        :param len_threshold: channel length threshold
        :return: a dictionary contains the information
        """
        blackbeard_dict = {'is_blackbeard': False, 'on_left': None}
        left_channel = [[14-i, 26-i] for i in range(13)]
        right_channel = [[13+i, 26-i] for i in range(13)]
        left_cnt = right_cnt = 0

        # count left
        for location in left_channel:
            if game_state.contains_stationary_unit(location):
                left_cnt += 1

        # count right
        for location in right_channel:
            if game_state.contains_stationary_unit(location):
                right_cnt += 1

        max_cnt = max([left_cnt, right_cnt])

        # detect other types of attacks
        blackbeard_left_attack = True
        blackbeard_right_attack = True
        left_pool = [[0, 14], [1, 14], [2, 14], [1, 15], [2, 15], [2, 16], [3, 16]]
        right_pool = [[25, 14], [26, 14], [27, 14], [25, 15], [26, 15], [24, 16], [25, 16]]
        for unit_type in self.enemy_attack_paths_p2.keys():
            for unit_id in self.enemy_attack_paths_p2[unit_type].keys():
                path = self.enemy_attack_paths_p2[unit_type][unit_id]
                if not self.locations_not_in_path(left_pool, path):
                    # attacks other than left BB (or at least no threat)
                    blackbeard_left_attack = False
                if not self.locations_not_in_path(right_pool, path):
                    # attacks other than right BB (or at least no threat)
                    blackbeard_right_attack = False

        # blackbeard structure appears!
        if max_cnt >= len_threshold:
            if left_cnt == max_cnt and blackbeard_left_attack:
                blackbeard_dict['is_blackbeard'] = True
                blackbeard_dict['on_left'] = True
            elif right_cnt == max_cnt and blackbeard_right_attack:
                blackbeard_dict['is_blackbeard'] = True
                blackbeard_dict['on_left'] = False

        return blackbeard_dict

    def detect_madrox(self, game_state, len_threshold):
        """ detect the suspicious walls in the enemy's front rows:
            level 0: j=14, level 1: j=15, level 2: j=16, level 3: j=17
        :param game_state: game state
        :param len_threshold: length threshold to be regarded as a 'wall'
        :return: a dictionary contains the wall information
        """
        enemy_front_row_idxs = [14, 15, 16, 17]
        wall_dict = {'is_madrox': False, 'walls': {}}
        wall_dict['walls']['0'] = []
        wall_dict['walls']['1'] = []
        wall_dict['walls']['2'] = []
        wall_dict['walls']['3'] = []

        # check walls using enemy's stationary units information
        # i.e. check the longest consecutive stationary units
        for idx in enemy_front_row_idxs:
            # renew some parameters
            start = idx - game_state.HALF_ARENA
            end = game_state.ARENA_SIZE - start
            i = j = start
            # find the longest consecutive section
            while i < end:
                while j + 1 < end and game_state.contains_stationary_unit([j+1, idx]):
                    j += 1
                # update
                if j - i + 1 >= len_threshold:
                    wall_dict['is_madrox'] = True
                    wall_dict['walls'][str(idx-14)].append([i, j])
                # next round
                j += 1
                i = j

        # if there's no explicit walls, we need to double check the
        # paths of enemy's attacking information units, because some
        # structures are not walls explicitly, but they function as
        # walls in reality
        if not wall_dict['is_madrox']:
            for unit_type in self.enemy_attack_paths_p2.keys():
                for unit_id in self.enemy_attack_paths_p2[unit_type].keys():
                    path = self.enemy_attack_paths_p2[unit_type][unit_id]
                    i = j = 0
                    while i < len(path) - 1:
                        y = path[i][1]
                        while j + 1 < len(path) - 1 and path[j+1][1] == y:
                            # move horizontally
                            j += 1
                        # update
                        if j - i + 1 >= len_threshold and 14 < y <= 18:
                            wall_dict['is_madrox'] = True
                            left = path[i][0]
                            right = path[j][0]
                            wall_dict['walls'][str(y-15)].append([left, right])
                        # next round
                        j += 1
                        i = j

        return wall_dict

    def deploy_strategy_for_blackbeard(self, game_state, info):
        """ deploy strategy in particular for blackbeard-alike algorithms
        :param game_state: current game_state
        :param info: a dict of information
        :return: None
        """
        left_walls = [[i, 13-i] for i in range(4)]
        left_extended_walls = [[4+i, 9-i] for i in range(4)]
        left_auxiliray_destructors = [[3, 13], [4, 13]]
        left_encryptors = [[4, 12], [5, 11], [6, 10]]
        left_auxiliray_encryptors = [[5, 12], [6, 11]]
        left_channel = [[1+i, 13-i] for i in range(14)] + [[2+i, 13-i] for i in range(13)]
        left_attack = [14, 0]

        right_walls = [[27-i, 13-i] for i in range(4)]
        right_extended_walls = [[23-i, 9-i] for i in range(4)]
        right_auxiliray_destructors = [[24, 13], [23, 13]]
        right_encryptors = [[23, 12], [22, 11], [21, 10]]
        right_auxiliray_encryptors = [[22, 12], [21, 11]]
        right_channel = [[26-i, 13-i] for i in range(14)] + [[25-i, 13-i] for i in range(13)]
        right_attack = [13, 0]

        if info['blackbeard']['on_left']:
            BB_walls = left_walls
            BB_extended_walls = left_extended_walls
            BB_auxiliray_destructors = left_auxiliray_destructors
            BB_encryptors = left_encryptors
            BB_auxiliray_encryptors = left_auxiliray_encryptors
            BB_channel = left_channel
            BB_attack = left_attack
        else:
            BB_walls = right_walls
            BB_extended_walls = right_extended_walls
            BB_auxiliray_destructors = right_auxiliray_destructors
            BB_encryptors = right_encryptors
            BB_auxiliray_encryptors = right_auxiliray_encryptors
            BB_channel = right_channel
            BB_attack = right_attack

        # clear the channel
        no_units_in_channel = 1
        for location in BB_channel:
            if game_state.contains_stationary_unit(location):
                no_units_in_channel = 0  # we cannot attack this round
                game_state.attempt_remove(location)

        # construct defenses in terms of priority
        # check essential destructors (if bad we replace them)
        x, y = map(int, BB_walls[0])
        if game_state.contains_stationary_unit(BB_walls[0]):
            unit = game_state.game_map[x, y][0]
            if unit.unit_type is not DESTRUCTOR or unit.stability <= 37.5:
                game_state.attempt_remove(BB_walls[0])

        x, y = map(int, BB_auxiliray_destructors[0])
        if game_state.contains_stationary_unit(BB_auxiliray_destructors[0]):
            unit = game_state.game_map[x, y][0]
            if unit.unit_type is not DESTRUCTOR or unit.stability <= 37.5:
                game_state.attempt_remove(BB_auxiliray_destructors[0])

        # build up critical walls
        for location in BB_walls:
            if game_state.contains_stationary_unit(location):
                x, y = map(int, location)
                unit = game_state.game_map[x, y][0]
                if unit.unit_type is not DESTRUCTOR:
                    game_state.attempt_remove(location)
            else:
                    game_state.attempt_spawn(DESTRUCTOR, location)

        # build up essential encryptors
        if self.my_current_resources['BITS'] >= 10:
            for location in BB_encryptors:
                if game_state.contains_stationary_unit(location):
                    x, y = map(int, location)
                    unit = game_state.game_map[x, y][0]
                    if unit.unit_type is not ENCRYPTOR:
                        game_state.attempt_remove(location)
                else:
                    game_state.attempt_spawn(ENCRYPTOR, location)

        # build up auxiliary destructors
        for location in BB_auxiliray_destructors:
            game_state.attempt_spawn(DESTRUCTOR, location)

        # build up extended walls
        need_extended_walls = (self.my_current_health < self.my_previous_health)
        if need_extended_walls:
            for location in BB_extended_walls:
                if game_state.contains_stationary_unit(location):
                    if int(location[1]) % 2 == 0:
                        x, y = map(int, location)
                        if game_state.game_map[x, y][0].unit_type is not DESTRUCTOR:
                            game_state.attempt_remove(location)
                else:
                    if int(location[1]) % 2 == 0:
                        game_state.attempt_spawn(DESTRUCTOR, location)
                    else:
                        game_state.attempt_spawn(FILTER, location)

        # build up auxiliary encryptors
        if self.my_current_resources['BITS'] >= 10:
            for location in BB_auxiliray_encryptors:
                game_state.attempt_spawn(ENCRYPTOR, location)

        # launch attack
        if self.my_current_resources['BITS'] < 10:
            return
        else:
            if no_units_in_channel:
                num_of_units = game_state.number_affordable(PING)
                game_state.attempt_spawn(PING, BB_attack, num_of_units)

    def deploy_strategy_for_madrox(self, game_state, info):
        """ deploy strategy in particular for madrox-alike algorithms
        :param game_state: current game state
        :param info: a dict of information
        :return: None
        """
        # the most front row of wall
        enemy_front_row_idxs = [14, 15, 16, 17]
        first_row_idx = None

        # and we will collect the data we use along the way
        first_row_defenses = []
        visited_points_on_my_side = []  # may not in use

        for i in range(4):
            if len(info['madrox']['walls'][str(i)]) > 0:
                first_row_idx = i
                break

        # 1. REMOVE all the stationary units that are not helpful
        n_left_bdry = 0
        n_right_bdry = 0
        for boundaries in info['madrox']['walls'][str(first_row_idx)]:
            # count boundary types for further yse
            left, right = boundaries
            n_left_bdry += (first_row_idx <= left - 1 < 14) + \
                           (first_row_idx <= right + 1 < 14)
            n_right_bdry += (14 <= left - 1 < 28 - first_row_idx) + \
                            (14 <= right + 1 < 28 - first_row_idx)
            # collect defense info for boundaries
            if left - 1 not in first_row_defenses \
                    and first_row_idx <= left - 1 < 28 - first_row_idx:
                first_row_defenses.append(left - 1)
            if right + 1 not in first_row_defenses \
                    and first_row_idx <= right + 1 < 28 - first_row_idx:
                first_row_defenses.append(right + 1)
            # remove redundancies (frugal)
            for i in range(left, right+1):
                # we remove all except for destructors in the first two rows
                for j in range(enemy_front_row_idxs[first_row_idx]-2,
                               enemy_front_row_idxs[first_row_idx]):
                    if j < 14 and game_state.game_map.in_arena_bounds([i, j]) \
                            and game_state.contains_stationary_unit([i, j]):
                        unit = game_state.game_map[i, j][0]
                        if unit.unit_type is not DESTRUCTOR:
                            game_state.attempt_remove([i, j])
                # for others, we remove everything within the EMP range
                for j in range(enemy_front_row_idxs[first_row_idx]-4,
                               enemy_front_row_idxs[first_row_idx]-2):
                    if j < 14 and game_state.game_map.in_arena_bounds([i, j]) \
                            and game_state.contains_stationary_unit([i, j]):
                        game_state.attempt_remove([i, j])

        # display for 1
        gamelib.debug_write('----------------PART 1: DEBUG WRITE BEGINS-----------------')
        gamelib.debug_write('index: ' + str(first_row_idx))
        gamelib.debug_write('with boundaries:' + str(info['madrox']['walls'][str(first_row_idx)]))
        gamelib.debug_write('#left_bdry: ' + str(n_left_bdry) + ' #right_bdry: ' + str(n_right_bdry))
        gamelib.debug_write('----------------PART 1: DEBUG WRITE ENDS-------------------')

        # 2. DETERMINE attacking direction:
        # Our principle is not to break enemy's defense structures but to
        # take advantage of that. So we attack the 'holes'.
        attack_left = None

        # 2.1 first, we check entry point
        n_left_entry = 0
        n_right_entry = 0
        for unit_type in self.enemy_attack_paths_p1.keys():
            for unit_id in self.enemy_attack_paths_p1[unit_type].keys():
                for location in self.enemy_attack_paths_p1[unit_type][unit_id]:
                    # collect visited points
                    if location not in visited_points_on_my_side:
                        visited_points_on_my_side.append(location)
                    # collect entry points
                    if location[1] == 13:
                        if location[0] < 14:
                            n_left_entry += 1
                        else:
                            n_right_entry += 1

        if attack_left is None:
            if n_left_entry > n_left_entry:
                attack_left = True
            elif n_left_entry < n_left_entry:
                attack_left = False

        # 2.2 if we cannot tell through entry points, we check boundaries of walls
        if attack_left is None:
            if n_left_bdry > n_right_bdry:
                attack_left = True
            elif n_left_bdry < n_right_bdry:
                attack_left = False

        # 2.3 if we still cannot determine it, we choose LEFT (which is arbitrary)
        if attack_left is None:
            attack_left = True

        gamelib.debug_write('----------------PART 2: DEBUG WRITE BEGINS-----------------')
        gamelib.debug_write('#left_entry: ' + str(n_left_entry) + ' #right_entry: ' + str(n_right_entry))
        gamelib.debug_write('if to attack on left: ' + str(attack_left))
        gamelib.debug_write('----------------PART 2: DEBUG WRITE ENDS-------------------')

        # 3. DEPLOY DEFENSE
        # some local collectors
        max_length_left = 0
        max_length_right = 0
        enemy_attack_left_paths = []   # possible enemy's attacking paths to our left
        enemy_attack_right_paths = []  # possible enemy's attacking paths to our right
        my_left_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT)
        my_right_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        enemy_left_edges = game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT)
        enemy_right_edges = game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        # find paths that are potential threats
        for start_location in self.enemy_attack_starts_history:
            if start_location in enemy_left_edges:
                path = game_state.find_path_to_edge(start_location, game_state.game_map.BOTTOM_RIGHT)
                if path is not None and len(path) > 0 and path[-1] in my_right_edges:
                    path = [location for location in path if location[1] <= 13]
                    max_length_right = max([max_length_right, len(path)])
                    enemy_attack_right_paths.append(path)
            elif start_location in enemy_right_edges:
                path = game_state.find_path_to_edge(start_location, game_state.game_map.BOTTOM_LEFT)
                if path is not None and len(path) > 0 and path[-1] in my_left_edges:
                    path = [location for location in path if location[1] <= 13]
                    max_length_left = max([max_length_left, len(path)])
                    enemy_attack_left_paths.append(path)

        # 3.1 if enemy hasn't attacked yet or there's no threat,
        # we build some destructors to defend each boundary first,
        # otherwise we build destructors according to such paths
        y_breach_left = 1  # the highest horizon of the right breaches
        y_breach_right = 1  # the highest horizon of the right breaches

        if max_length_left == 0 and max_length_right == 0:
            # which is suspicious
            gamelib.debug_write("ATTENTION: enemy doesn't have a path to attack!")
            for x in first_row_defenses:
                if game_state.contains_stationary_unit([x, 13]):
                    if game_state.game_map[x, 13][0].unit_type is not DESTRUCTOR:
                        game_state.attempt_remove([x, 13])
                else:
                    game_state.attempt_spawn(DESTRUCTOR, [x, 13])
        else:
            # which is the normal case
            finished_left = []  # locations that we already take care of
            finished_right = []  # locations that we already take care of
            for i in range(max([max_length_left, max_length_right])):
                # for left attacks
                for path in enemy_attack_left_paths:
                    # we enhance the defense in a circulate manner
                    idx = i % int(len(path))
                    if path[idx] not in finished_left:
                        if idx == len(path) - 1:
                            # meaning, this is the breach
                            y_breach_left = max(y_breach_left, path[idx][1])
                        else:
                            x, y = map(int, path[idx])
                            enchanced_already = False
                            # Level 1
                            if not enchanced_already:
                                if [x-1, y] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x-1, y]):
                                    if game_state.contains_stationary_unit([x-1, y]):
                                        if game_state.game_map[x-1, y][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x-1, y])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x-1, y])
                                        enchanced_already = True
                                elif [x, y-1] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x, y-1]):
                                    if game_state.contains_stationary_unit([x, y-1]):
                                        if game_state.game_map[x, y-1][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x, y-1])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x, y-1])
                                        enchanced_already = True
                            # Level 2
                            if not enchanced_already:
                                if [x-1, y-1] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x-1, y-1]):
                                    if game_state.contains_stationary_unit([x-1, y-1]):
                                        if game_state.game_map[x-1, y-1][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x-1, y-1])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x-1, y-1])
                                elif [x-2, y] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x-2, y]):
                                    if game_state.contains_stationary_unit([x-2, y]):
                                        if game_state.game_map[x-2, y][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x-2, y])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x-2, y])
                                        # enchanced_already = True
                                elif [x, y-2] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x, y-2]):
                                    if game_state.contains_stationary_unit([x, y-2]):
                                        if game_state.game_map[x, y-2][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x, y-2])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x, y-2])
                                        # enchanced_already = True
                            # Maybe more levels ... ?
                    finished_left.append(path[idx])  # make a mark, not to process repeatedly

                # for right attacks
                for path in enemy_attack_right_paths:
                    # we enhance the defense in a circulate manner
                    idx = i % int(len(path))
                    if path[idx] not in finished_right:
                        if idx == len(path) - 1:
                            # meaning, this is the breach
                            y_breach_right = max(y_breach_right, path[idx][1])
                        else:
                            x, y = map(int, path[idx])
                            enchanced_already = False
                            # Level 1
                            if not enchanced_already:
                                if [x+1, y] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x+1, y]):
                                    if game_state.contains_stationary_unit([x+1, y]):
                                        if game_state.game_map[x+1, y][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x+1, y])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x+1, y])
                                        enchanced_already = True
                                elif [x, y+1] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x, y+1]):
                                    if game_state.contains_stationary_unit([x, y+1]):
                                        if game_state.game_map[x, y+1][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x, y+1])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x, y+1])
                                        enchanced_already = True
                            # Level 2
                            if not enchanced_already:
                                if [x+1, y+1] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x+1, y+1]):
                                    if game_state.contains_stationary_unit([x+1, y+1]):
                                        if game_state.game_map[x+1, y+1][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x+1, y+1])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x+1, y+1])
                                        # enchanced_already = True
                                elif [x+2, y] not in path[idx+1:] and game_state.game_map.in_arena_bounds([x+2, y]):
                                    if game_state.contains_stationary_unit([x+2, y]):
                                        if game_state.game_map[x+2, y][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x+2, y])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x+2, y])
                                        # enchanced_already = True
                                elif [x, y+2] not in path[idx + 1:] and game_state.game_map.in_arena_bounds([x-1, y+2]):
                                    if game_state.contains_stationary_unit([x, y+2]):
                                        if game_state.game_map[x, y+2][0].unit_type is not DESTRUCTOR:
                                            game_state.attempt_remove([x, y+2])
                                    else:
                                        game_state.attempt_spawn(DESTRUCTOR, [x, y+2])
                                        # enchanced_already = True
                            # Maybe more levels ... ?
                    finished_right.append(path[idx])

        # 3.2 build up walls from the highest horizons if we have more cores
        wall_left = range(y_breach_left, 1, -1)
        wall_right = range(y_breach_right, 1, -1)
        for i in range(max([len(wall_left), len(wall_right)])):
            # left wall
            if len(wall_left) > i:
                y = int(wall_left[i])
                x = int(13 - y)
                if y % 2 == 0:
                    game_state.attempt_spawn(FILTER, [x, y])
                else:
                    game_state.attempt_spawn(DESTRUCTOR, [x, y])

            # right wall
            if len(wall_right) > i:
                y = int(wall_right[i])
                x = int(y + 14)
                if y % 2 == 0:
                    game_state.attempt_spawn(FILTER, [x, y])
                else:
                    game_state.attempt_spawn(DESTRUCTOR, [x, y])

        gamelib.debug_write('----------------PART 3: DEBUG WRITE BEGINS-----------------')
        gamelib.debug_write('enemy left attack paths: ')
        gamelib.debug_write(enemy_attack_left_paths)
        gamelib.debug_write('enemy right attack paths: ')
        gamelib.debug_write(enemy_attack_right_paths)
        gamelib.debug_write('left_attack_max_len: '+str(max_length_left))
        gamelib.debug_write('right_attack_max_len: ' + str(max_length_right))
        gamelib.debug_write('highest_breach_on_left: '+str(y_breach_left))
        gamelib.debug_write('highest_breach_on_right: ' + str(y_breach_right))
        gamelib.debug_write('----------------PART 3: DEBUG WRITE ENDS-------------------')

        # 4. DEPLOY ATTACK
        if attack_left:
            my_attack_start = [14, 0]
            enemy_edge = game_state.game_map.TOP_LEFT
            enemy_edge_locations = enemy_left_edges
        else:
            my_attack_start = [13, 0]
            enemy_edge = game_state.game_map.TOP_RIGHT
            enemy_edge_locations = enemy_right_edges

        # if we are short of bits, save it for the next round
        if self.my_current_resources['BITS'] < 10 + int(game_state.turn_number)/10:
            return

        # 4.1 estimate the damage to determine the attack type
        emp_attack = None
        damage_threshold = 50
        path = game_state.find_path_to_edge(my_attack_start, enemy_edge)

        if len(path) >= 14:
            if path[-1] not in enemy_edge_locations:
                gamelib.debug_write("ATTENTION: we use EMP to attack because we "
                                    "cannot get to enemy's edge!")
                emp_attack = True
            else:
                damage = 0.
                for each_step in path:
                    x, y = each_step
                    if y < game_state.HALF_ARENA - 3:
                        # no threat
                        continue
                    else:
                        locations_around = game_state.game_map.get_locations_in_range(each_step, 3.5)  # hard-coded
                        for location in self.enemy_current_defenses[DESTRUCTOR]:
                            if json.loads(location) in locations_around:
                                damage += (4 * 2)
                # check if damage is larger than threshold
                if damage <= damage_threshold:
                    emp_attack = False
                else:
                    gamelib.debug_write("ATTENTION: we use EMP to attack due to large "
                                        "damages along the way!")
                    emp_attack = True
        else:
            # this should be unusual
            gamelib.debug_write("ATTENTION: information units get stuck somewhere!")

        # 4.2 launch the attacks
        if emp_attack is not None:
            if emp_attack:
                num_emp = game_state.number_affordable(EMP)
                game_state.attempt_spawn(EMP, my_attack_start, num_emp)
                num_scrambler = game_state.number_affordable(SCRAMBLER)
                game_state.attempt_spawn(EMP, my_attack_start, num_scrambler)
            else:
                num_ping = game_state.number_affordable(PING)
                game_state.attempt_spawn(PING, my_attack_start, num_ping)

        gamelib.debug_write('----------------PART 4: DEBUG WRITE BEGINS-----------------')
        gamelib.debug_write("the path we take to attack: ")
        gamelib.debug_write(path)
        gamelib.debug_write('----------------PART 4: DEBUG WRITE ENDS-------------------')

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
        # gamelib.debug_write('damages at each region:' + str(damages))
        # gamelib.debug_write('ordered indices are:' + str(ordered_indices))

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

        # gamelib.debug_write('front defenses level:' + str(self.front_regional_defense_level))

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

    def locations_not_in_path(self, locations, path):
        """ identify if at least one of the locations
            is in the specified path
        :param locations: a list of [x, y]
        :param path: a list of [x, y] (a path)
        :return: boolean value
        """
        for location in locations:
            if location in path:
                return True

        return False


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
