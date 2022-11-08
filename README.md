# OAG-taxo

### Introduction

This project aims to implement several methods for taxonomy expansion. We provide three methods: Bilinear, TaxoExpan, and TaxoEnrich.
Also, we provide inference on AI taxonomy via pre-trained models on Computer Science taxonomy.

This work is mainly based on the work of [TaxoEnrich](https://github.com/minhaoJ2/TaxoEnrich). We choose it because it has many available models and trainers.

### Data Preparation

If you want to try the dataset of Mag-CS, Mag-full, and our own dataset on these models, we have prepared the dataset [here](https://drive.google.com/drive/folders/1Yl5pQKCGytJPgxghs-M4kVzf7bJV200c?usp=sharing)

If you want to try other datasets, you can follow the methods mentioned in Taxoenrich. In short, you need to prepare the x.terms file, x.taxo file. Next, run the embedding_generation.py and generate_dataset_binary.py, then you can get the x.bin file for training.

For example,

```bash
python data_creation/embedding_generation.py --dataset oag-ai
python data_creation/generate_dataset_binary.py -d data/OAG_AI -t "Artificial Intelligence" -p 0
```

### Environment

You need to prepare an environment of cuda10 + dgl0.4.0. It can be only used on the Graphics Card below 30.

### Train the model

try: `python train.py --config config-file`， in which config-file has been prepared in config_files folder. Run the enrich model with config.test.enrich.json. Run the config.test.baseline.json for Billiear Model. Run the config.test.baselineextmn.json for TaxoExpan Model. For example,

```bash
python train.py -c config_files/MAG-CS/config.test.enrich.json
```

### Infer the model

We provide inference methods for the Artificial Intelligence dataset from pre-trained models on Computer Science taxonomy.

```bash
python inner_infer.py --resume your_model_path_here --config config_files/MAG-CS/config.test.enrich.json
```

We provide our pre-trained models for you [here](https://drive.google.com/drive/folders/18JacRQeLDAzYA8fA3jSmUlU9tbBA5Mhp?usp=sharing)

### Config File Prepared
For example, in ./config_file/mag_cs, we introduce each file's usage:

config.test.enrich.json: TaxoEnrich method on completion task
config.test.baseline.json: baseline Bilinear method on completion task
config.test.baselineex.json: TaxoExpan method on expansion task
config.test.baselineextmn.json: TaxoExpan method on completion task

config.valid.X.json means the corresponding infer config file for the X method and config.test.X.json

If you do not have enough GPU memory for training, decrease the batch size and the number of negative samples.

### Report PDF
Share my report [here](https://drive.google.com/file/d/10lrXlKZ5pPvr40ea7XEm5_G4bU2qShOp/view?usp=sharing). 
