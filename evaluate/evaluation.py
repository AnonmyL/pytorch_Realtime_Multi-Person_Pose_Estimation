import sys, os

sys.path.append(os.path.abspath("./"))
import argparse
from lib.config import update_config, cfg

import torch
from evaluate import bean_eval, coco_eval
from collections import OrderedDict
from lib.network.rtpose_vgg import get_model, use_vgg
from lib.network.openpose import OpenPose_Model, use_vgg
from torch import load


NOW_WHAT = 'bean'

parser = argparse.ArgumentParser()

# parser.add_argument('--weight', type=str,
#                     default='../ckpts/openpose.pth')
parser.add_argument('opts',
                    help="Modify config options using the command-line",
                    default=None,
                    nargs=argparse.REMAINDER)


if NOW_WHAT == 'coco':
    weight_path = 'network/weight/4.11/best_openpose.pth'
    image_dir = 'data/coco/images/val2017'
    anno_file = 'data/coco/annotations/person_keypoints_val2017.json'
    vis_dir = 'data/coco/images/vis_val2017'
    parser.add_argument('--cfg', help='experiment configure file name',
                        default='./experiments/vgg19_368x368_sgd.yaml', type=str)

elif NOW_WHAT == 'bean':
    weight_path = 'network/weight/4.15/best_bean.pth'
    image_dir = 'data/bean/val'
    anno_file = None
    vis_dir = 'data/bean/output'
    parser.add_argument('--cfg', help='experiment configure file name',
                        default='./experiments/vgg19_368x368_sgd_bean.yaml', type=str)


args = parser.parse_args()
# update config file
update_config(cfg, args)

# Notice, if you using the
with torch.autograd.no_grad():
    # this path is with respect to the root of the project
    # weight_name = '/data/rtpose/rtpose_lr001/1/_ckpt_epoch_82.ckpt'
    # state_dict = torch.load(weight_name)['state_dict']

    # new_state_dict = OrderedDict()
    # for k,v in state_dict.items():
    #     name = k[6:]
    #     new_state_dict[name]=v

    model = get_model(trunk='vgg19', dataset=NOW_WHAT)
    # model = openpose = OpenPose_Model(l2_stages=4, l1_stages=2, paf_out_channels=38, heat_out_channels=19)
    # model = torch.nn.DataParallel(model).cuda()
    wts_dict = torch.load(weight_path)
    wts_dict_corrected = {k.replace('module.', ''): v for k, v in wts_dict.items()}
    model.load_state_dict(wts_dict_corrected)
    # model.load_state_dict(new_state_dict)
    model.eval()
    model.float()
    model = model.cuda()

    # The choice of image preprocessing include: 'rtpose', 'inception', 'vgg19' and 'ssd'.
    # If you use the converted model from caffe, it is 'rtpose' preprocess, the model trained in
    # this repo used 'vgg19' preprocess
    if NOW_WHAT == 'coco':
        avg_precision = coco_eval.run_eval(image_dir=image_dir, anno_file=anno_file, vis_dir=vis_dir, model=model, preprocess='vgg19')
        print("Average precision:", avg_precision)
    elif NOW_WHAT == 'bean':
        bean_eval.run_eval(image_dir=image_dir, model=model, vis_dir=vis_dir, preprocess='vgg19')