# OAG-taxo

### Introduction

OAG-taxo 's now project aims to realize the impletion of taxo-expan and taxo-enrich and other easy models. Also, we will infer the model on the dataset of Artificial Intelligence

This work is mainly based on the work of Taxoenrich. We choose it because the work itself has many models and trainers we want to use.

We are still in work...

### Data Preparation

If you want to try the dataset of Mag-CS, Mag-full and our own dataset on these model, we have prepared the dataset [here](https://drive.google.com/drive/folders/1Yl5pQKCGytJPgxghs-M4kVzf7bJV200c?usp=sharing)

If you want to try other dataset, you can accpet the methods mentioned in Taxoenrich. In short, you need to prepare the x.terms file, x.taxo file. Next, run the embedding_generation.py and generate_dataset_binary.py, then you can get the x.bin file for training

### Enviroment

You need to prepare an enviroment of cuda10 + dgl0.4.0 . It can be only used on the Graphics Card with model below 30

I want to change the code really for newer dgl version. However, not enough time for me to do

### Train the model

try: `python train.py --config config-file`， in which config-file has been prepared in config_files folder. Run the enrich model with config.test.enrich.json. Run the config.test.baseline.json for Billiear Model. Run the config.test.baselineex.json for Expan Model.

### Infer the model

We provide two infer method for the Artificial Intelligence dataset.

The Inner Infer means we choose the dataset itself to generate the exsiting graph and test node. Try: `python inner_infer.py --resume path_to_pth --config config_files`. path to pth means the path to your trained model.pth, config_files means your corresponding config files. We have prepared the config.files of three model for you.

The Outer Infer measn we choose the Mag_CS as the exsiting graph and all nodes of Artificial Intelligence node for test. Use the outer_infer.py and the same method.
