"""summary.py - one-screen facts about the current build, from manifest.json and preview/report.json"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
rep = json.load(open(os.path.join(HERE, "preview", "report.json"), encoding="utf-8"))
loops = [k for k, v in man.items() if v["loop"]]
print(f"{len(man)} files, {sum(v['bytes'] for v in man.values()) / 1e6:.2f} MB, {len(loops)} loops")
print("max true peak over all files:", max(v["true_peak"] for v in man.values()), "dBTP")
print("max loop-join hf ratio:", max(rep[k]["join_hf_ratio"] for k in loops), "| min:", min(rep[k]["join_hf_ratio"] for k in loops))
for fam in ("amb", "music"):
    ls = [v["lufs"] for k, v in man.items() if k.startswith(fam + ".")]
    print(f"{fam}: LUFS {min(ls):.1f} .. {max(ls):.1f}  ({len(ls)} files)")
print("flags:", {k: v["flags"] for k, v in rep.items() if v["flags"]})
for fam in ("sfx", "amb", "music"):
    b = sum(v["bytes"] for k, v in man.items() if k.startswith(fam + "."))
    print(f"{fam}: {sum(1 for k in man if k.startswith(fam + '.'))} files {b / 1e6:.2f} MB")
