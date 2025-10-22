#!/usr/intel/bin/python3.6.3a
import os, sys, platform
import argparse, time

# PLATFORM CHECKS
if platform.platform().startswith("Linux"):
    print(f"Running in {platform.platform()}")
    print(f"Configuring for EC_Linux")
    import UsrIntel.R1    
elif platform.platform().startswith("Windows"):
    print(f"Running in {platform.platform()}")
else:
    raise Exception(f"[ERROR] : tool is not supported in {platform.platform()}")

current_dir = os.path.dirname(__file__)
pkg_dir = os.path.join(current_dir,"..")
#print(f"importing {pkg_dir}")
sys.path.append(pkg_dir)

from val_ai import ttg

DEBUG_FILE = "debug_ttg.log"

if __name__ =="__main__":
    parser = argparse.ArgumentParser(prog='TTG Template generation')
    parser.add_argument('-n', help='Generate template for n dimension. Default: 5',type=int,default=5)
    parser.add_argument('-o', '--output', help='output directory',default="output")

    args = parser.parse_args()

    if args.template:
        col_names = [f"COL_{x}" for x in range(args.n)]
        ttg.generate_all_combination(col_names,output_file=f"{args.output}/template.csv",extra_cols=["OUT"])
        exit(0)

    exit(0)

