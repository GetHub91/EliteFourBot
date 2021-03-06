import copy
import csv
import json
import jsonpickle

move_effectiveness = {}
viable_moves = {}


class Pokemon:
    poke_id = None
    attack = None
    defense = None
    sp_att = None  # sp_att is used as special for gen1 pokemon
    sp_def = None
    speed = None
    maxhp = None
    level = None
    currhp = 1.0
    gen = None
    moveids = []
    types = []
    status = None
    stat_multipliers = None

    def __init__(self, poke_id, attack, defense, sp_att, sp_def, speed, maxhp, level, currhp, gen, moveids, types, status, stat_multipliers):
        self.poke_id = poke_id
        self.attack = attack
        self.defense = defense
        self.sp_att = sp_att
        self.sp_def = sp_def
        self.speed = speed
        self.maxhp = maxhp
        self.level = level
        self.currhp = currhp
        self.gen = gen
        self.moveids = moveids
        self.types = types
        self.status = status
        self.stat_multipliers = stat_multipliers


def calcDamage(attackingPokemon, defendingPokemon, move):
    if attackingPokemon.gen == 1:
        critchance = attackingPokemon.speed / 512 * 8 ** (move.critratio - 1)
        level = attackingPokemon.level * (1 * (
            1 - critchance) + 2 * critchance)  # Expected value for level, taking into account crit chance
        if move.category.lower() == "physical":
            a = attackingPokemon.attack
            d = defendingPokemon.defense
        else:
            a = attackingPokemon.sp_att
            d = defendingPokemon.sp_att
        basedmg = int(int(int(2 * level / 5 + 2) *
                          move.basePower * a / d) / 50 + 2)
        effectivenesses = [move_effectiveness[(
            move.type, def_type)] for def_type in defendingPokemon.types]
        effectiveness = 1
        for e in effectivenesses:
            effectiveness = effectiveness * e
        random = list(range(217, 256))  # all random values
        stab = 1.5 if move.type in attackingPokemon.types else 1
        modifier = stab * effectiveness
        damage_values = [int(basedmg * modifier * r / 255.0) for r in random]
        return sum(damage_values) / len(random)
    else:
        raise (NotImplementedError(
            "Generation {} not implemented yet".format(attackingPokemon.gen)))


def getLegalTeamActions(curr_poke, team_poke):
    actions = []
    for move in team_poke[curr_poke].moveids:
        actions.append(("move", move))
    for poke_id, pokemon in team_poke.items():
        if poke_id != curr_poke and pokemon.currhp > 0:
            actions.append(("switch", poke_id))
    return actions

def getLegalEnemyActions(enemy_poke):
    actions = []
    for move in enemy_poke.moveids:
        actions.append(("move", move))
    return actions

def performActions(p1_pokemon, p2_pokemon, p1action, p2action, team):
    ret = []
    # switch first
    if p1action[0] == "switch" and p2action[0] == "move":
        p1_pokemon = p1action[1]
        ret = viable_moves[p2action[1]].effect(p2_pokemon, p1_pokemon)
    if p2action[0] == "switch" and p2action[0] == "move":
        p2_pokemon = p2action[1]
        ret = viable_moves[p1action[1]].effect(p1_pokemon, p2_pokemon)
    if p1action[0] == "move" and p2action[0] == "move":
        p1move = viable_moves[p1action[1]]
        p2move = viable_moves[p2action[1]]

        # First, compare priorities
        if p1move.priority != p2move.priority:
            if p1move.priority > p2move.priority:
                p1_move_results = p1move.effect(p1_pokemon, p2_pokemon)
                for prob, (p1_poke, p2_poke) in p1_move_results:
                    p2_move_results = p2move.effect(p2_poke, p1_poke)
                    ret = ret + [(prob * newprob, (p1_poke_final, p2_poke_final))
                                 for newprob, (p2_poke_final, p1_poke_final) in p2_move_results]
            else:
                p2_move_results = p2move.effect(p2_pokemon, p1_pokemon)
                for prob, (p2_poke, p1_poke) in p2_move_results:
                    p1_move_results = p1move.effect(p1_poke, p2_poke)
                    ret = ret + [(prob * newprob, (p1_poke_final, p2_poke_final))
                                 for newprob, (p1_poke_final, p2_poke_final) in p1_move_results]

        # Then, compare speeds
        else:
            if p1_pokemon.speed > p2_pokemon.speed:
                p1_move_results = p1move.effect(p1_pokemon, p2_pokemon)
                for prob, (p1_poke, p2_poke) in p1_move_results:
                    p2_move_results = p2move.effect(p2_poke, p1_poke)
                    ret = ret + [(prob * newprob, (p1_poke_final, p2_poke_final))
                                 for newprob, (p2_poke_final, p1_poke_final) in p2_move_results]
            else:
                p2_move_results = p2move.effect(p2_pokemon, p1_pokemon)
                for prob, (p2_poke, p1_poke) in p2_move_results:
                    p1_move_results = p1move.effect(p1_poke, p2_poke)
                    ret = ret + [(prob * newprob, (p1_poke_final, p2_poke_final))
                                 for newprob, (p1_poke_final, p2_poke_final) in p1_move_results]
    return ret


class Move:
    accuracy = None
    basePower = None
    category = None
    multihit = None
    pp = None
    priority = None
    secondary = None
    type = None
    boosts = None
    effect = None
    critratio = None

    def __init__(self, movedata):
        self.accuracy = movedata['accuracy']
        self.basePower = movedata['basePower']
        self.category = movedata['category']
        self.multihit = movedata.get('multihit', 1)
        self.pp = movedata['pp']
        self.priority = movedata['priority']
        self.secondary = movedata['secondary']
        self.type = movedata['type'].lower()
        self.boosts = movedata.get('boosts', None)
        if 'effect' in movedata.keys():
            self.effect = getattr(self, movedata['id'])
        else:
            self.effect = self.defaultmove
        self.critratio = movedata.get('critratio', 1)

    def defaultmove(self, ourPokemon, theirPokemon):
        """
        Return a list of (prob, (poke1, poke2)) tuples resulting from taking this move
        :param ourPokemon:
        :param theirPokemon:
        :return:
        """
        # Copy pokemon for the new state
        ourPokemon_hit = copy.copy(ourPokemon)
        theirPokemon_hit = copy.copy(theirPokemon)

        states = []
        # Add missed state first, if accuracy is <100
        if self.accuracy is True:
            acc = 1.0
        else:
            acc = self.accuracy / 100.0
        if acc != 1.0:
            states.append(
                (1.0 - acc, (copy.copy(ourPokemon), copy.copy(theirPokemon))))

        # Do damage calc first
        if self.basePower != 0:
            damage = calcDamage(ourPokemon_hit, theirPokemon_hit, self)
            theirPokemon_hit.currhp -= damage / theirPokemon_hit.maxhp

        # Then apply boosts if they exist
        if self.boosts is not None:
            # Apply boost to self
            if self.accuracy is True:
                ourPokemon_hit.attack += self.boosts.get("atk", 0)
                ourPokemon_hit.defense += self.boosts.get("def", 0)
                ourPokemon_hit.sp_att += self.boosts.get("spa", 0)
                ourPokemon_hit.sp_def += self.boosts.get("spd",0)
                ourPokemon_hit.speed += self.boosts.get("spe", 0)
            # Otherwise, apply boosts to opponent
            else:
                theirPokemon_hit.attack += self.boosts.get("atk", 0)
                theirPokemon_hit.defense += self.boosts.get("def", 0)
                theirPokemon_hit.sp_att += self.boosts.get("spa", 0)
                theirPokemon_hit.sp_def += self.boosts.get("spd",0)
                theirPokemon_hit.speed += self.boosts.get("spe", 0)

        # Then, apply secondary effects if they exist
        if self.secondary is not None:
            secondary_acc = self.secondary['chance'] / 100.0
            ourPokemon_secondary = copy.copy(ourPokemon_hit)
            theirPokemon_secondary = copy.copy(theirPokemon_hit)
            if "status" in self.secondary.keys() and theirPokemon_secondary.status is None:
                theirPokemon_secondary.status = self.secondary['status']
            if "boosts" in self.secondary.keys():
                theirPokemon_secondary.attack += self.secondary['boosts'].get(
                    "atk", 0)
                theirPokemon_secondary.defense += self.secondary['boosts'].get(
                    "def", 0)
                theirPokemon_secondary.sp_att += self.secondary['boosts'].get(
                    "spa", 0)
                theirPokemon_secondary.sp_def += self.secondary['boosts'].get("spd",0)
                theirPokemon_secondary.speed += self.secondary['boosts'].get(
                    "spe", 0)
            states.append(
                (acc * secondary_acc, (ourPokemon_secondary, theirPokemon_secondary)))
            states.append((acc * (1 - secondary_acc),
                           (ourPokemon_hit, theirPokemon_hit)))
        else:
            states.append((acc, (ourPokemon_hit, theirPokemon_hit)))
        return states

    def bide(self, ourPokemon, theirPokemon):
        print("bide")
        return [(1.0, (copy.copy(ourPokemon), copy.copy(theirPokemon)))]

    def counter(self, ourPokemon, theirPokemon):
        print("counter")
        return [(1.0, (copy.copy(ourPokemon), copy.copy(theirPokemon)))]

    def reflect(self, ourPokemon, theirPokemon):
        print("reflect")
        return [(1.0, (copy.copy(ourPokemon), copy.copy(theirPokemon)))]

    def substitute(self, ourPokemon, theirPokemon):
        print("substitute")
        return [(1.0, (copy.copy(ourPokemon), copy.copy(theirPokemon)))]


with open('pysim/viablemovesdata.json') as f:
    move_data = json.loads(f.read())
    for id, data in move_data.items():
        viable_moves[id] = Move(data)

with open('pysim/effectiveness.csv', 'rt') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        move_effectiveness[(row[0], row[1])] = float(row[2])


def getScore(ourPokemon, enemyPokemon):
    teamScore = 0
    for poke_id, pokemon in ourPokemon.items():  
      if pokemon.status != "None":
        status_effect = 0.5
      else:
        status_effect = 1
      stat_multiplier = 1 
      for stat,mult in pokemon.stat_multipliers.items():
        if pokemon.gen == 1 and stat == 3:
            continue
        stat_multiplier *= stat
      teamScore += pokemon.currhp * status_effect * stat_multiplier
    teamScore = teamScore / NUM_TEAM_MEMBERS
    if enemyPokemon.status != "None":
      status_effect = 0.5
    else:
      status_effect = 1
    stat_multiplier = 1
    for stat, mult in enemyPokemon.stat_multipliers.items():
        if enemyPokemon.gen == 1 and stat == 3:
            continue
        stat_multiplier *= mult
    enemyScore = enemyPokemon.currhp * status_effect * stat_multiplier
    score = teamScore - enemyScore
    return score

def isWin(enemyPokemon):
    return enemyPokemon.currhp <= 0 

def isLose(ourPokemon):
    allFainted = True 
    for pokemon in ourPokemon.values():
        if pokemon.currhp > 0:
            allFainted = False
    return allFainted

def main():
    # (attack, defense, sp_att, sp_def, speed, maxhp, level, currhp, gen, moveids, types)
    poke1 = Pokemon(90, 90, 100, 1, 100, 353, 100, 1.0,
                    1, ['blizzard'], ['fire', 'water'])
    poke1_2 = Pokemon(90, 90, 100, 3, 100, 353, 100, 1.0,
                      1, ['blizzard'], ['grass', 'ground'])
    poke2 = Pokemon(90, 90, 100, 2, 100, 353, 100, 1.0,
                    1, ['blizzard'], ['fire', 'water'])



    nextStates = performActions(
        poke1, poke2, ("move", "blizzard"), ("move", "bide"))
    print(json.dumps(json.loads(jsonpickle.encode(nextStates)), indent=2))


if __name__ == "__main__":
    main()
