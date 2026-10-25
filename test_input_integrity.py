"""Invalid requests must not corrupt memory or bypass prepared-set constraints."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from catalogue import load_catalogue
from hmem_memory import recall_preferences
from team_builder import build_team
from team import execute, canonical_candidate


class InputIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _ = load_catalogue(True)
        cls.baseline, _, _ = build_team(cls.data, ["Charizard"])

    def test_invalid_species_and_duplicate_locks_do_not_change_preferences(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            recall_preferences(root/"memory","integrity",{"favourite":"Charizard","avoided_partner":"Incineroar"})
            state=root/"memory/integrity/state.json"
            before=state.read_bytes()
            with patch("team.load_catalogue",return_value=(self.data,"sample fixture")), \
                 patch("team.recall_preferences",side_effect=lambda d,p,u,**kw:recall_preferences(root/"memory",p,u,**kw)):
                for favourites in [["Miraidon"],["Bulbasaur"],["Charizardzzz"],["Charizard","Charizard"]]:
                    with self.assertRaises(ValueError):execute(favourites,sample=True,profile="integrity",output=root/"runs")
                    self.assertEqual(state.read_bytes(),before)

    def test_locked_secondary_favourite_conflicts_with_remembered_avoidance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            recall_preferences(root/"memory","conflict",{"favourite":"Charizard","avoided_partner":"Incineroar"})
            state=root/"memory/conflict/state.json";before=state.read_bytes()
            with patch("team.load_catalogue",return_value=(self.data,"sample fixture")), \
                 patch("team.recall_preferences",side_effect=lambda d,p,u,**kw:recall_preferences(root/"memory",p,u,**kw)):
                with self.assertRaises(ValueError):execute(["Charizard","Incineroar"],sample=True,profile="conflict",output=root/"runs")
                self.assertEqual(state.read_bytes(),before)
                result,_=execute(["Charizard","Incineroar"],sample=True,profile="conflict",output=root/"runs",clear_avoidance=True)
                self.assertIn("Incineroar",[m["species"] for m in result["team"]])
                self.assertIsNone(result["memory_used"]["avoided_partner"])

    def test_invalid_preference_batch_is_validated_before_either_update(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            recall_preferences(root,"batch",{"favourite":"Charizard"})
            state=root/"batch/state.json";before=state.read_bytes()
            with self.assertRaises(RuntimeError):recall_preferences(root,"batch",{"favourite":"Venusaur","avoided_partner":"not-a-species"})
            self.assertEqual(state.read_bytes(),before)

    def test_review_input_is_canonicalized_without_extra_private_metadata(self):
        candidate=copy.deepcopy(self.baseline)
        candidate[0]["private_note"]="private note that must never reach a model or report"
        result=canonical_candidate(self.data,candidate)
        self.assertNotIn("private_note",result[0])
        self.assertEqual(result[0]["item"],candidate[0]["item"])

    def test_non_source_review_set_is_rejected_before_memory_or_model(self):
        candidate=copy.deepcopy(self.baseline);candidate[0]["ivs"]["hp"]=0
        with tempfile.TemporaryDirectory() as folder:
            with patch("team.load_catalogue",return_value=(self.data,"sample fixture")), \
                 patch("team.recall_preferences") as memory, patch("nightshift_client.NightshiftClient") as model:
                with self.assertRaises(ValueError):execute(["Charizard"],review_candidate=candidate,ai=True,output=Path(folder))
                memory.assert_not_called();model.assert_not_called()

    def test_local_mode_does_not_silently_ignore_an_ai_objective(self):
        with patch("team.load_catalogue") as data:
            with self.assertRaises(ValueError):execute(["Charizard"],sample=True,objective="rain")
            data.assert_not_called()

    def test_duplicate_provided_species_are_refused_before_preferences(self):
        candidate=copy.deepcopy(self.baseline);candidate[-1]=copy.deepcopy(candidate[0])
        with tempfile.TemporaryDirectory() as folder:
            with patch("team.load_catalogue",return_value=(self.data,"sample fixture")),patch("team.recall_preferences") as memory:
                with self.assertRaises(ValueError):execute(["Charizard"],sample=True,review_candidate=candidate,output=Path(folder))
                memory.assert_not_called()


if __name__=="__main__":unittest.main()
