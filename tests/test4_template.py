#!/usr/intel/bin/python3.6.3a
import os, sys, platform
import time
import argparse, traceback

# PLATFORM CHECKS
if platform.platform().startswith("Linux"):
    print(f"Running in {platform.platform()}...")
    print(f"Configuring for EC_Linux ...")
    import UsrIntel.R1    
elif platform.platform().startswith("Windows"):
    print(f"Running in {platform.platform()} ...")
else:
    raise Exception(f"[ERROR] : tool is not supported in {platform.platform()}")

# Required for local testing
sys.path.append("../")


from val_ai import ttg
from val_ai.ops.df_utils import *

generate_all_combination(["A","B","C"], {"A":["ON","OFF"], "B" : ["IDLE","ACTIVE"]},output_file="output/template.xlsx")