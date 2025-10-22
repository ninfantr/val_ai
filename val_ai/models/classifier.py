import pandas as pd
import numpy as np

from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.svm import SVC
# from sklearn.ensemble import VotingClassifier
# from sklearn.ensemble import AdaBoostRegressor
#ensemble method
#from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
#from sklearn.model_selection import GridSearchCV, KFold

import itertools

#visualization,metrics
from sklearn.tree import export_graphviz 
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score

import pickle

from val_ai.ops.df_utils import *
from val_ai.ops.log_utils import *

def prepare_dataset(df,Features, col ):
    #logger.info(f"Columns = {df.dtypes}")
    logger.info(f"FEATURES = {Features}")
    logger.info(f"TARGETS = {df[col].unique()}")
    Features = sorted(Features)
    X = df[Features]
    Y = df[[col]]
    return X, Y 

def train(X_train,Y_train, feature_names, target_names, model_path, model_name="decision_tree", **kwargs):
    if model_name=="decision_tree":
        model = DecisionTreeClassifier()
    elif model_name =="neural_network":
        model = MLPClassifier()
    elif model_name =="random_forest":
        model = RandomForestClassifier(random_state=0)
    else:
        raise Exception("invalid model selection")
    model.fit(X_train,Y_train)
    model.feature_names =  feature_names
    model.target_names = target_names
    model.model_name = model_name
    if model_path:
        pickle.dump(model, open(model_path, 'wb'))
    return model

def test(model, X_train, Y_train, X_test, Y_test, X, Y,dump_file=None):
    Targets = list(model.classes_)
    doc_lines = []
    doc_lines.append("\n")
    doc_lines.append(txt_banner("TESTING REPORT",display=False))
    doc_lines.append(f"TRAINING SCORE = {model.score(X_train,Y_train)}")
    doc_lines.append(f"TESTING SCORE =  {model.score(X_test,Y_test)}")
    #doc_lines.append("CROSS VALIDATION (3 FOLD) = ", cross_val_score(model, X , Y,cv=2))
    Y_pred = model.predict(X_train)
    report = classification_report(Y_train, Y_pred, target_names=Targets)
    doc_lines.append("\nCLASSIFICATION REPORT ON TRAIN ")
    doc_lines.append(report)
    Y_pred = model.predict(X_test)
    report = classification_report(Y_test, Y_pred, target_names=Targets)
    doc_lines.append("\nCLASSIFICATION REPORT ON TEST ")
    doc_lines.append(report)
    Y_pred = model.predict(X)
    report = classification_report(Y, Y_pred, target_names=Targets)
    doc_lines.append("\nCLASSIFICATION REPORT ON COMPLETE DATASET")
    doc_lines.append(report)
    doc_lines.append("\n")
    
    logger.debug("\n".join(doc_lines))
    if dump_file:
        f = open(dump_file,"w")
        for line in doc_lines:
            f.write(line+"\n")
        f.close()

def derive_probabilites_map(Targets,Y_proba):
    Probabilities = []
    # map probabitlites
    for prob in Y_proba:
        tl = []
        for id,val in enumerate(Targets):
            percent = round(float(prob[id]) *100 )
            tl.append(f"{val}:{percent: < 5} %")
        proba_txt = " ".join(tl)
        Probabilities.append(proba_txt)
        # print(txt)
    return Probabilities

# def predict_all(df,out_file, cols=[],models=[]) :
#     # model = pickle.load(open(MODEL_FILENAME, 'rb'))
#     df = pd.read_excel( TESTING_XLS, sheet_name=TRAINING_SHEET)
#     df.columns = df.columns.str.strip()
#     df.columns = df.columns.str.replace("\n","")
#     # df["BIOS Logging"].fillna("NA",inplace=True)
#     df.fillna("NA",inplace=True)
#     out_df = df.copy()

#     # drop_columns = [ i  for i in list(out_df.columns) if (i not in ["STATUS"]) and (i not in Features)]
#     # out_df = out_df.drop(columns=drop_columns,inplace=False)

#     # if only_invalid:
#     #     index_names = out_df[ out_df['STATUS'].isin(ValidStatusTargets)].index 
#     #     out_df = out_df.drop(index_names, inplace = False) 

#     for m,c in zip(models,cols):
#         X_test = out_df[Features]
#         model = pickle.load(open(m, 'rb'))
#         Y_pred = model.predict(X_test)
#         # Y_proba = model.predict_proba(X_test)
#         Targets = sorted(list(model.classes_))
#         print(Targets)
#         # Probabilities = derive_probabilites_map(Targets,Y_proba)
#         out_df.loc[:,f"Pred_{c}"] = Y_pred
    
    
#     for m,c in zip(models,cols):
#         X_test = out_df[Features]
#         model = pickle.load(open(m, 'rb'))
#         # Y_pred = model.predict(X_test)
#         Y_proba = model.predict_proba(X_test)
#         Targets = sorted(list(model.classes_))
#         print(Targets)
#         Probabilities = derive_probabilites_map( Targets,Y_proba)
#         out_df.loc[:,f"Pred_{c}_Proba"] = Probabilities
    
#     for m,c in zip(models,cols):
#         out_df[f'RESULTS_{c}'] = np.where((out_df[c] == out_df[f'Pred_{c}']), True, False)
    
#     out_df.to_excel(out_file,index=False)
#     print(f"{out_file} generated.")

def predict(model_path, df,out_file, features, col,sort=False ) :
    model = pickle.load(open(model_path, 'rb'))
    Targets= model.classes_
    out_df = df.copy()
    #print(df.head())
    features= sorted(features)
    # drop_columns = [ i  for i in list(out_df.columns) if (i not in [col]) and (i not in features)]
    # out_df = out_df.drop(columns=features,inplace=False)
    #print(out_df.columns)
    X_test = out_df[features]
    #print(f"predict -  \n{X_test.head()}")
    Y_pred = model.predict(X_test)
    Y_proba = model.predict_proba(X_test)
    
    # Y_proba_log = model.predict_log_proba(X_test)
    # print(Y_proba_log)

    Probabilities = []
    # map probabitlites
    for prob in Y_proba:
        tl = []
        for id,val in enumerate(model.classes_):
            percent = round(float(prob[id]) *100 )
            tl.append(f"{val}:{percent: < 5} %")
        proba_txt = " ".join(tl)
        Probabilities.append(proba_txt)
        # print(txt)

    out_df.loc[:,col] = Y_pred
    out_df = out_df.drop_duplicates()
    #out_df.loc[:,f"Predicted {col}"] = Y_pred
    # out_df.loc[:,f"Predicted {col} Probabilties"] = Probabilities
    # out_df['RESULTS'] = np.where((out_df[col] == out_df[f'Predicted {col}']), True, False)

    dump_df(out_df,out_file,sort=sort)