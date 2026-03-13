#!/usr/bin/env python3
"""
Generate ARM compatibility bundles for the major HOI4 Workshop mods installed locally.

This script reuses the ARM tech generator module to build one compat bundle per
major installed mod. Each bundle contains:

  - common/scripted_effects/auto_research_techlist.txt
  - common/scripted_effects/arm_evaluation.txt (only when a preset is used)
  - Tools/arm_tech_report.txt
  - README.txt
  - manifest.json

The output is written under compat_generated/<slug>/.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import stat
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_PATH = Path(__file__).resolve().parent / "arm_tech_generator.py"
CUSTOM_MAPPINGS_PATH = Path(__file__).resolve().parent / "custom_mappings.txt"
BASE_EVALUATION_PATH = REPO_ROOT / "common" / "scripted_effects" / "arm_evaluation.txt"
DEFAULT_HOI4_PATH = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
DEFAULT_WORKSHOP_ROOT = Path(r"E:\SteamLibrary\steamapps\workshop\content\394360")
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "compat_generated"


MAJOR_MOD_PROFILES = [
    {
        "workshop_id": "1137372539",
        "slug": "blackice",
        "display_name": "BlackICE Historical Immersion Mod",
        "mode": "overhaul",
        "preset": {
            "name": "blackice",
            "description": "BlackICE - denser WW2 industrial and doctrine scale",
            "tier_thresholds": {
                "superpower": 240,
                "great_power": 165,
                "regional_power": 95,
                "minor_industrial": 48,
                "minor": 21,
            },
        },
    },
    {
        "workshop_id": "1458561226",
        "slug": "cold_war_iron_curtain",
        "display_name": "Cold War Iron Curtain: A World Divided",
        "mode": "overhaul",
        "preset": {
            "name": "cold_war_iron_curtain",
            "description": "Cold War Iron Curtain - modern-era global economy scale",
            "tier_thresholds": {
                "superpower": 450,
                "great_power": 310,
                "regional_power": 180,
                "minor_industrial": 90,
                "minor": 40,
            },
        },
    },
    {
        "workshop_id": "1521695605",
        "slug": "kaiserreich",
        "display_name": "Kaiserreich",
        "mode": "overhaul",
        "preset_name": "kaiserreich",
    },
    {
        "workshop_id": "1532883122",
        "slug": "endsieg",
        "display_name": "EndsiegDEV",
        "mode": "overhaul",
        "preset": {
            "name": "endsieg",
            "description": "Endsieg - late-war scenario with roughly vanilla industrial scale",
            "tier_thresholds": {
                "superpower": 220,
                "great_power": 150,
                "regional_power": 90,
                "minor_industrial": 45,
                "minor": 20,
            },
        },
    },
    {
        "workshop_id": "1778255798",
        "slug": "extended_tech_tree_1960",
        "display_name": "Extended Tech Tree 1960",
        "mode": "expansion",
        "preset": {
            "name": "extended_tech_tree_1960",
            "description": "Extended Tech Tree 1960 - vanilla-scale economy with longer research tails",
            "tier_thresholds": {
                "superpower": 220,
                "great_power": 150,
                "regional_power": 90,
                "minor_industrial": 45,
                "minor": 20,
            },
        },
    },
    {
        "workshop_id": "1827273767",
        "slug": "novum_vexillum",
        "display_name": "Novum Vexillum",
        "mode": "overhaul",
        "preset": {
            "name": "novum_vexillum",
            "description": "Novum Vexillum - modern-era economy and force structure",
            "tier_thresholds": {
                "superpower": 380,
                "great_power": 260,
                "regional_power": 150,
                "minor_industrial": 75,
                "minor": 33,
            },
        },
    },
    {
        "workshop_id": "2026448968",
        "slug": "rise_of_nations",
        "display_name": "Rise of Nations",
        "mode": "overhaul",
        "preset": {
            "name": "rise_of_nations",
            "description": "Rise of Nations - modern-era economy with large branch breadth",
            "tier_thresholds": {
                "superpower": 400,
                "great_power": 280,
                "regional_power": 160,
                "minor_industrial": 80,
                "minor": 35,
            },
        },
    },
    {
        "workshop_id": "2076426030",
        "slug": "kaiserredux",
        "display_name": "KaiserreduX",
        "mode": "overhaul",
        "preset": {
            "name": "kaiserredux",
            "description": "Kaiserredux - Kaiserreich-scale economy with more content inflation",
            "tier_thresholds": {
                "superpower": 255,
                "great_power": 175,
                "regional_power": 102,
                "minor_industrial": 50,
                "minor": 22,
            },
        },
    },
    {
        "workshop_id": "2438003901",
        "slug": "the_new_order",
        "display_name": "The New Order: Last Days of Europe",
        "mode": "overhaul",
        "preset": {
            "name": "the_new_order",
            "description": "The New Order - 1960s start with larger baseline economies",
            "tier_thresholds": {
                "superpower": 300,
                "great_power": 205,
                "regional_power": 120,
                "minor_industrial": 60,
                "minor": 25,
            },
        },
    },
    {
        "workshop_id": "2777392649",
        "slug": "millennium_dawn",
        "display_name": "Millennium Dawn: A Modern Day Mod",
        "mode": "overhaul",
        "preset_name": "millennium_dawn",
    },
    {
        "workshop_id": "3350890356",
        "slug": "the_fire_rises",
        "display_name": "The Fire Rises",
        "mode": "overhaul",
        "preset": {
            "name": "the_fire_rises",
            "description": "The Fire Rises - near-modern economy and technology scale",
            "tier_thresholds": {
                "superpower": 420,
                "great_power": 290,
                "regional_power": 170,
                "minor_industrial": 85,
                "minor": 35,
            },
        },
    },
    {
        "workshop_id": "3365515312",
        "slug": "great_war_redux",
        "display_name": "The Great War Redux - 1.17.*",
        "mode": "overhaul",
        "preset": {
            "name": "great_war_redux",
            "description": "The Great War Redux - WW1 economy with expanded content",
            "tier_thresholds": {
                "superpower": 185,
                "great_power": 125,
                "regional_power": 72,
                "minor_industrial": 36,
                "minor": 15,
            },
        },
    },
    {
        "workshop_id": "699709023",
        "slug": "great_war",
        "display_name": "Hearts of Iron IV: The Great War",
        "mode": "overhaul",
        "preset_name": "great_war",
    },
    {
        "workshop_id": "820260968",
        "slug": "road_to_56",
        "display_name": "The Road to 56",
        "mode": "expansion",
        "preset_name": "road_to_56",
    },
]


def load_generator():
    spec = importlib.util.spec_from_file_location("arm_tech_generator", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def resolve_preset(generator, profile: dict) -> dict | None:
    if "preset" in profile:
        return profile["preset"]
    preset_name = profile.get("preset_name")
    if preset_name:
        preset = dict(generator.PRESETS[preset_name])
        preset["name"] = preset_name
        return preset
    return None


def apply_thresholds_to_evaluation(text: str, thresholds: dict) -> str:
    replacements = [
        (r"(arm_tier_index < 1\s*\}\s*check_variable = \{\s*arm_global_power > )\d+(\s*\})", thresholds["minor"] + 5),
        (r"(arm_tier_index < 2\s*\}\s*check_variable = \{\s*arm_global_power > )\d+(\s*\})", thresholds["minor_industrial"] + 5),
        (r"(arm_tier_index < 3\s*\}\s*check_variable = \{\s*arm_global_power > )\d+(\s*\})", thresholds["regional_power"] + 5),
        (r"(arm_tier_index < 4\s*\}\s*check_variable = \{\s*arm_global_power > )\d+(\s*\})", thresholds["great_power"] + 5),
        (r"(arm_tier_index < 5\s*\}\s*check_variable = \{\s*arm_global_power > )\d+(\s*\})", thresholds["superpower"] + 5),
        (r"(arm_tier_index > 4\s*\}\s*check_variable = \{\s*arm_global_power < )\d+(\s*\})", thresholds["superpower"] - 5),
        (r"(arm_tier_index > 3\s*\}\s*check_variable = \{\s*arm_global_power < )\d+(\s*\})", thresholds["great_power"] - 5),
        (r"(arm_tier_index > 2\s*\}\s*check_variable = \{\s*arm_global_power < )\d+(\s*\})", thresholds["regional_power"] - 5),
        (r"(arm_tier_index > 1\s*\}\s*check_variable = \{\s*arm_global_power < )\d+(\s*\})", thresholds["minor_industrial"] - 5),
        (r"(arm_tier_index > 0\s*\}\s*check_variable = \{\s*arm_global_power < )\d+(\s*\})", thresholds["minor"] - 5),
    ]

    updated = text
    for pattern, value in replacements:
        updated, count = re.subn(pattern, rf"\g<1>{value}\g<2>", updated, count=1, flags=re.S)
        if count != 1:
            raise RuntimeError(f"Failed to apply preset threshold replacement for pattern: {pattern}")
    return updated


def write_preset_evaluation(output_path: Path, preset: dict):
    base_text = BASE_EVALUATION_PATH.read_text(encoding="utf-8-sig")
    patched = apply_thresholds_to_evaluation(base_text, preset["tier_thresholds"])
    header = (
        "##########################################################\n"
        f"# Generated preset override: {preset['description']}\n"
        "# This file is generated by Tools/generate_big_mod_compat.py\n"
        "##########################################################\n\n"
    )
    output_path.write_text(header + patched, encoding="utf-8")


def parse_descriptor_name(mod_dir: Path) -> str:
    descriptor = mod_dir / "descriptor.mod"
    if not descriptor.exists():
        return mod_dir.name
    text = descriptor.read_text(encoding="utf-8-sig", errors="replace")
    match = re.search(r'^name\s*=\s*"([^"]+)"', text, re.M)
    return match.group(1) if match else mod_dir.name


def handle_remove_readonly(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        raise exc_info[1]


def build_final_techs(generator, vanilla_techs: list, mod_techs: list) -> list:
    vanilla_tech_ids = {tech.tech_id for tech in vanilla_techs}
    final_techs = [tech for tech in vanilla_techs if tech.tech_id not in {m.tech_id for m in mod_techs}]
    final_techs.extend(mod_techs)
    generator.calculate_dependency_depths(final_techs)
    return final_techs


def write_bundle_readme(path: Path, profile: dict, actual_name: str, stats: dict, preset: dict | None):
    lines = [
        f"ARM compatibility bundle for {actual_name}",
        "",
        f"Workshop ID: {profile['workshop_id']}",
        f"Bundle slug: {profile['slug']}",
        f"Generation mode: {profile['mode']}",
        f"Parsed techs: {stats['techs_total']}",
        f"Unknown techs: {stats['unknown_total']}",
        f"Doctrines detected: {stats['doctrine_total']}",
    ]
    if preset:
        lines.append(f"Preset thresholds: {preset.get('name', 'custom')}")
    lines.extend(
        [
            "",
            "Files in this bundle:",
            "- common/scripted_effects/auto_research_techlist.txt",
            "- Tools/arm_tech_report.txt",
        ]
    )
    if preset:
        lines.append("- common/scripted_effects/arm_evaluation.txt")
    lines.extend(
        [
            "",
            "Load after Arms Race Mechanics and the target mod.",
            "This bundle is generated output, not hand-authored logic.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate ARM compat bundles for major installed Workshop mods.")
    parser.add_argument("--hoi4", default=str(DEFAULT_HOI4_PATH), help="Path to the HOI4 install directory")
    parser.add_argument("--workshop-root", default=str(DEFAULT_WORKSHOP_ROOT), help="Path to workshop/content/394360")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Where compat bundles should be written")
    args = parser.parse_args()

    hoi4_dir = Path(args.hoi4)
    workshop_root = Path(args.workshop_root)
    output_root = Path(args.output_root)

    if not hoi4_dir.exists():
        raise SystemExit(f"HOI4 directory not found: {hoi4_dir}")
    if not workshop_root.exists():
        raise SystemExit(f"Workshop root not found: {workshop_root}")

    generator = load_generator()
    custom_mappings = generator.load_custom_mappings(CUSTOM_MAPPINGS_PATH)
    if custom_mappings:
        generator.CATEGORY_MAP.update(custom_mappings)

    vanilla_techs = generator.parse_tech_files(hoi4_dir / "common" / "technologies", "vanilla", False)

    if output_root.exists():
        shutil.rmtree(output_root, onexc=handle_remove_readonly)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = {"generated_bundles": []}

    for profile in MAJOR_MOD_PROFILES:
        mod_dir = workshop_root / profile["workshop_id"]
        if not mod_dir.exists():
            continue

        actual_name = parse_descriptor_name(mod_dir)
        mod_techs = generator.parse_tech_files(mod_dir / "common" / "technologies", profile["slug"], False)
        final_techs = build_final_techs(generator, vanilla_techs, mod_techs)
        preset = resolve_preset(generator, profile)

        bundle_root = output_root / profile["slug"]
        scripted_effects_dir = bundle_root / "common" / "scripted_effects"
        reports_dir = bundle_root / "Tools"
        scripted_effects_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        generator.generate_output_files(
            final_techs,
            scripted_effects_dir,
            profile["mode"],
            profile["slug"],
            report_dir=reports_dir,
        )

        if preset:
            write_preset_evaluation(scripted_effects_dir / "arm_evaluation.txt", preset)

        stats = {
            "techs_total": len(mod_techs),
            "unknown_total": sum(1 for tech in mod_techs if tech.branch == "unknown"),
            "doctrine_total": sum(1 for tech in mod_techs if tech.is_doctrine),
        }
        write_bundle_readme(bundle_root / "README.txt", profile, actual_name, stats, preset)

        bundle_manifest = {
            "workshop_id": profile["workshop_id"],
            "slug": profile["slug"],
            "display_name": actual_name,
            "mode": profile["mode"],
            "preset": preset["name"] if preset else None,
            "stats": stats,
        }
        (bundle_root / "manifest.json").write_text(json.dumps(bundle_manifest, indent=2) + "\n", encoding="utf-8")
        manifest["generated_bundles"].append(bundle_manifest)

    (output_root / "index.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(manifest['generated_bundles'])} major-mod compat bundles in {output_root}")
    for item in manifest["generated_bundles"]:
        print(
            f"  - {item['slug']}: techs={item['stats']['techs_total']} "
            f"unknown={item['stats']['unknown_total']} preset={item['preset']}"
        )


if __name__ == "__main__":
    main()
