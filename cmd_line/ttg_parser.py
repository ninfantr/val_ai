#!/usr/intel/bin/python3.6.3a
import os, sys, platform
import time
import argparse, traceback

# PLATFORM CHECKS
if platform.platform().startswith("Linux"):
    # print(f"Running in {platform.platform()}...")
    # print(f"Configuring for EC_Linux ...")
    import UsrIntel.R1    
elif platform.platform().startswith("Windows"):
    #print(f"Running in {platform.platform()} ...")
    pass
else:
    raise Exception(f"[ERROR] : tool is not supported in {platform.platform()}")

current_dir = os.path.dirname(__file__)
pkg_dir = os.path.join(current_dir,"..")
#print(f"importing {pkg_dir}")
sys.path.append(pkg_dir)

import warnings
warnings.filterwarnings('ignore')

class StageSkip(Exception):
    pass

#CMDLINE PARSER

available_models = ["decision_tree","neural_network","random_forest"]
parser = argparse.ArgumentParser(prog='TTG_PARSER', description='Process logic truth table and extracts insightful information from it using AI/ML', epilog="Let's get started")
parser.add_argument('-i', '--input', help='input filepath (supports xlsx, xls, csv)')
parser.add_argument('-s', '--sheet', help='input sheetname in case of xlsx/xls. Default: Sheet1',default="Sheet1")
parser.add_argument('-o', '--output', help='output directory. Default: output',default="output")
#stages
parser.add_argument('-model', help='select ML/DL model. Default: decision_tree . Available Options: '+ ",".join(available_models) , choices=available_models, default="decision_tree")
parser.add_argument('-elaborate', help='Perform only elab to expand the dont care condition. Default: False (analysis stage does elab explicitly)',action='store_true',default=False)
#parser.add_argument('-analysis',  help='Perform complete analysis of Truth Table. Default: True',action='store_true',default=True)
parser.add_argument('-sort_row',    help='Sorted output along rows. Easy for comparsion. Default: True',action='store_true',default=False)
parser.add_argument('-sort_col',    help='Sorted output along columns Easy for comparsion. Default: True',action='store_true',default=False)
#parser.add_argument('-template', help='Generate template of n dimension',type=int,default=0)

args = parser.parse_args()

if os.path.exists(args.output) :
    base_output_name = args.output
    output_dir = base_output_name
    i = 1
    while True:
        if os.path.exists(output_dir):
            #print(f"searching.......{i}")
            output_dir = f"{base_output_name}_{i}"
            i +=1
        else:
            break
    args.output = output_dir

os.makedirs(args.output,exist_ok=False)    
os.environ["TTG_DEBUG_FILE"] = os.path.join(args.output,"debug_ttg.log")

args.sort = ( args.sort_x , args.sort_y )
args.analysis = True

#FROM IMPORT
from val_ai import ttg

_tool_name_ = "TTG"

if __name__ == "__main__":
    error_msg = ""
    profile = ttg.TaskProfiler(_tool_name_)        
    # MAIN PROCESS
    try:
        ttg.txt_banner(f" EXECUTION RUN {time.strftime('%Y-%m-%d %H:%M:%S')} ",symbol="=")
        ttg.logger.info(f"Running in {platform.platform()}...")
        ttg.logger.info("ttg module imported\n")
        ttg.logger.info(f"Resolved Arguments: {args}")
        
        # if args.template:
        #     col_names = [f"COL_{x}" for x in range(args.template)]
        #     ttg.generate_all_combination(col_names,output_file=f"{args.output}/template.xlsx",extra_cols=["OUT"])
        #     exit(0)

        if args.input is None:
            raise Exception(f"Please provide input xlsx path using -i or --input option.")

        if args.elaborate:
            # ttg.log_restore()
            ttg.elaborate(args.input,sheet_name=args.sheet,output_dir=args.output,sort=args.sort)
            raise StageSkip(f"[STATUS]: Elaboration COMPLETED")

        if args.analysis:
            ttg.analysis_elab(args.input,sheet_name=args.sheet,output_dir=args.output,do_predict_misses=True,do_elab=True,model = args.model,sort=args.sort)
        
        ttg.logger.info(f"[DONE] : {args.output}/ is generated")
        ttg.logger.info(f"COMPLETED")
    
    except StageSkip as t:
        ttg.log_restore()
        print(t)
        pass
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        error_msg = e

    ttg.log_restore()
    print(f"[STATUS]: Executed in {profile.get_exec_time()} sec")

    if error_msg:
        print(f"[ERROR] : Something went wrong. Please check {ttg.DEBUG_FILE}")    
        exit(15)
    else:
        print(f"[DONE] : {args.output}/ is generated")
        print(f"COMPLETED")
        exit(0)
