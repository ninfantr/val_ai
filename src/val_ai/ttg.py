import argparse
import pandas as pd
import numpy as np
import os,sys
import time

from val_ai.ops.df_utils import *
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

def elaborate(input_file, sheet_name="Sheet1", output_dir="output",output_file =None, support_enum=False):
    output_file = generate_out_filename(input_file,tag="elab",output_dir=output_dir,output_file=output_file,extension="csv")
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    edit_df = df.copy()
    #populate dont care variables
    edit_df = fillX(edit_df,support_enum=support_enum)
    if output_file:
        edit_df.to_csv(output_file,index=False)
        print(f"elaborate - {output_file} written succesfully")
    return edit_df

def analysis_elab(input_file,sheet_name="Sheet1", model="decision_tree", output_dir="output", output_file=None, col=None, subset=None,do_predict_misses=False,support_enum=False,do_elab=True):
    if do_elab:
        elab_df = elaborate(input_file,sheet_name=sheet_name,output_dir=output_dir, support_enum=support_enum)
    else:
            elab_df = pd.read_excel(input_file, sheet_name=sheet_name)
    output_file = generate_out_filename(input_file,tag="analysis",output_dir=output_dir,output_file=output_file)

    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    #elab_df.to_excel(writer,sheet_name="elab",index=False)

    #df sort
    df = elab_df.copy()
    if subset is None:
        #consider only last column as output
        features = list(elab_df.columns)[:-1]
    else:
        features = subset
    print(features)
    if col is None:
        target = list(elab_df.columns)[-1]
    else:
        target = col

    #check:
    for feature in features:
        if "X" in df[feature].values :
            raise Exception(f"analysis_elab...FAILED. {feature} contains X. Please run -elaborate stage first")

    #assign logic_val
    if support_enum:
        #TODO
        def find_logic_val(row) :
            return int(''.join(row.values.astype(str)),2)
    else:
        def find_logic_val(row) :
            return int(''.join(row.values.astype(str)),2)
    
    df['_logic_index'] = df[features].apply(lambda row: find_logic_val(row) , axis=1)
    #df['combined'] = df[cols].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
    df = df.sort_values(by=['_logic_index'])

    print("analysis_elab - finding DUPLICATES")
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
    print(elab_no_dup_df)
    elab_no_dup_df = elab_no_dup_df.drop(['_logic_dup','_logic_index'],axis=1)     
    elab_no_dup_df.to_excel(writer,sheet_name="elab_no_duplicates",index=False)

    #MISSES
    df["_logic_miss"] = 0
    for i in range(2**len(features)):
        if i not in df['_logic_index'].values:
            new_row = {"_logic_miss": True, '_logic_index': i}
            lf = len(features)
            for feature,val in zip(features,format(i,f'0{lf}b')):
                new_row[feature] = val
            print("analysis_elab - found MISSES", i, new_row)
            df = df.append(new_row, ignore_index=True)
    df = df.sort_values(by=['_logic_index'])
    print(df.head(10))

    #dup
    df["_logic_miss"].fillna(0,inplace=True)
    df["_logic_dup"].fillna(0,inplace=True)

    dup_df =df.copy()
    #dup_df = dup_df.fillna(0)
    dup_df = df[df['_logic_dup']==1]
    print(dup_df.head(10))
    dup_df = dup_df.drop(['_logic_dup','_logic_index',"_logic_miss"],axis=1)     
    dup_df.to_excel(writer,sheet_name="duplicates",index=False)

    miss_df =df.copy()
    #miss_df = miss_df.fillna(0)
    miss_df = df[df['_logic_miss']==1]
    print(miss_df.head(10))
    miss_df = miss_df.drop(['_logic_dup','_logic_index',"_logic_miss"],axis=1)     
    miss_df.to_excel(writer,sheet_name="miss",index=False)
    writer.save()
    print(f"analysis - {output_file} written succesfully")
    
    if do_predict_misses:
        #TRAIN
        out_predict_file = generate_out_filename(input_file,tag="predict_on_miss",output_dir=output_dir, extension="csv")
        model_path = predict_misses(output_file, sheet_name="elab_no_duplicates", model=model, output_file=out_predict_file,subset=subset,train_only=True)
        #MODEL EXPLAIN
        ml_model_explain(model_path,output_dir)
        #PREDICTION
        predict_misses(output_file, sheet_name="miss", output_file=out_predict_file,predict_col=target, subset=subset, load_model = model_path, predict_only=True)
        out_predict_file = generate_out_filename(input_file,tag="predict_all",output_dir=output_dir, extension="csv")    
        predict_misses(None,output_file=out_predict_file,subset=features,predict_col=target, load_model = model_path, predict_only=True)
    
def predict_misses(input_file, sheet_name="Sheet1", output_dir="output", output_file=None, output_sheet_name="Sheet1", subset=None, predict_col=None,load_model="",model="decision_tree",train_only=False, predict_only=False, train_ratio=None):
    if input_file is None:
        subset_sorted = sorted(subset)
        df = generate_all_combination(subset_sorted)
        df = df[subset]
    else:
        df = pd.read_excel(input_file, sheet_name=sheet_name)
    if subset is None:
        Features = list(df.columns)[:-1]
    else:
        Features = subset
    if predict_col is None:
        TargetColumn = list(df.columns)[-1]
    else:
        TargetColumn =  predict_col
    
    print(f"FEATURES = {Features}, TARGET = {TargetColumn}")

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
        print("predict_misses - Training ....")
        X, Y = prepare_dataset(train_df,Features = Features, col=TargetColumn)
        if train_ratio is not None:
            X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.3, random_state=100)
        else:
            X_train = X
            Y_train = Y
            X_test = X
            Y_test = Y
        #model_path = generate_out_filename(input_file,tag=f"{model}_{TargetColumn}",output_dir=output_dir, extension="pkl",prefix="model")
        model_path= os.path.join(output_dir,f"model_{model}_column_{TargetColumn}.pkl")
        trained_model = train(X_train,Y_train,feature_names =Features , target_names = Targets, model_path=model_path,model_name=model)
        test(trained_model, X_train, Y_train, X_test, Y_test, X, Y)
        if train_only:
            print(f"predict_misses - {model_path} written succesfully")
            return model_path
    
    if process_predict:
        df[TargetColumn] = ""
        output_file = generate_out_filename(input_file, output_dir=output_dir,output_file=output_file, extension="csv")
        predict(load_model, df,output_file, features= Features, col=TargetColumn)
