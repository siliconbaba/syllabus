#!/usr/bin/env python3
import argparse
from common import *
def main():
 p=argparse.ArgumentParser();p.add_argument('--pack',required=True);p.add_argument('--output',required=True);a=p.parse_args();pack=Path(a.pack);issues=[]
 for relative,h in read(pack/'artifact-hashes.json').items():
  path=pack/relative
  if not path.is_file() or sha(path)!=h:issues.append({'packHashMismatch':relative})
 for name,h in read(pack/'batch-contract.json')['sources'].items():
  if not Path(name).is_file() or sha(name)!=h:issues.append({'sourceHashMismatch':name})
 summary(a.output,issues)
 if issues:raise SystemExit(1)
if __name__=='__main__':entry(main)
