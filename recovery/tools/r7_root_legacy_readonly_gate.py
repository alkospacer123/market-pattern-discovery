#!/usr/bin/env python3
"""Read-only root-legacy PR gate: Git tree scope, Markdown links, static Python imports.
Never imports target modules, runs repository code, touches FINAM or local LIVE.
"""
from __future__ import annotations
import argparse
import ast
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ARCHIVE = "09bca5641cb5bb367e84505ebfc6f8c7f35e2620"
ROOTS = {"docs":34,"research":4,"schemas":6,"scripts":7,"src":86,
         "tests":50,"config":17,"results":17,"evidence":5}
FILES = {"ARTIFACT_HANDOFF_VERIFICATION_REPORT.md",
 "CURRENT_ARTIFACT_STORAGE_STATUS.md","PERMANENT_MEMORY_DIAGNOSTIC_REPORT.md",
 "PERSISTENT_MEMORY_VERIFICATION_REPORT.md","SMOKE_RUN_V2_REPORT.md",
 "SMOKE_RUN_V3_REPORT.md","pyproject.toml"}
MODIFIED = {"README.md","AGENTS.md","ROADMAP.md","research_domains.md",
 "recovery/ROOT_LEGACY_AUDIT_2026-11-21.md",
 "recovery/LEGACY_DEPENDENCIES_AND_RETENTION.md"}
ADDED = {"recovery/R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md",
 "recovery/tools/r7_root_legacy_readonly_gate.py",
 ".github/workflows/r7-root-legacy-readonly.yml"}
PROTECTED = ("V20_TradingSystem_M15","ControlCenter","TradingResearchLab",
 "TradingSystemLab","IntradayLab","audit_only")
TEXT = {".md",".py",".ps1",".psm1",".psd1",".toml",".yml",".yaml"}
LINK = re.compile(r"\]\(([^)]+)\)")

def git(*args):
    return subprocess.check_output(("git",)+args,stderr=subprocess.PIPE).decode().strip()

def tree(ref):
    raw = subprocess.check_output(("git","ls-tree","-r","-z","--full-tree",ref))
    out = {}
    for entry in raw.split(b"\0"):
        if not entry: continue
        info, name = entry.split(b"\t",1)
        mode, kind, sha = info.decode().split()
        if kind != "blob": raise ValueError("UNEXPECTED_GIT_TYPE")
        path = name.decode("utf-8")
        if path in out: raise ValueError("DUPLICATE_GIT_PATH")
        out[path] = (mode,sha)
    return out

def directory_set(paths):
    d = set()
    for p in paths:
        parts = p.split("/")
        for j in range(1,len(parts)):
            d.add("/".join(parts[:j]))
    return d

def local_link(owner, ref):
    ref=ref.strip().strip("<>")
    if not ref or ref.startswith(("#","http:","https:","mailto:","data:","//")):
        return None
    ref=ref.split("#",1)[0].split("?",1)[0].split(' "',1)[0]
    ref=unquote(ref).replace(chr(92),"/")
    if not ref or ref.startswith("/"): return None
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner),ref))

def source_scan(before,after):
    old_targets=set(before)|directory_set(before)
    new_targets=set(after)|directory_set(after)
    scanned=0
    links=0
    broken=[]
    imports=[]
    references=[]
    dynamic=0
    dynamic_sites=[]
    omissions=[]
    for path in sorted(after):
        if Path(path).suffix.lower() not in TEXT: continue
        f=Path(path)
        if not f.is_file():
            omissions.append(("missing_checkout",path)); continue
        if f.stat().st_size > (8000000 if f.suffix.lower() == ".md" else 2000000):
            omissions.append(("large",path)); continue
        try: body=f.read_text("utf-8")
        except UnicodeError:
            omissions.append(("non_utf8",path)); continue
        scanned+=1
        if path.endswith(".md"):
            for m in LINK.finditer(body):
                target=local_link(path,m.group(1))
                if not target: continue
                links+=1
                if target in old_targets and target not in new_targets:
                    broken.append({"source":path,"missing_target":target})
        if path.endswith(".py"):
            try: parsed=ast.parse(body,filename=path)
            except SyntaxError:
                omissions.append(("ast_error",path)); continue
            for node in ast.walk(parsed):
                if isinstance(node,ast.Import):
                    modules=[a.name for a in node.names]
                elif isinstance(node,ast.ImportFrom):
                    modules=[node.module or ""]
                else: modules=[]
                for mod in modules:
                    if mod=="market_pattern_discovery" or mod.startswith(
                        ("market_pattern_discovery.","src.market_pattern_discovery")):
                        imports.append({"source":path,"line":node.lineno,"module":mod})
                if isinstance(node,ast.Call):
                    fn=node.func
                    name=getattr(fn,"id",getattr(fn,"attr",""))
                    if name in ("eval","exec","__import__","import_module"):
                        dynamic+=1
                        first=node.args[0] if node.args else None
                        literal=(first.value if isinstance(first,ast.Constant)
                                 and isinstance(first.value,str) else None)
                        dynamic_sites.append({
                            "path":path,"line":node.lineno,"call":name,
                            "arg_type":type(first).__name__ if first is not None else "NONE",
                            "literal_legacy":bool(literal and (
                                "market_pattern_discovery" in literal or
                                "unknown_universe_v1" in literal))
                        })
        if re.search(r"market_pattern_discovery|research_domains\.md|pyproject\.toml|unknown_universe_v1",body,re.I):
            references.append(path)
    return {"scanned_text":scanned,"links_checked":links,"newly_broken":broken,
            "legacy_imports":imports,"nonliteral_or_dynamic_calls_count":dynamic,
            "dynamic_sites":dynamic_sites,
            "files_with_legacy_reference_markers":references[:100],
            "files_with_legacy_reference_markers_count":len(references),
            "omissions":omissions[:100],"omission_count":len(omissions)}

def run():
    ap=argparse.ArgumentParser()
    ap.add_argument("--expect-head",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    assert git("rev-parse","HEAD")==args.expect_head,"HEAD_SHA_CHANGED"
    git("merge-base","--is-ancestor",ARCHIVE,"HEAD") # pinned immutable ancestor, not HEAD^
    old,head=tree(ARCHIVE),tree("HEAD")
    removed=set(old)-set(head)
    added=set(head)-set(old)
    modified={p for p in set(old)&set(head) if old[p]!=head[p]}
    expected={p for p in old if p.split("/")[0] in ROOTS or p in FILES}
    assert removed==expected,"REMOVAL_SCOPE_CHANGED"
    assert len(removed)==233,"REMOVAL_COUNT_CHANGED"
    assert added==ADDED,"ADDED_SCOPE_CHANGED:"+str(added^ADDED)
    assert modified==MODIFIED,"MODIFIED_SCOPE_CHANGED:"+str(modified^MODIFIED)
    assert all(sum(p.startswith(root+"/") for p in removed)==count for root,count in ROOTS.items()),"ROOT_COUNTS_CHANGED"
    for root in PROTECTED:
        assert git("rev-parse",ARCHIVE+":"+root)==git("rev-parse","HEAD:"+root),"PROTECTED_CHANGED:"+root
    original_ci=[p for p in old if p.startswith(".github/workflows/")]
    assert all(head.get(p)==old[p] for p in original_ci),"ORIGINAL_CI_CHANGED"
    assert old["research_domains.md"]!=head["research_domains.md"],"LEGACY_POINTER_NOT_REPLACED"
    scan=source_scan(old,head)
    report={"schema":"r7-root-legacy-readonly-gate-v1",
      "head":args.expect_head,"archive_anchor":ARCHIVE,
      "archive_equal_removed_blobs":len(removed),
      "source_files":len(old),"candidate_files":len(head),
      "deleted":len(removed),"modified":len(modified),"added":len(added),
      "prior_ci_unchanged":len(original_ci),"protected_tree_roots_unchanged":len(PROTECTED),
      "scan":scan}
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("R7_ROOT_GIT_SCOPE=PASS ARCHIVED_233/233 original research_domains preserved separately")
    print("R7_SCANNED_TEXT="+str(scan["scanned_text"])+" LINKS="+str(scan["links_checked"]))
    print("R7_NEWLY_BROKEN="+str(len(scan["newly_broken"]))+" AST_IMPORTS="+str(len(scan["legacy_imports"])))
    print("R7_DYNAMIC_CALLS="+str(scan["nonliteral_or_dynamic_calls_count"])+" OMISSIONS="+str(scan["omission_count"]))
    if scan["newly_broken"] or scan["legacy_imports"] or scan["omission_count"]:
        print("R7_ROOT_GATE=BLOCKED",file=sys.stderr)
        return 2
    print("R7_ROOT_GATE=PASS_SCOPED_NOT_FULL_REPLAY")
    return 0

if __name__=="__main__":
    sys.exit(run())
