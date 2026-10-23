"""Small, explicit Gen 9 mechanics checks. No turn simulation or model calls.

Stat arithmetic is checked against the pinned Showdown implementation. Field
checks describe assumptions, never predict damage, survival or an opponent's play.
"""
from itertools import combinations

STATS = ("hp", "atk", "def", "spa", "spd", "spe")
NATURES = {
    "Lonely": ("atk", "def"), "Brave": ("atk", "spe"), "Adamant": ("atk", "spa"), "Naughty": ("atk", "spd"),
    "Bold": ("def", "atk"), "Relaxed": ("def", "spe"), "Impish": ("def", "spa"), "Lax": ("def", "spd"),
    "Timid": ("spe", "atk"), "Hasty": ("spe", "def"), "Jolly": ("spe", "spa"), "Naive": ("spe", "spd"),
    "Modest": ("spa", "atk"), "Mild": ("spa", "def"), "Quiet": ("spa", "spe"), "Rash": ("spa", "spd"),
    "Calm": ("spd", "atk"), "Gentle": ("spd", "def"), "Sassy": ("spd", "spe"), "Careful": ("spd", "spa"),
}
WEATHER = {"Drought": "sun", "Drizzle": "rain", "Sand Stream": "sand", "Snow Warning": "snow"}
WEATHER_SPEED = {"Chlorophyll": "sun", "Swift Swim": "rain", "Sand Rush": "sand", "Slush Rush": "snow"}
TERRAINS = {"Psychic Surge": "Psychic", "Grassy Surge": "Grassy", "Electric Surge": "Electric", "Misty Surge": "Misty"}
SEEDS = {"Psychic Seed": "Psychic", "Grassy Seed": "Grassy", "Electric Seed": "Electric", "Misty Seed": "Misty"}
PROTECT = {"Protect", "Detect", "Spiky Shield", "Baneful Bunker", "Burning Bulwark", "Silk Trap", "Obstruct"}
REDIRECT = {"Follow Me", "Rage Powder"}
SLEEP = {"Spore", "Sleep Powder", "Hypnosis", "Sing", "Lovely Kiss", "Grass Whistle", "Yawn"}
ROOM_SLOW = 85


def actual_stats(member, data):
    """Unboosted stats at the set's level, before item/ability/field modifiers."""
    level = member.get("level", 50)
    plus, minus = NATURES.get(member.get("nature"), (None, None))
    result = {}
    for key, base in data["species"][member["species"]]["base_stats"].items():
        iv = member.get("ivs", {}).get(key, 31)
        ev = member.get("evs", {}).get(key, 0)
        value = (2 * base + iv + ev // 4) * level // 100
        if key == "hp": value = 1 if base == 1 else value + level + 10
        else:
            value += 5
            if plus == key: value = value * 110 // 100
            if minus == key: value = value * 90 // 100
        result[key] = value
    return result


def speed_value(member, data, *, weather=None, tailwind=False, unburden=False):
    """Neutral stages, no status: the explicitly supported modifiers only."""
    speed = actual_stats(member, data)["spe"]
    numerator, denominator = 1, 1
    item = member["item"]
    # An Unburden scenario means the original held item has already gone.
    if not unburden:
        if item == "Choice Scarf": numerator *= 3; denominator *= 2
        if item in {"Iron Ball", "Macho Brace", "Power Anklet", "Power Band", "Power Belt", "Power Bracer", "Power Lens", "Power Weight"}:
            denominator *= 2
    ability = member["ability"]
    if weather and WEATHER_SPEED.get(ability) == weather: numerator *= 2
    if ability == "Unburden" and unburden: numerator *= 2
    if ability == "Slow Start": denominator *= 2
    if tailwind: numerator *= 2
    return max(1, speed * numerator // denominator)


def speed_profile(member, team, data):
    base = actual_stats(member, data)["spe"]
    normal = speed_value(member, data)
    scenarios = []
    tailwind = any("Tailwind" in m["moves"] for m in team)
    if tailwind:
        scenarios.append({"condition": "After your side successfully sets Tailwind", "speed": speed_value(member, data, tailwind=True)})
    weather = WEATHER_SPEED.get(member["ability"])
    if weather:
        setters = [m["species"] for m in team if WEATHER.get(m["ability"]) == weather]
        scenarios.append({"condition": f"While {weather} is active ({', '.join(setters) if setters else 'no automatic setter on this team'})",
                          "speed": speed_value(member, data, weather=weather)})
        if tailwind:
            scenarios.append({"condition": f"While both {weather} and your Tailwind are active", "speed": speed_value(member, data, weather=weather, tailwind=True)})
    if member["ability"] == "Unburden":
        terrain = SEEDS.get(member["item"])
        setter = next((m["species"] for m in team if TERRAINS.get(m["ability"]) == terrain), None) if terrain else None
        condition = f"After {member['item']} is consumed with {setter}'s {terrain} Terrain active" if setter else "After its held item is actually consumed or removed; not active on entry by default"
        scenarios.append({"condition": condition + "; bonus ends on switching out", "speed": speed_value(member, data, unburden=True)})
    return {"base_stat": base, "ordinary_speed": normal, "scenarios": scenarios,
            "scope": "Neutral stat stages; no paralysis, opponent effects or ability suppression. Listed conditional modifiers only. Trick Room changes order, not this number."}


def grounded(member, data):
    if member["item"] == "Iron Ball": return True
    return ("Flying" not in data["species"][member["species"]]["types"]
            and member["ability"] != "Levitate" and member["item"] != "Air Balloon")


def incoming_multiplier(member, attack_type, data):
    """Baseline plus common unconditional immunities, only for ally-hit checks."""
    ability = member["ability"]
    if ability == "Telepathy": return 0
    immunities = {"Ground": {"Levitate", "Earth Eater"}, "Electric": {"Volt Absorb", "Lightning Rod", "Motor Drive"},
                  "Water": {"Water Absorb", "Storm Drain", "Dry Skin"}, "Fire": {"Flash Fire", "Well-Baked Body"}, "Grass": {"Sap Sipper"}}
    if ability in immunities.get(attack_type, set()) and not (ability == "Levitate" and member["item"] == "Iron Ball"): return 0
    if attack_type == "Ground" and not grounded(member, data): return 0
    if attack_type == "Ground" and member["item"] == "Iron Ball":
        # Grounding removes Flying's Ground immunity, retaining the other type.
        value = 1
        for kind in data["species"][member["species"]]["types"]:
            value *= 2 if kind in {"Electric", "Fire", "Poison", "Rock", "Steel"} else .5 if kind in {"Grass", "Bug"} else 1
        return value
    return data["species"][member["species"]]["incoming"][attack_type]


def interaction_checks(team, data):
    """Actionable, conditional conflicts. A warning is not a legality failure."""
    findings = []
    def add(code, severity, names, text, penalty=0):
        findings.append({"code": code, "severity": severity, "pokemon": list(dict.fromkeys(names)), "explanation": text, "penalty": penalty})
    weather = {WEATHER[m["ability"]] for m in team if m["ability"] in WEATHER}
    terrains = {TERRAINS[m["ability"]] for m in team if m["ability"] in TERRAINS}
    if len(weather) > 1:
        add("competing_weather", "caution", [m["species"] for m in team if m["ability"] in WEATHER],
            "These setters overwrite each other's weather. Pick one weather mode for a given opening; do not assume both benefits are active.", 5)
    if len(terrains) > 1:
        add("competing_terrain", "caution", [m["species"] for m in team if m["ability"] in TERRAINS],
            "Only one terrain is active at a time. A terrain change can remove a partner's expected benefit.", 2)
    for m in team:
        name, moves, ability = m["species"], set(m["moves"]), m["ability"]
        priority = [move for move in moves if (data["moves"][move]["priority"] > 0 or ability == "Prankster" and data["moves"][move]["category"] == "Status")
                    and data["moves"][move]["target"] in {"normal", "allAdjacentFoes", "any"}]
        if "Psychic" in terrains and priority:
            add("psychic_priority", "caution", [name],
                f"Psychic Terrain blocks {name}'s {', '.join(sorted(priority))} against grounded opponents. Use another move or check the target is airborne; allied support is not blocked.", 3)
        if moves & SLEEP and terrains & {"Electric", "Misty"}:
            add("terrain_sleep", "caution", [name], f"Active {' / '.join(sorted(terrains & {'Electric', 'Misty'}))} Terrain prevents new sleep on grounded targets. Do not rely on {', '.join(sorted(moves & SLEEP))} there.", 2)
        wanted = WEATHER_SPEED.get(ability) or ("sun" if ability == "Solar Power" else None)
        if wanted and wanted not in weather:
            add("missing_weather", "caution", [name], f"{ability} needs {wanted}, but the team has no automatic {wanted} setter. Manual weather or the opponent would have to supply it.", 3)
        if ability == "Solar Power" and "sun" in weather:
            add("solar_power_hp", "trade-off", [name], "Solar Power boosts Special Attack in sun but costs 1/8 of maximum HP at each turn's end. Plan a short attacking window rather than assuming it can stay in indefinitely.")
        if "sun" in weather and any(data["moves"][move]["type"] == "Water" and data["moves"][move]["category"] != "Status" for move in moves):
            add("sun_water", "trade-off", [name], f"Sun halves ordinary Water-move damage, so {name}'s Water attacks lose power while sun stays up.", 1)
        if "rain" in weather and any(data["moves"][move]["type"] == "Fire" and data["moves"][move]["category"] != "Status" for move in moves):
            add("rain_fire", "trade-off", [name], f"Rain halves ordinary Fire-move damage. {name} may need to attack outside rain or choose another move.", 1)
        if "sun" in weather and moves & {"Hurricane", "Thunder"}:
            add("sun_accuracy", "caution", [name], f"Sun reduces the accuracy of {', '.join(sorted(moves & {'Hurricane', 'Thunder'}))} to 50%. Avoid relying on it as a consistent sun attack.", 2)
        if "Electro Shot" in moves and "rain" not in weather:
            text = "Electro Shot normally spends a turn charging; rain removes the charge turn. This team has no automatic rain setter."
            if m["item"] == "Power Herb": text += " Power Herb can skip one charge turn, then is consumed."
            add("electro_shot_charge", "trade-off", [name], text, 0 if m["item"] == "Power Herb" else 1)
        if m["item"] == "Power Herb" and "Electro Shot" in moves and "rain" in weather:
            add("herb_in_rain", "trade-off", [name], "Electro Shot already skips its charge turn in rain. Power Herb is mainly backup for turns without rain; it does not add a second charge-turn benefit.", .8)
        if moves & {"Solar Beam", "Solar Blade"} and "sun" not in weather:
            add("solar_charge", "caution", [name], f"{', '.join(sorted(moves & {'Solar Beam', 'Solar Blade'}))} needs a charge turn outside sun. No automatic sun setter is selected.", 2)
        terrain = SEEDS.get(m["item"])
        if terrain and terrain not in terrains:
            add("missing_seed_terrain", "caution", [name], f"{m['item']} needs {terrain} Terrain to be consumed. No automatic matching setter is selected, so its boost is not guaranteed" + (" and Unburden cannot be assumed." if ability == "Unburden" else "."), 3)
        if ability == "Unburden":
            if m["item"] == "Focus Sash":
                add("conditional_unburden", "trade-off", [name], "Focus Sash does not activate Unburden on entry. It must actually save this Pokemon from a full-HP knockout and be consumed; do not plan with doubled Speed beforehand.", .5)
        if m["item"].startswith("Choice "):
            add("choice_lock", "trade-off", [name], f"{m['item']} locks {name} into its first selected move until it switches out. Choose an attack that remains useful if the opponent protects or changes position.")
        if "Trick Room" in moves:
            slow = [s["species"] for s in team if s is not m and speed_value(s, data) <= ROOM_SLOW]
            if not slow:
                add("unsupported_room", "caution", [name], "No other selected member has ordinary Speed at or below 85. Trick Room can favour the opponent; keep it off unless the matchup calls for reversing Speed order.", 2)
        if m["item"] == "Assault Vest" and any(data["moves"][move]["category"] == "Status" for move in moves):
            add("vest_status", "caution", [name], "Assault Vest prevents using status moves in normal play. Legality alone does not make this moveset usable.", 12)
        if "Grassy" in terrains and "Earthquake" in moves:
            add("grassy_earthquake", "trade-off", [name], "Grassy Terrain halves Earthquake damage against grounded targets. Consider the selected single-target Ground alternative if available.", 1)
    for attacker, ally in ((a, b) for a, b in combinations(team, 2)):
        for source, target in ((attacker, ally), (ally, attacker)):
            for move in source["moves"]:
                info = data["moves"][move]
                if info["target"] != "allAdjacent" or info["category"] == "Status": continue
                multiplier = incoming_multiplier(target, info["type"], data)
                if multiplier > 0:
                    guard = bool(set(target["moves"]) & PROTECT)
                    add("ally_spread", "caution", [source["species"], target["species"]],
                        f"{source['species']}'s {move} also hits {target['species']} (original-type multiplier {multiplier:g}x, before other damage modifiers). "
                        + ("The ally has a protection move, but must spend its action using it; otherwise switch or choose another attack." if guard else "The ally has no selected personal protection move; choose another attack or switch it out."),
                        (1 if guard else 3) * min(multiplier, 2))
    if any(m["ability"] == "Neutralizing Gas" for m in team):
        add("ability_suppression", "caution", [m["species"] for m in team], "Neutralizing Gas can suppress allies' abilities. Weather, terrain and ability-based speed examples assume their effects are available and are not reliable while suppressed.", 6)
    room_setters = [m["species"] for m in team if "Trick Room" in m["moves"]]
    if len(room_setters) > 1:
        add("double_room", "caution", room_setters, "Using Trick Room again while it is active ends it. Do not use both setters' Trick Room on the same turn: the second can undo the first.", 1)
    return findings


def pair_plan(first, second, data):
    pair = [first, second]
    reasons, actions, score = [], [], 0
    checks = interaction_checks(pair, data)
    for m, ally in ((first, second), (second, first)):
        name, partner = m["species"], ally["species"]
        moves = set(m["moves"])
        weather = WEATHER.get(m["ability"])
        if weather and (WEATHER_SPEED.get(ally["ability"]) == weather or (weather == "sun" and ally["ability"] == "Solar Power")):
            score += 7
            reasons.append(f"{name} supplies {weather} for {partner}'s {ally['ability']}; the weather must remain active.")
            attack = next((move for move in ally["moves"] if data["moves"][move]["category"] != "Status"), None)
            if attack:
                actions.append(f"If the opponent cannot immediately remove {partner}, consider {attack} with it while {name} attacks or protects. Check opposing weather setters before committing to this mode.")
        terrain = TERRAINS.get(m["ability"])
        if terrain and SEEDS.get(ally["item"]) == terrain and ally["ability"] == "Unburden":
            score += 6
            reasons.append(f"{name}'s {terrain} Terrain consumes {partner}'s {ally['item']}, enabling Unburden if item and ability effects are not suppressed.")
        if "Tailwind" in moves:
            score += 3
            actions.append(f"Consider Tailwind with {name}; {partner} can attack or protect. The setter must successfully act first; do not assume Tailwind is already active.")
        for move in ("Icy Wind", "Electroweb"):
            if move in moves:
                score += 1
                actions.append(f"{name} can use {move} to lower the opponents' Speed by one stage if it hits and the effect is not blocked. Damage immunity or stat-drop protection can stop this plan; it is not an immediate guaranteed outspeed.")
        if "Trick Room" in moves:
            if speed_value(ally, data) <= ROOM_SLOW:
                score += 3
                actions.append(f"If the opponent is faster, consider Trick Room with {name} while {partner} protects or attacks. Trick Room has -7 priority, so it usually starts after ordinary attacks.")
            else:
                actions.append(f"{partner} has ordinary Speed {speed_value(ally, data)}. Keep Trick Room off when this faster mode benefits from moving first; it does not raise any Speed stat.")
        if moves & REDIRECT:
            score += 2
            redirection = sorted(moves & REDIRECT)[0]
            actions.append(f"{name} can use {redirection} to draw eligible single-target attacks away from {partner}. Spread moves bypass redirection" + ("; Grass types, Overcoat and Safety Goggles can ignore Rage Powder." if redirection == "Rage Powder" else "."))
        if m["ability"] == "Intimidate":
            score += 1
            reasons.append(f"{name}'s Intimidate can lower opposing Attack on entry. Immunities, Clear Amulet, Defiant and Competitive can change that trade-off.")
        if m["ability"] == "Friend Guard":
            score += 1
            reasons.append(f"{name}'s Friend Guard reduces damage to its ally while the ability is active; it does not protect {name} itself.")
        if "Fake Out" in moves:
            blocked = any(c["code"] == "psychic_priority" and name in c["pokemon"] for c in checks)
            if not blocked:
                score += 2
                actions.append(f"On {name}'s first turn after entering, Fake Out can disrupt one opponent while {partner} acts. Ghost immunity, protection, Inner Focus and other effects can stop the flinch; it is not guaranteed.")
        if "Helping Hand" in moves:
            attacks = [v for v in ally["moves"] if data["moves"][v]["category"] != "Status"]
            if attacks:
                score += 1
                actions.append(f"{name} can use Helping Hand with {partner}'s {attacks[0]}; it boosts that ally's attack damage this turn. Do not pair it with an ally's status move or Protect.")
    attacks = [m for m in pair if any(data["moves"][v]["category"] != "Status" for v in m["moves"])]
    if len(attacks) == 2: score += 1
    if not attacks: score -= 6
    if all(set(m["moves"]) & REDIRECT for m in pair):
        score -= 3
        reasons.append("Both have redirection; using it with both at once wastes the chance for an ally to attack or set up.")
    if all("Trick Room" in m["moves"] for m in pair): score -= 3
    score -= sum(c["penalty"] for c in checks)
    if not reasons: reasons.append("A utility or attacking opening to consider after checking the opposing six.")
    if not actions: actions.append("Choose attacks after checking targets, immunities and the opposing lead. No safe opening is guaranteed without the opponent's team.")
    return {"pokemon": [first["species"], second["species"]], "score": round(score, 3), "reasons": reasons,
            "opening_actions": actions, "cautions": [c["explanation"] for c in checks],
            "interaction_codes": sorted({c["code"] for c in checks})}


def member_guidance(member, team, data):
    stats = actual_stats(member, data)
    evs = member["evs"]
    investment = [f"{evs.get(k, 0)} {k.upper()}" for k in STATS if evs.get(k, 0)]
    plus, minus = NATURES.get(member["nature"], (None, None))
    nature = f"{member['nature']} raises {plus.upper()} and lowers {minus.upper()}." if plus else f"{member['nature']} is a neutral nature."
    physical = sum(data["moves"][m]["category"] == "Physical" for m in member["moves"])
    special = sum(data["moves"][m]["category"] == "Special" for m in member["moves"])
    cautions = []
    if "Trick Room" in member["moves"] or any("Trick Room" in m["moves"] for m in team):
        if evs.get("spe", 0) == 0:
            cautions.append("0 Speed EVs is not 0 Speed IVs. This build still has 31 Speed IVs; a dedicated Trick Room spread may want fewer, but IVs have not been optimized.")
    if physical == 0 and special:
        cautions.append("This is a special-attacking set. The default 31 Attack IVs are not optimized; lower Attack can sometimes reduce Foul Play and confusion self-damage.")
    if not set(member["moves"]) & PROTECT:
        cautions.append("No personal protection move is selected. Plan switches and support carefully rather than assuming this Pokemon can Protect.")
    if member["ability"] == "Prankster":
        cautions.append("Prankster boosts status-move priority. Its moves targeting opposing Dark types fail; Psychic Terrain can also block them against grounded opponents. Screens and other side-targeting support are different.")
    tips = []
    for move in member["moves"]:
        info = data["moves"][move]
        tip = info["description"]
        if info["target"] == "allAdjacentFoes": tip += " It targets both adjacent opponents; redirection does not turn it into a single-target attack."
        if info["target"] == "allAdjacent": tip += " It can hit your adjacent ally too; check the pair's cautions."
        if move in PROTECT: tip += " Use it to cover an exposed turn or let your partner act; repeated use is unreliable."
        if move == "Eruption": tip += " Its power falls as your current HP falls, so protecting HP matters."
        tips.append({"move": move, "guidance": tip})
    return {"actual_stats": stats, "speed": speed_profile(member, team, data),
            "spread_explanation": f"Historical EV investment: {' / '.join(investment) or 'none'}. {nature} These EVs produce the shown level-{member.get('level', 50)} stats; no survival or knockout benchmark has been verified.",
            "set_cautions": cautions, "move_guidance": tips}


def speed_overview(team, data):
    ordered = sorted(team, key=lambda m: (-speed_value(m, data), m["species"]))
    room = [m["species"] for m in team if "Trick Room" in m["moves"]]
    return {"ordinary_order": [{"pokemon": m["species"], "speed": speed_value(m, data)} for m in ordered],
            "trick_room_setters": room,
            "explanation": "Higher effective Speed normally acts first within the same move-priority bracket. Ties are not guaranteed. Trick Room reverses Speed order within that bracket for five turns including the activation turn; priority moves still use their own bracket. Tailwind lasts four turns including its activation turn.",
            "trick_room_plan": ("Use the slow mode only when the opposing active Pokemon are faster. Keep fast partners for turns without Trick Room; do not set Tailwind automatically in the slow mode." if room else "No Trick Room setter is selected. Do not assume the team can reverse Speed order.")}
