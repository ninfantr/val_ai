import argparse
import pandas as pd
import numpy as np
import os,sys
import time


from val_ai.ops.df_utils import *
from val_ai.ops.log_utils import *
from val_ai.models.classifier import *
from val_ai.models.explainability import *


###### SANITY CHECKS #################
def module_check():
    print("PASSED")
######################################

def generate_out_filename(input_file,  output_dir="out",output_file=None, tag=None, extension=None,prefix=None):
    if tag is None:
        tag=time.time()
    if output_file:
        output_file = output_file
    else:
        filename,ext = os.path.splitext(input_file)
        filename = os.path.basename(filename)
        os.makedirs(output_dir,exist_ok=True)
        output_filename = f"{filename}_{tag}{ext}"
        output_file = os.path.join(output_dir,output_filename)
    if extension:
        output_filename ,origin_ext  = os.path.splitext(output_file)
        if extension.startswith("."):
            extension = extension[1:]
        output_file = output_filename + "."+ extension
    if prefix:
        output_dir = os.path.dirname(output_file)
        filename = os.path.basename(output_filename)
        ext = os.path.splitext(output_file)[1]
        output_file = os.path.join(output_dir, f"{prefix}_{filename}{ext}")
        
    return output_file

def elaborate(input_file, sheet_name="Sheet1", output_dir="output",output_file =None, support_enum=False,sort=False):
    txt_banner("ELABORATE")
    output_file = generate_out_filename(input_file,tag="elab",output_dir=output_dir,output_file=output_file,extension="csv")
    df = read_df(input_file, sheet_name=sheet_name)
    edit_df = df.copy()
    #populate dont care variables
    edit_df = fillX(edit_df,support_enum=support_enum)
    if output_file:
        dump_df(edit_df,filename=output_file,sort=sort)
        logger.info(f"{output_file} written succesfully")  
    return edit_df

def analysis_elab(input_file,sheet_name="Sheet1", model="decision_tree", output_dir="output", output_file=None, col=None, subset=None,do_predict_misses=False,support_enum=False,do_elab=True,sort=False):
    txt_banner("ANALYSIS")
    if do_elab:
        logger.info(f"Running Elaborate on {input_file}")
        elab_df = elaborate(input_file,sheet_name=sheet_name,output_dir=output_dir, support_enum=support_enum,sort=sort)
    else:
        logger.info(f"loading {input_file}")
        elab_df = read_df(input_file, sheet_name=sheet_name)
    output_file = generate_out_filename(input_file,tag="analysis",output_dir=output_dir,output_file=output_file)

    #writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    #elab_df.to_excel(writer,sheet_name="elab",index=False)

    #df sort
    df = elab_df.copy()
    features = identify_feature_columns(df,subset=subset)
    target = identify_target_column(df,target=col)    

    #check:
    for feature in features:
        if "X" in df[feature].values :
            raise Exception(f"analysis_elab...FAILED. {feature} contains X. Please run -elaborate stage first")
    
    calculate_logic_index(df)
    df = df.sort_values(by=['_logic_index'])

    logger.info("Finding DUPLICATES...")
    #DUPLICATES
    #df['_logic_dup'] = df.duplicated(subset=features, keep=False )
    #df['_logic_dup'] = df.duplicated(keep=False)
    df = df.drop_duplicates() # drop duplicate with same targets
    df['_logic_dup'] = df.duplicated(subset=features, keep=False ) # identify duplicates with different targets
    
    # df[features].apply(lambda x : print(x))
    #print(df.head(10))
    
    elab_no_dup_df =df.copy()
    df["_logic_dup"].fillna(0,inplace=True)
    #elab_no_dup_df = elab_no_dup_df.fillna(0)
    elab_no_dup_df = df[df['_logic_dup']!=1]
    #logger.debug(f"Dataframe elab_no_duplicates = \n {elab_no_dup_df.head(5)}")
    elab_no_dup_df = elab_no_dup_df.drop(['_logic_dup','_logic_index'],axis=1)     
    #elab_no_dup_df.to_excel(writer,sheet_name="elab_no_duplicates",index=False)
    file_elab_no_dup = generate_out_filename(input_file,tag="elab_no_duplicates",output_dir=output_dir,extension="csv")
    dump_df(elab_no_dup_df,file_elab_no_dup,sheet_name="elab_no_duplicates")


    #MISSES
    df["_logic_miss"] = 0
    for i in range(2**len(features)):
        if i not in df['_logic_index'].values:
            new_row = {"_logic_miss": True, '_logic_index': i}
            lf = len(features)
            for feature,val in zip(features,format(i,f'0{lf}b')):
                new_row[feature] = val
                logger.debug(f"Found MISSES  {i} {new_row}")
            df = df.append(new_row, ignore_index=True)
    df = df.sort_values(by=['_logic_index'])

    #dup
    df["_logic_miss"].fillna(0,inplace=True)
    df["_logic_dup"].fillna(0,inplace=True)

    dup_df =df.copy()
    #dup_df = dup_df.fillna(0)
    dup_df = df[df['_logic_dup']==1]
    #logger.debug(f"Dataframe duplicates = \n {dup_df.head(5)}")
    dup_df = dup_df.drop(['_logic_dup','_logic_index',"_logic_miss"],axis=1)     
    #dup_df.to_excel(writer,sheet_name="duplicates",index=False)
    file_dup = generate_out_filename(input_file,tag="duplicates",output_dir=output_dir,extension="csv")
    dump_df(dup_df,file_dup,sheet_name="duplicates")

    miss_df =df.copy()
    #miss_df = miss_df.fillna(0)
    miss_df = df[df['_logic_miss']==1]
    #logger.debug(f"Dataframe miss_df = \n {miss_df.head(5)}")
    miss_df = miss_df.drop(['_logic_dup','_logic_index',"_logic_miss"],axis=1)     
    #miss_df.to_excel(writer,sheet_name="miss",index=False)
    file_miss = generate_out_filename(input_file,tag="misses",output_dir=output_dir,extension="csv")
    dump_df(miss_df,file_miss,sheet_name="miss")
    # if writer:
    #     writer.close()
    
    if do_predict_misses:
        #TRAIN
        txt_banner(f"TRAINING {model} MODEL")
        model_path = predict_misses(file_elab_no_dup, output_dir=output_dir,sheet_name="elab_no_duplicates", model=model,subset=subset,train_only=True)
        #MODEL EXPLAIN
        ml_model_explain(model_path,output_dir)
        #PREDICT DUPLICATE
        txt_banner("PREDICTING DUPLICATES")
        file_predict_dup = generate_out_filename(input_file,prefix="predict",tag="on_duplicates",output_dir=output_dir, extension="csv")
        predict_misses(file_dup, sheet_name="duplicates", output_dir=output_dir, output_file=file_predict_dup,predict_col=target, subset=subset, load_model = model_path, predict_only=True,sort=sort)
        #PREDICT MISS
        txt_banner("PREDICTING MISSES")
        file_predict_on_miss = generate_out_filename(input_file,prefix="predict",tag="on_miss",output_dir=output_dir, extension="csv")
        predict_misses(file_miss, sheet_name="miss", output_dir=output_dir, output_file=file_predict_on_miss,predict_col=target, subset=subset, load_model = model_path, predict_only=True,sort=sort)
        #PREDICT ALL
        txt_banner("PREDICTING ALL")
        file_predict_all = generate_out_filename(input_file,prefix="predict",tag="all",output_dir=output_dir, extension="csv")    
        predict_misses(None,output_dir=output_dir, output_file=file_predict_all,subset=features,predict_col=target, load_model = model_path, predict_only=True,sort=sort)
    
def predict_misses(input_file, sheet_name="Sheet1", output_dir="output", output_file=None, output_sheet_name="Sheet1", subset=None, predict_col=None,load_model="",model="decision_tree",train_only=False, predict_only=False, train_ratio=None, sort=False):
    if input_file is None:
        subset_sorted = sorted(subset)
        df = generate_all_combination(subset_sorted)
        df = df[subset]
    else:
        df = read_df(input_file, sheet_name=sheet_name)
    
    
    Features = identify_feature_columns(df,subset)
    TargetColumn = identify_target_column(df,target=predict_col)

    logger.debug(f"FEATURES = {Features}, TARGET = {TargetColumn}")

    #processing the stages
    process_train = True
    process_predict = False
    if load_model:
        process_train = False
        process_predict = True
        model_path = load_model
    if train_only:
        process_train = True
        process_predict = False
    elif predict_only:
        process_train = False
        process_predict = True
    
    if process_train:
        train_df = df.copy()
        Targets = train_df[TargetColumn].unique()
        train_df[TargetColumn].dropna()
        logger.info("Training ....")
        if df.shape[0] == 0:
            logger.warning(f"CANNOT TRAIN. No valid combination in {input_file}.")
            logger.warning(f"SKIPPING Model creation")
            return
        X, Y = prepare_dataset(train_df,Features = Features, col=TargetColumn)
        if train_ratio is not None:
            X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.3, random_state=100)
        else:
            X_train = X
            Y_train = Y
            X_test = X
            Y_test = Y
        #model_path = generate_out_filename(input_file,tag=f"{model}_{TargetColumn}",output_dir=output_dir, extension="pkl",prefix="model")
        model_path= os.path.join(output_dir,f"model_{model}_{TargetColumn}.pkl")
        trained_model = train(X_train,Y_train,feature_names =Features , target_names = Targets, model_path=model_path,model_name=model)
        report_file = os.path.join(output_dir,f"report_{model}_{TargetColumn}.txt")
        test(trained_model, X_train, Y_train, X_test, Y_test, X, Y, dump_file=report_file)
        if train_only:
            logger.info(f"checkpoint {model_path} created")
            return model_path
    
    if process_predict:
        df[TargetColumn] = ""
        output_file = generate_out_filename(input_file, output_dir=output_dir,output_file=output_file, extension="csv")
        if df.shape[0] == 0:
            logger.warning(f"no row entry {input_file}.")
            logger.warning(f"SKIPPING {output_file} generation. ")
            return
        predict(load_model, df,output_file, features= Features, col=TargetColumn,sort=sort)
