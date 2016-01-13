#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# ELEKTRONN - Neural Network Toolkit
#
# Copyright (c) 2014 - now
# Max-Planck-Institute for Medical Research, Heidelberg, Germany
# Authors: Marius Killinger, Gregor Urban
"""
TrainCNN.py [config=</path/to_config_file>] [ gpu={Auto|False|<int>}]
"""

import sys, os, inspect
from subprocess import check_call, CalledProcessError
import matplotlib
orig_cwd = os.getcwd()
# prevent setting of mpl qt-backend on machines without X-server before other modules import mpl
with open(
        os.devnull,
        'w') as devnull:  #  Redirect to /dev/null because xset output is unimportant
    try:
        # "xset q" will always succeed to run if an X server is currently running
        check_call(['xset', 'q'], stdout=devnull, stderr=devnull)
        print('X available')
        # Don't set backend explicitly, use system default...
    except (OSError, CalledProcessError
            ):  # if "xset q" fails, conclude that X is not running
        print('X unavailable')
        matplotlib.use('AGG')

from elektronn.training.config import default_config, Config  # the global user-set config
from elektronn.training import trainutils  # contains import of mpl

config_file = "./Profiling_conf.py"
gpu = default_config.device
this_file = os.path.abspath(inspect.getframeinfo(inspect.currentframe(
)).filename)
# commandline arguments override config_file and gpu if given as argv
config_file, gpu = trainutils.parseargs(sys.argv, config_file, gpu)
# copies config, inits gpu (theano import)

config = Config(config_file, gpu, this_file, use_existing_dir=True)


class Data(object):
    pass


from elektronn.training import trainer  # contains import of theano
os.chdir(config.save_path)  # The trainer works directly in the save dir

### Main Part ################################################################################################
if __name__ == "__main__":
    import traceback
    import numpy as np
    import time

    config.batch_size = None

    def find_z(x):
        z = int(x / 8.5)
        z_ = z
        for valid_z in config.dimensions.valid_inputs[0][::1]:
            if valid_z > z:
                z_ = valid_z
                break

        if z_ == z:
            z_ = config.dimensions.valid_inputs[0][0]

        return z_

    T = trainer.Trainer(config)
    T.data = Data()
    T.data.n_lab = 3
    T.data.n_ch = 1
    T.createNet()
    os.chdir(orig_cwd)
    with file('Speed_%s.csv' % (config.save_name), 'a') as f:
        f.write("z-shape\txy-shape\tpixel\tSpeed [MPix/s]\n")

    for x in config.dimensions.valid_inputs[1][4:50]:
        z = find_z(x)
        for z_mod in [-16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24]:
            in_sh = list(T.cnn.input_shape)
            in_sh[0] = 1
            in_sh[1] = z + z_mod
            in_sh[3] = x
            in_sh[4] = x
            print in_sh
            try:
                val = np.random.rand(*in_sh).astype(np.float32)
                t0 = time.time()
                y = T.cnn.class_probabilities(val)
                t1 = time.time()
                n = np.prod(y.shape[2:])
                speed = float(n) / (t1 - t0) / 1e6
                # z, x, static, speed
                s = '%i\t%i\t%i\t%f\n' % (z + z_mod, x, n, speed)

                with file('Speed_%s.csv' % (config.save_name), 'a') as f:
                    f.write(s)
            except:
                traceback.print_exc(file=sys.stdout)
