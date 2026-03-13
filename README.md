# Arms Race Mechanics

A Hearts of Iron IV mod that dynamically grants technologies to nations based on their global power, military competence, and industrial capacity, making the world's tech race feel realistic without scripting every country by hand.

**Version:** 1.0.0 | **HOI4:** 1.17.4.1

---

## Features

**Power-based technology granting**
- Nations are ranked into six power tiers (Micro through Superpower) based on economy, science, mobilisation, resources, and war posture
- Stronger nations research faster and unlock more tech categories; weaker nations lag behind but never become completely obsolete
- Technologies are granted quarterly in strict priority order (infantry first, nuclear and rockets last)

**Branch competence system**
- Four independent competence scores (Land, Air, Naval, Industry/Electronics) control which categories a nation can receive
- A country with a large navy but no air force gets naval tech, not fighters
- Competence scores feed into per-branch research speed spirits (+10% to -10%)

**Catch-up and anti-death-spiral mechanics**
- War bonus, faction bonus, and desperation bonus reduce tech lag for nations under pressure
- Puppet tech sharing lets subjects benefit from their overlord's tier
- Nations losing a war get accelerated research to keep late-game fights competitive

**Historical bias mode**
- Optional preset that boosts historically advanced nations in their strongest branches

**DLC-aware**
- Man the Guns, No Step Back, and By Blood Alone techs are gated behind `has_dlc`, so players without a DLC waste zero grant slots on technologies that do not exist in their game

---

## Game rules

| Rule | Default | Options |
|---|---|---|
| Scope | AI Only | AI Only / Everyone / Disabled |
| Intensity | Balanced | Relaxed / Balanced / Aggressive / Historical |
| Compatibility Profile | Auto Detect | Auto Detect / Vanilla / bundled major-mod profiles |
| Tech Scope | Core + Air/Naval | Core Only / Core + Air/Naval / All Except Doctrines / Everything |
| Doctrine Handling | Disabled | Disabled / AI Only / Everyone |
| Advanced Tech | Excluded | Excluded / Superpowers Only / Included |
| War/Faction Catch-Up | Standard | Disabled / Standard / Enhanced |
| Grant Cap | Standard | Strict / Standard / Unlimited |
| Notifications | Major Only | Silent / Major Only / All |
| Power Visibility | Own Country | Hidden / Own Country / All (Debug) |
| Puppet Sharing | Standard | Disabled / Standard / Enhanced |
| Anti-Death Spiral | Standard | Disabled / Standard / Enhanced |
| Research Speed Bonuses | Full | Full / Tier Only / Disabled |

---

## How it works

Every month, one-third of the world's countries are evaluated (3-bucket round-robin for performance). Each country's evaluation:

1. **Score** - calculate global power and four branch competence scores
2. **Tier** - assign a power tier with hysteresis
3. **Categories** - determine which tech categories the country is allowed to receive
4. **Lag** - compute effective technology lag per branch
5. **Target year** - determine the latest tech year each branch can grant
6. **Grant** - walk the priority list and grant eligible techs up to the quarterly cap

---

## Power tiers

| Tier | Name | Power | Base Lag | Grants/Quarter |
|---|---|---|---|---|
| 5 | Superpower | 220+ | 0.0 years | 6 |
| 4 | Great Power | 150-219 | 0.5 years | 5 |
| 3 | Regional Power | 90-149 | 1.5 years | 4 |
| 2 | Minor Industrial | 45-89 | 3.0 years | 3 |
| 1 | Minor | 20-44 | 5.0 years | 2 |
| 0 | Micro | 0-19 | 7.0 years | 1 |

---

## Mod compatibility

ARM now ships as one mod folder with built-in compatibility profiles for major overhaul and expansion mods.

**For players**
- Enable ARM and the target mod as normal
- Leave `Compatibility Profile` on `Auto Detect` in normal use
- ARM will automatically switch to the matching built-in profile for supported major mods and fall back to vanilla otherwise
- If you need to force a specific profile, use the manual override in the lobby

**Bundled profiles**
- Road to 56
- Kaiserreich
- Kaiserredux
- BlackICE
- Cold War Iron Curtain
- Endsieg
- Extended Tech Tree 1960
- Novum Vexillum
- Rise of Nations
- The New Order
- Millennium Dawn
- The Fire Rises
- The Great War
- The Great War Redux

Each profile switches ARM to the matching generated tech grant lists. Overhaul profiles also use profile-specific tier thresholds.

**For maintainers**
- Rebuild the bundled profiles from installed Workshop mods with:

```bash
python Tools/rebuild_builtin_major_compat.py
```

- Custom category tags can be added to `Tools/custom_mappings.txt`
- The generated staging bundles are written to `compat_generated/`
- The baked in one-folder profile files are written to `common/scripted_effects/arm_compat_generated_*.txt`

---

## Load order

This mod has no hard dependencies. When using a bundled profile, load ARM after the target overhaul or expansion mod.

---

## Debug tools

When the Power Visibility game rule is set to Debug, decisions are available to inspect:
- Global power score and all components
- Branch competence scores
- Effective lag and target years per branch
- Force an immediate evaluation cycle
