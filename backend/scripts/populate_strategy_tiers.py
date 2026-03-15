import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")
ARK_NOVA_STRATEGY = """
Based on community consensus and BGA usage stats.
- **Map 4: Commercial Harbor**: The flexibility to sell cards and the 4-card draw capability makes this a powerhouse for cycling decks and finding key animals early.
- **Map 1: Observation Tower (BGA Alt)**: The alternative layout buffs this map significantly, offering great placement bonuses and flexibility.
- **Map 2: Outdoor Areas**: Excellent for large animal strategies. Early partnership access is key.
- **Map 6: Research Institute**: Ignoring conditions for playing animals allows for explosive starts, though the new BGA version adds blockers.
- **Map 3: Silver Lake**: A solid map, though the recent BGA alternative version nerfed it by moving the lake. Still good for digging with "Determination".
- **Tempo is King**: Don't just build a zoo; race for the break. Triggering breaks when opponents are low on money or full of cards is a key disruption tactic.
- **Conservation First**: Prioritize Base Conservation Projects. Unlocking your second worker early is often better than a small appeal boost.
"""
TM_STRATEGY = """
Assuming all expansions (Prelude, Colonies, Turmoil).
- **Point Luna**: Access to Earth tags and card draw (Titan) makes this arguably the highest ceiling corp in the game.
- **Credicor**: The economy king. 4 MC rebate on all expensive projects allows for massive efficiency engines.
- **Manutech**: With Preludes, this corporation can explode on turn 1, converting immediate production into resources.
- **Tharsis Republic**: Dominant on the Tharsis map. City-building engines win ground games.
- **Saturn Systems**: Jovian tag multipliers are the strongest late-game scoring mechanic.
- **Vitor**: Awards for funding awards? Yes. Victory points for playing events? Double yes.
- **Ecoline**: Great for terraforming rushing, but vulnerable to plant-killing asteroids.
- **Thorgate**: Reliable Power strategy, but often lacks the explosive scoring of others.
- **Terraform Early**: Don't overbuild engines in Gen 8+. If you have the lead, push the parameters to end the game.
- **Milestones are Trap or Treasure**: Assess if 8 MC for 5 VP is worth it. Usually yes, but not if it stalls your engine by a generation.
"""
SCYTHE_STRATEGY = """
Standard listing based on potential turn count to win.
- **Rusviet Union + Industrial**: The infamous "Rusviet Industrial" combo. Can end games in 12-14 turns. relentless production and movement.
- **Crimea Khanate + Patriotic**: Insane resource generation flexibility.
- **Crimea Khanate + Industrial/innovative**: Still extremely powerful due to the Coercion ability (combat cards as resources).
- **Saxony Empire + Innovative**: An aggressive, objective-rushing powerhouse. Unlimited stars from combat mean you control the game pace.
- **Polania Republic + Innovative**: Mobility meets cheaper upgrades. Good for encounter-heavy playstyles.
- **Nordic Kingdoms + Engineering**: Specific strategies involving workers and seaworthy can be surprisingly fast.
- **Movement Upgrade**: Speed is life. prioritizing the Move upgrade is essential for almost every faction.
- **Bottom Actions**: Scythe is an engine builder. Always try to align your Top Action with a useful Bottom Action.
"""
ISTANBUL_STRATEGY = """
Istanbul is a race. Efficiency of movement is everything.
1.  **The Fountain Loop**: Plan your routes in loops that bring you back to the Fountain (central tile) to recall assistants. A strict back-and-forth is inefficient.
2.  **Wainwright Rush**: Expanding your wheelbarrow early (to max size) grants a Ruby and makes all future goods collection massive. This is a common opening gambit.
3.  **Mosque Tiles**:
    - **Red/Yellow Mosques**: Getting the "Fifth Assistant" tile early is a game momentum changer.
    - **Blue Mosque**: The extra movement die can be useful, but is often less consistent than the extra assistant.
- **Dice Game**: Prioritize **Mosque Tiles** over single Rubies in the early game. The passive income or extra dice pay off huge dividends in later rounds.
- **Choose & Write**: Watch your opponents! If an opponent chooses an action that benefits you (e.g., "All players gain 1 Good"), position yourself to maximize it without spending your own turn.
"""
STRATEGIES = {
    "ark-nova": {
        "tier": "S",
        "content": ARK_NOVA_STRATEGY,
        "author": "BGG Community / BGA Stats",
    },
    "terraforming-mars": {
        "tier": "S",
        "content": TM_STRATEGY,
        "author": "Reddit / TMC",
    },
    "scythe": {
        "tier": "S",
        "content": SCYTHE_STRATEGY,
        "author": "Beloved Pacifist Data",
    },
    "istanbul": {
        "tier": "A",
        "content": ISTANBUL_STRATEGY,
        "author": "Tournament Meta",
    },
}


def populate_strategies():
    print("Starting strategy population...")
    for slug, data in STRATEGIES.items():
        try:
            payload = {
                "game_slug": slug,
                "tier_rating": data["tier"],
                "strategy_content": data["content"],
                "author": data["author"],
            }
            res = supabase._client.table("strategy_tiers").insert(payload).execute()
            if res.data:
                print(f"✅ Strategy added for {slug}")
            else:
                print(f"⚠️ Failed to add strategy for {slug} (No data returned)")
        except Exception as e:
            print(f"❌ Error for {slug}: {e}")


if __name__ == "__main__":
    populate_strategies()
