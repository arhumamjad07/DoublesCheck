"""A legal six-favourite request must not be lost to premature heuristic pruning."""
import itertools
import random
import unittest

from catalogue import load_catalogue
from team_builder import build_team, item_assignment_possible
from reasoning_cases import CASES


class LockedSearchTests(unittest.TestCase):
    def test_observed_six_lock_item_conflict_has_a_legal_solution(self):
        data,_=load_catalogue(True)
        names=list(CASES["locked-tradeoffs"].favourites)
        team,validation,locked=build_team(data,names)
        self.assertTrue(validation["valid"])
        self.assertEqual(locked,names)
        self.assertEqual(set(names),{m["species"] for m in team})
        self.assertEqual(len({m["item"] for m in team}),6)

    def test_matching_check_agrees_with_independent_exhaustive_oracle(self):
        rng=random.Random(20261025)
        items=["Focus Sash","Choice Scarf","Life Orb","Sitrus Berry"]
        for _ in range(80):
            names=[str(i) for i in range(rng.randint(1,5))]
            domains={name:rng.sample(items,rng.randint(1,4)) for name in names}
            used=set(rng.sample(items,rng.randint(0,2)))
            mons={name:{"sets":[{"item":item} for item in values]} for name,values in domains.items()}
            expected=any(len(set(combo))==len(combo) and not (set(combo)&used)
                         for combo in itertools.product(*(domains[name] for name in names)))
            self.assertEqual(item_assignment_possible(mons,names,used),expected)


if __name__=="__main__":unittest.main()
