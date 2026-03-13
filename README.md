# Arms Race Mechanics

**Keep AI nations technologically credible without killing player research.**

Arms Race Mechanics fixes one of HOI4's most common late-game problems: countries falling absurdly far behind in branches they should realistically be able to support. Majors stop showing up with bizarre gaps in armor, air, radar, or naval tech. Regional powers stay dangerous in their strongest areas. Minors stay relevant without becoming ahistorical superpowers.

ARM gives each country a credible technological baseline based on its power, industry, and military profile. Countries stay closer to the curve, but the frontier is still left for active research. By default, the system is AI-only, so your own research game stays fully in your hands.

**What that means in practice:** stronger AI competition, fewer immersion-breaking tech gaps, more credible minors, and late-game wars decided more by production, planning, and execution instead of one side still using outdated equipment trees.

**Version:** 1.0.0 | **HOI4:** 1.17.4.1+ | **DLC Required:** None

**Steam Workshop:** https://steamcommunity.com/sharedfiles/filedetails/?id=3683996696

---

## What changes in your game

- **AI nations stay near a believable baseline.** Majors no longer drift years behind in branches they obviously have the economy and slots to support.
- **Wars get harder to snowball.** Nations under pressure catch up faster, so one bad year does not automatically become permanent tech irrelevance.
- **Minor nations contribute.** Romania gets artillery. Siam gets basic fighters. They are not world leaders, but they stop being free wins.
- **Late-game wars stay competitive.** 1944-45 conflicts are more often decided by production, planning, and execution instead of wild tech mismatches.
- **Your research choices matter more.** With a stronger baseline across the world, smart specialization and timing create the real edge.

---

## How it works

Every nation is scored on five dimensions: **economy, science, mobilization, resources, and war posture**. That score places them into one of six power tiers, from Micro to Superpower. Each tier sets a technology lag (how many years behind the frontier) and a quarterly grant cap (how many techs per cycle). Under the default balanced rules, ARM also keeps auto-grants at least one year behind the frontier so manual research keeps a real role.

| Tier | Name | Base Lag | Grants/Quarter |
|---|---|---|---|
| 5 | Superpower | 0.0 years | 6 |
| 4 | Great Power | 0.5 years | 5 |
| 3 | Regional Power | 1.5 years | 4 |
| 2 | Minor Industrial | 3.0 years | 3 |
| 1 | Minor | 5.0 years | 2 |
| 0 | Micro | 7.0 years | 1 |

On top of global power, four **branch competence** scores (Land, Air, Naval, Industry) control which specific tech categories a nation receives. A country with 50 dockyards and no air force gets destroyers and cruisers, not fighters. A landlocked nation with heavy industry gets tanks and artillery, not submarines. Tech grants follow what a country can plausibly support rather than using a flat one-size-fits-all dump.

Nations at war, in factions with stronger allies, or losing badly get catch-up bonuses that reduce their tech lag. Puppet nations benefit from their overlord's strength. The system is designed to prevent the snowball effect where one lost campaign leads to permanent technological irrelevance.

Evaluation runs monthly on a rotating third of all countries for performance. The system runs AI-only by default, so players keep full control of their own research unless they opt in.

---

## Features

- Six power tiers (Micro to Superpower) with hysteresis to prevent oscillation
- Four independent branch competence scores gate access to specific tech categories
- Technologies granted quarterly in strict priority order with configurable caps
- War, faction, and desperation catch-up bonuses for nations under pressure
- Anti-death-spiral system keeps late-game wars competitive
- Puppet tech sharing scales with overlord strength
- Per-tier and per-branch research speed national spirits (+10% to -10%)
- Historical bias mode boosts historically advanced nations in their strongest branches
- DLC-aware: Man the Guns, No Step Back, and By Blood Alone techs gated behind `has_dlc`
- 13 game rules for control over scope, intensity, and behavior
- AI-only by default with opt-in for player nations

---

## Game rules

| Rule | Default | Options |
|---|---|---|
| Scope | AI Only | AI Only / Everyone / Disabled |
| Intensity | Balanced | Relaxed / Balanced / Aggressive / Historical |
| Compatibility Profile | Auto Detect | Auto Detect / Vanilla / bundled major-mod profiles |
| Tech Scope | All Except Doctrines | Core Only / Core + Air/Naval / All Except Doctrines / Everything |
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

## Mod compatibility

ARM ships with built-in compatibility profiles that auto-detect your mod setup. No patches, no sub-mods, no load order headaches. Just enable both mods and leave Compatibility Profile on Auto Detect.

**Bundled profiles:** Road to 56, Kaiserreich, Kaiserredux, BlackICE, Cold War Iron Curtain, Endsieg, Extended Tech Tree 1960, Novum Vexillum, Rise of Nations, The New Order, Millennium Dawn, The Fire Rises, The Great War, The Great War Redux

Each profile uses mod-specific tech grant lists and tier thresholds. You can force a specific profile manually in the lobby if needed.

---

## Load order

No hard dependencies. When using a bundled profile, load ARM after the target overhaul or expansion mod.

---

## For modders and maintainers

**Debug tools** - Set the Power Visibility game rule to Debug to inspect power scores, branch competence, effective lag, target years, and force immediate evaluation cycles via decisions.

**Rebuilding compatibility profiles:**

```bash
python Tools/rebuild_builtin_major_compat.py
```

- Custom category tags: `Tools/custom_mappings.txt`
- Generated staging bundles: `compat_generated/`
- Baked-in profile files: `common/scripted_effects/arm_compat_generated_*.txt`
