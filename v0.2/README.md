# my v0.2 algo

## File Overview

```
v0.2
 │
 ├──gamelib
 │   ├──__init__.py
 │   ├──advanced.py
 │   ├──algocore.py
 │   ├──game.py
 │   ├──map.py
 │   ├──navigation.py
 │   ├──tests.py
 │   ├──unit.py
 │   └──util.py
 ├──defensive_data.txt
 ├──defensive_img.png
 ├──algo_strategy.py
 ├──README.md
 └──run.sh
 
```

## Strategy Notes
### Ideas
1. Strengthened v0.1. Prioritize DESTRUCTOR constructions, especially on the top left part.
2. Use all the BIT resources to optimize the attacks.

### Feedbacks
1. ![WIN](https://placehold.it/15/c5f015/000000?text=+)`STARTERALGO`: NA.
2. ![WIN](https://placehold.it/15/c5f015/000000?text=+)`SPECTOR`: Vulnerable to the attacks that already get into the channel. 
Consider adjusting the DESTRUCTOR at [12, 4]
3. ![WIN](https://placehold.it/15/c5f015/000000?text=+)`PUNCHBAGROB`: NA.
4. ![LOSS](https://placehold.it/15/f03c15/000000?text=+) `STARFISH`: Much better than before but still FATAL EMP ATTACK. Consider 
modifying scramblers to EMPs.
5. ![WIN](https://placehold.it/15/c5f015/000000?text=+)`HELLFIRE`: Still Vulnerable to EMP attacks.
6. ![WIN](https://placehold.it/15/c5f015/000000?text=+)`BLACKBEARD`: Also vulnerable to the attacks that already get into the channel.
7. ![LOSS](https://placehold.it/15/f03c15/000000?text=+)`MADROXFACTOR4`: FATAL EMP attacks. Consider add DESTRUCTORs in the first line 
and move Encryptors a little bit backward. 
8. ![LOSS](https://placehold.it/15/f03c15/000000?text=+)`AELGOO54`: Enemy strengthened the weakness, F*ck! must have a plan B!



### Performance (12/15/2018 23:43)
1. 22 WINS | 20 LOST
2. ELO: 1543

## Defense Overview
![image info](./defensive_img.png)

