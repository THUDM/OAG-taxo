import argparse
import torch
from tqdm import tqdm
import data_loader.data_loaders as module_data
import model.model as module_arch
from parse_config import ConfigParser
from gensim.models import KeyedVectors
import numpy as np
import more_itertools as mit
from pathlib import Path
import model.metric as module_metric
from functools import partial
import trainer as trainer_arch


def rearrange(energy_scores, candidate_position_idx, true_position_idx):
    tmp = np.array([[x==y for x in candidate_position_idx] for y in true_position_idx]).any(0)
    correct = np.where(tmp)[0]
    incorrect = np.where(~tmp)[0]
    labels = torch.cat((torch.ones(len(correct)), torch.zeros(len(incorrect)))).int()
    energy_scores = torch.cat((energy_scores[correct], energy_scores[incorrect]))
    return energy_scores, labels

def main(config, args_outer):
    # Load trained model and existing taxonomy
    mode = config['mode']
    logger = config.get_logger('test')
    torch.multiprocessing.set_sharing_strategy('file_system')
    test_data_loader = config.initialize('train_data_loader', module_data, config['mode'], config['data_path'])
    logger.info(test_data_loader)
    test_dataset = test_data_loader.dataset
    node_features = test_dataset.node_features
    input_features = test_dataset.input_features

    model = config.initialize('arch', module_arch, mode)
    vocab_size, embed_dim = node_features.size()
    model.set_embedding(vocab_size=vocab_size, embed_dim=embed_dim, pretrained_embedding=node_features, input_features=input_features)
    logger.info(model)
    device = torch.device('cuda:0')

    now = model.state_dict()

    # load saved model
    logger.info('Loading checkpoint: {} ...'.format(config.resume))
    checkpoint = torch.load(config.resume)
    state_dict = checkpoint['state_dict']
    """if config['n_gpu'] > 1:
        model = torch.nn.DataParallel(model)"""
    print(state_dict.keys())
    keys = ['embedding.weight', 'bert_embedding.weight']
    for key in keys:
        state_dict[key] = now[key]
    model.load_state_dict(state_dict)
    model.set_device(device)

    model.to(device)
    metrics = [getattr(module_metric, met) for met in config['metrics']]
    if config['loss'].startswith("info_nce") or config['loss'].startswith("bce_loss"):
        print("mode is 1")
        pre_metric = partial(module_metric.obtain_ranks, mode=1)  # info_nce_loss
    else:
        print("mode is 2")
        pre_metric = partial(module_metric.obtain_ranks, mode=0)

    model.eval()
    modes = "valid"

    Trainer = config.initialize_trainer('arch', trainer_arch)
    trainer = Trainer(config['mode'], model, None, metrics, pre_metric, None,
                      config=config,
                      data_loader=test_data_loader,
                      lr_scheduler=None)

    trainer.test()




if __name__ == '__main__':
    args = argparse.ArgumentParser(description='Testing structure expansion model with case study logging')
    args.add_argument('-r', '--resume', default=None, type=str, help='path to latest model checkpoint (default: None)')
    args.add_argument('-c', '--config', default=None, type=str, help='config file path (default: None)')
    args.add_argument('-t', '--taxon', default=None, type=str, help='path to new taxon list  (default: None)')
    args.add_argument('-d', '--device', default=None, type=str, help='indices of GPUs to enable (default: all)')
    # args.add_argument('-k', '--topk', default=-1, type=int, help='topk retrieved instances for testing, -1 means no retrieval stage (default: -1)')
    args.add_argument('-m', '--topm', default=10, type=int, help='save topm ranked positions (default: 10)')
    args.add_argument('-b', '--batch_size', default=-1, type=int, help='batch size, -1 for small dataset (default: -1), 20000 for larger MAG-Full data')
    args.add_argument('-s', '--save', default="./output/prediction_results.tsv", type=str, help='save file for prediction results (default: ./output/prediction_results.tsv)')
    args_outer = args.parse_args()
    config = ConfigParser(args)
    main(config, args_outer)
