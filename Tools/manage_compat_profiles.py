#!/usr/bin/env python3
"""
Unified ARM compatibility profile manager.

This is the single entrypoint for:
  - listing known/generated profiles
  - generating compat bundles for supported major Workshop mods
  - building bundled runtime profiles from compat_generated/
  - rebuilding both stages in one command
  - creating or updating a compat bundle for an arbitrary mod folder
"""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import sys
from pathlib import Path

import build_builtin_compat_profiles as builtin_builder
import generate_big_mod_compat as big_mod


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "compat_generated"


def handle_remove_readonly(func, path, exc_info):
    try:
        Path(path).chmod(stat.S_IWRITE)
        func(path)
    except OSError:
        raise exc_info[1]


def load_index(path: Path) -> dict:
    if not path.exists():
        return {"generated_bundles": []}
    return json.loads(path.read_text(encoding="utf-8"))


def write_index(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def get_generator():
    generator = big_mod.load_generator()
    custom_mappings = generator.load_custom_mappings(big_mod.CUSTOM_MAPPINGS_PATH)
    if custom_mappings:
        generator.CATEGORY_MAP.update(custom_mappings)
    return generator


def build_bundle(
    *,
    generator,
    hoi4_dir: Path,
    mod_dir: Path,
    slug: str,
    display_name: str | None,
    mode: str,
    preset: dict | None,
    output_root: Path,
    workshop_id: str | None,
) -> dict:
    vanilla_techs = generator.parse_tech_files(hoi4_dir / "common" / "technologies", "vanilla", False)
    mod_techs = generator.parse_tech_files(mod_dir / "common" / "technologies", slug, False)
    final_techs = big_mod.build_final_techs(generator, vanilla_techs, mod_techs)

    bundle_root = output_root / slug
    if bundle_root.exists():
        shutil.rmtree(bundle_root, onexc=handle_remove_readonly)

    scripted_effects_dir = bundle_root / "common" / "scripted_effects"
    reports_dir = bundle_root / "Tools"
    scripted_effects_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    generator.generate_output_files(
        final_techs,
        scripted_effects_dir,
        mode,
        slug,
        report_dir=reports_dir,
    )

    if preset:
        big_mod.write_preset_evaluation(scripted_effects_dir / "arm_evaluation.txt", preset)

    actual_name = display_name or big_mod.parse_descriptor_name(mod_dir)
    stats = {
        "techs_total": len(mod_techs),
        "unknown_total": sum(1 for tech in mod_techs if tech.branch == "unknown"),
        "doctrine_total": sum(1 for tech in mod_techs if tech.is_doctrine),
    }

    profile = {
        "workshop_id": workshop_id or "",
        "slug": slug,
        "display_name": actual_name,
        "mode": mode,
        "preset": preset["name"] if preset else None,
        "stats": stats,
    }

    big_mod.write_bundle_readme(bundle_root / "README.txt", profile, actual_name, stats, preset)
    (bundle_root / "manifest.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    return profile


def upsert_index_entry(index: dict, entry: dict) -> None:
    bundles = index.setdefault("generated_bundles", [])
    for idx, existing in enumerate(bundles):
        if existing.get("slug") == entry["slug"]:
            bundles[idx] = entry
            break
    else:
        bundles.append(entry)

    bundles.sort(key=lambda item: item["slug"])


def resolve_major_profiles(selected_slugs: list[str] | None) -> list[dict]:
    profiles = list(big_mod.MAJOR_MOD_PROFILES)
    if not selected_slugs:
        return profiles

    wanted = set(selected_slugs)
    filtered = [profile for profile in profiles if profile["slug"] in wanted]
    missing = sorted(wanted - {profile["slug"] for profile in filtered})
    if missing:
        raise SystemExit(f"Unknown profile slug(s): {', '.join(missing)}")
    return filtered


def resolve_preset_from_args(generator, args) -> dict | None:
    if args.preset_name:
        if args.preset_name not in generator.PRESETS:
            raise SystemExit(f"Unknown preset: {args.preset_name}")
        preset = dict(generator.PRESETS[args.preset_name])
        preset["name"] = args.preset_name
        return preset

    threshold_values = [
        args.superpower,
        args.great_power,
        args.regional_power,
        args.minor_industrial,
        args.minor,
    ]
    if any(value is not None for value in threshold_values):
        if not all(value is not None for value in threshold_values):
            raise SystemExit(
                "Custom thresholds require all five values: "
                "--superpower, --great-power, --regional-power, --minor-industrial, --minor"
            )
        return {
            "name": args.preset_label or args.slug,
            "description": args.preset_description or f"Custom preset for {args.slug}",
            "tier_thresholds": {
                "superpower": args.superpower,
                "great_power": args.great_power,
                "regional_power": args.regional_power,
                "minor_industrial": args.minor_industrial,
                "minor": args.minor,
            },
        }

    return None


def command_list(_args) -> int:
    index = load_index(DEFAULT_OUTPUT_ROOT / "index.json")
    generated = {item["slug"]: item for item in index.get("generated_bundles", [])}

    print("Known builtin profiles:")
    for profile in big_mod.MAJOR_MOD_PROFILES:
        generated_entry = generated.get(profile["slug"])
        suffix = "generated" if generated_entry else "missing"
        print(f"  - {profile['slug']}: {profile['display_name']} [{suffix}]")

    extra = sorted(slug for slug in generated if slug not in {profile['slug'] for profile in big_mod.MAJOR_MOD_PROFILES})
    if extra:
        print("Custom/generated-only bundles:")
        for slug in extra:
            item = generated[slug]
            print(f"  - {slug}: {item.get('display_name', slug)}")
    return 0


def command_generate_major(args) -> int:
    hoi4_dir = Path(args.hoi4)
    workshop_root = Path(args.workshop_root)
    output_root = Path(args.output_root)

    if not hoi4_dir.exists():
        raise SystemExit(f"HOI4 directory not found: {hoi4_dir}")
    if not workshop_root.exists():
        raise SystemExit(f"Workshop root not found: {workshop_root}")

    profiles = resolve_major_profiles(args.profile)
    generator = get_generator()
    output_root.mkdir(parents=True, exist_ok=True)
    index = load_index(output_root / "index.json")

    written: list[dict] = []
    for profile in profiles:
        mod_dir = workshop_root / profile["workshop_id"]
        if not mod_dir.exists():
            if args.fail_missing:
                raise SystemExit(f"Workshop mod not found for {profile['slug']}: {mod_dir}")
            continue

        preset = big_mod.resolve_preset(generator, profile)
        entry = build_bundle(
            generator=generator,
            hoi4_dir=hoi4_dir,
            mod_dir=mod_dir,
            slug=profile["slug"],
            display_name=None,
            mode=profile["mode"],
            preset=preset,
            output_root=output_root,
            workshop_id=profile["workshop_id"],
        )
        upsert_index_entry(index, entry)
        written.append(entry)

    write_index(output_root / "index.json", index)

    print(f"Generated {len(written)} compat bundle(s) in {output_root}")
    for item in written:
        print(
            f"  - {item['slug']}: techs={item['stats']['techs_total']} "
            f"unknown={item['stats']['unknown_total']} preset={item['preset']}"
        )
    return 0


def command_build_builtin(_args) -> int:
    builtin_builder.main()
    return 0


def command_rebuild(args) -> int:
    command_generate_major(args)
    command_build_builtin(args)
    print("Rebuilt bundled ARM compatibility profiles.")
    return 0


def command_create(args) -> int:
    hoi4_dir = Path(args.hoi4)
    output_root = Path(args.output_root)
    if not hoi4_dir.exists():
        raise SystemExit(f"HOI4 directory not found: {hoi4_dir}")

    if args.mod_path:
        mod_dir = Path(args.mod_path)
        workshop_id = args.workshop_id
    else:
        workshop_root = Path(args.workshop_root)
        if not workshop_root.exists():
            raise SystemExit(f"Workshop root not found: {workshop_root}")
        mod_dir = workshop_root / args.workshop_id
        workshop_id = args.workshop_id

    if not mod_dir.exists():
        raise SystemExit(f"Mod directory not found: {mod_dir}")

    generator = get_generator()
    preset = resolve_preset_from_args(generator, args)

    entry = build_bundle(
        generator=generator,
        hoi4_dir=hoi4_dir,
        mod_dir=mod_dir,
        slug=args.slug,
        display_name=args.display_name,
        mode=args.mode,
        preset=preset,
        output_root=output_root,
        workshop_id=workshop_id,
    )

    index_path = output_root / "index.json"
    index = load_index(index_path)
    upsert_index_entry(index, entry)
    write_index(index_path, index)

    print(f"Wrote compat bundle: {entry['slug']}")
    print(f"  path: {output_root / entry['slug']}")
    print(f"  mode: {entry['mode']}")
    print(f"  preset: {entry['preset']}")
    return 0


def add_shared_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--hoi4", default=str(big_mod.DEFAULT_HOI4_PATH), help="Path to the HOI4 install directory")
    parser.add_argument(
        "--workshop-root",
        default=str(big_mod.DEFAULT_WORKSHOP_ROOT),
        help="Path to workshop/content/394360",
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Bundle output directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage ARM compatibility profiles from a single entrypoint.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List known builtin profiles and generated bundles")
    list_parser.set_defaults(func=command_list)

    generate_parser = subparsers.add_parser(
        "generate-major",
        help="Generate compat bundles for supported major Workshop mods into compat_generated/",
    )
    add_shared_generation_args(generate_parser)
    generate_parser.add_argument(
        "--profile",
        action="append",
        help="Only generate the specified builtin profile slug. Repeatable.",
    )
    generate_parser.add_argument(
        "--fail-missing",
        action="store_true",
        help="Exit with an error if a requested Workshop mod is not installed.",
    )
    generate_parser.set_defaults(func=command_generate_major)

    build_parser_cmd = subparsers.add_parser(
        "build-builtin",
        help="Compile compat_generated/ bundles into runtime scripted effects under common/scripted_effects/",
    )
    build_parser_cmd.set_defaults(func=command_build_builtin)

    rebuild_parser = subparsers.add_parser(
        "rebuild",
        help="Generate major Workshop compat bundles and rebuild bundled runtime profiles.",
    )
    add_shared_generation_args(rebuild_parser)
    rebuild_parser.add_argument(
        "--profile",
        action="append",
        help="Only rebuild the specified builtin profile slug. Repeatable.",
    )
    rebuild_parser.add_argument(
        "--fail-missing",
        action="store_true",
        help="Exit with an error if a requested Workshop mod is not installed.",
    )
    rebuild_parser.set_defaults(func=command_rebuild)

    create_parser = subparsers.add_parser(
        "create",
        help="Create or update a compat bundle for an arbitrary mod path or Workshop ID.",
    )
    add_shared_generation_args(create_parser)
    source_group = create_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--mod-path", help="Path to the target mod directory")
    source_group.add_argument("--workshop-id", help="Workshop ID under --workshop-root")
    create_parser.add_argument("--slug", required=True, help="Output bundle slug")
    create_parser.add_argument(
        "--mode",
        choices=["expansion", "overhaul"],
        default="overhaul",
        help="Generation mode for the compat bundle",
    )
    create_parser.add_argument("--display-name", help="Override display name written into the bundle manifest")
    create_parser.add_argument("--preset-name", help="Use an existing preset from arm_tech_generator.py")
    create_parser.add_argument("--preset-label", help="Name for a custom threshold preset")
    create_parser.add_argument("--preset-description", help="Description for a custom threshold preset")
    create_parser.add_argument("--superpower", type=int, help="Custom superpower threshold")
    create_parser.add_argument("--great-power", dest="great_power", type=int, help="Custom great power threshold")
    create_parser.add_argument(
        "--regional-power",
        dest="regional_power",
        type=int,
        help="Custom regional power threshold",
    )
    create_parser.add_argument(
        "--minor-industrial",
        dest="minor_industrial",
        type=int,
        help="Custom minor industrial threshold",
    )
    create_parser.add_argument("--minor", type=int, help="Custom minor threshold")
    create_parser.set_defaults(func=command_create)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
