#!/usr/bin/env python3
"""Canonical Stage 6 build/certification entry point."""
import argparse

from .stage6_production_assembly import OUT, build, certify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--certify", action="store_true", help="run two isolated builds and publish certified artifacts")
    args = parser.parse_args()
    result = certify(OUT) if args.certify else build(OUT)
    print(result["status"])
    print(result["audit_status"])
    print(result["production_assembly_id"])


if __name__ == "__main__":
    main()
