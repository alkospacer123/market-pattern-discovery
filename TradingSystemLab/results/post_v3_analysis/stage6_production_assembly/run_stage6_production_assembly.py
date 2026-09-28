#!/usr/bin/env python3
from stage6_production_assembly import OUT, build

if __name__ == "__main__":
    result = build(OUT)
    print(result["status"])
    print(result["production_assembly_id"])
