import argparse
import pandas as pd
import numpy as np
import os
import time

#visualization,metrics
from sklearn.tree import export_graphviz  
import pickle
import graphviz
from sklearn import tree

from val_ai.ops.log_utils import *

def ml_model_explain(model_path,output_dir,convert_pdf=False):
    txt_banner("ML_MODEL EXPLAINABILTY")
    logger.info(f"opening {model_path}")
    model = pickle.load(open(model_path, 'rb'))
    model_name = model.model_name
    if model_name == "decision_tree":
        logger.info(f"model = {vars(model)}")
        output_file=f"{output_dir}/{model_name}.jpg"
        dot_data = tree.export_graphviz(model,
                        out_file = output_file,
                        feature_names=model.feature_names,  
                        class_names=model.classes_,  
                        filled=True, rounded=True,  
                        special_characters=True)
        graph = graphviz.Source(dot_data)
        # graph.format = "png"
        # graph.render(output_file)
        logger.info(f"rendered {output_file}")
        if convert_pdf:
            image_file = output_file
            pdf_file = output_file.replace(".jpg",".pdf")
            os.system(f"convert {image_file} -auto-orient {pdf_file}")
            logger.info(f"convert {pdf_file}")
        
    elif model_name == "neural_network":
        #TODO: generate image for neural network
        pass
    elif model_name =="random_forest":
        #TODO: generate image for random forest
        pass
        





if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description='Display model analysis')
    arg_parser.add_argument("-m", "--model", dest='model', type=str, nargs="?", help=f'input model path',required=True)
    arg_parser.add_argument("-o", "--output", dest='output', type=str, nargs="?", help=f'output jpg format',required=True)
    args = arg_parser.parse_args()
    
    model = pickle.load(open(args.model, 'rb')) # cant save features
    # Features = ["UC","PCC","S","AR","Health1","Health0","EMCA","IERR","MCERR","MSMI","LTERR","RMCA","RMSMI","CMCI","CSMI","CMCI_EN"]
    # model.feature_names = Features
    print(model)
    print(vars(model))

    dot_data = tree.export_graphviz(model, out_file=output_file, 
                     feature_names=model.feature_names,  
                     class_names=model.classes_,  
                     filled=True, rounded=True,  
                     special_characters=True)
    
    #print(dot_data.nodes)

    #os.system("convert *.jpg -auto-orient document.pdf")
 
    graph = graphviz.Source(dot_data) 
    # graph.render("MCA classification")