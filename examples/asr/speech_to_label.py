# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
# Task 1: Speech Command

## Preparing the dataset
Use the `process_speech_commands_data.py` script under <NEMO_ROOT>/scripts in order to prepare the dataset.

```sh
python <NEMO_ROOT>/scripts/process_speech_commands_data.py \
    --data_root=<absolute path to where the data should be stored> \
    --data_version=<either 1 or 2, indicating version of the dataset> \
    --class_split=<either "all" or "sub", indicates whether all 30/35 classes should be used, or the 10+2 split should be used> \
    --rebalance \
    --log
```

## Train to convergence
```sh
python speech_to_label.py \
    # (Optional: --config-path=<path to dir of configs> --config-name=<name of config without .yaml>) \
    model.train_ds.manifest_filepath="<path to train manifest>" \
    model.validation_ds.manifest_filepath=["<path to val manifest>","<path to test manifest>"] \
    trainer.gpus=2 \
    trainer.distributed_backend="ddp" \
    trainer.max_epochs=200 \
    exp_manager.create_wandb_logger=True \
    exp_manager.wandb_logger_kwargs.name="MatchboxNet-3x1x64-v1" \
    exp_manager.wandb_logger_kwargs.project="MatchboxNet-v1" \
    +trainer.precision=16 \
    +trainer.amp_level=O1  # needed if using PyTorch < 1.6
```


# Task 2: Voice Activity Detection

## Preparing the dataset
Use the `process_vad_data.py` script under <NEMO_ROOT>/scripts in order to prepare the dataset.

```sh
python process_vad_data.py \
    --out_dir=<output path to where the generated manifest should be stored> \
    --speech_data_root=<path where the speech data are stored> \
    --background_data_root=<path where the background data are stored> \
    --rebalance_method=<'under' or 'over' of 'fixed'> \ 
    --log
    (Optional --demo (for demonstration in tutorial). If you want to use your own background noise data, make sure to delete --demo)
```

## Train to convergence
```sh
python speech_to_label.py \
    --config-path=<path to dir of configs e.g. "conf"> 
    --config-name=<name of config without .yaml e.g. "matchboxnet_3x1x64_vad"> \
    model.train_ds.manifest_filepath="<path to train manifest>" \
    model.validation_ds.manifest_filepath=["<path to val manifest>","<path to test manifest>"] \
    trainer.gpus=2 \
    trainer.distributed_backend="ddp" \
    trainer.max_epochs=200 \
    exp_manager.create_wandb_logger=True \
    exp_manager.wandb_logger_kwargs.name="MatchboxNet-3x1x64-vad" \
    exp_manager.wandb_logger_kwargs.project="MatchboxNet-vad" \
    +trainer.precision=16 \
    +trainer.amp_level=O1  # needed if using PyTorch < 1.6
```
"""
import pytorch_lightning as pl

from nemo.collections.asr.models import EncDecClassificationModel
from nemo.core.config import hydra_runner
from nemo.utils.exp_manager import exp_manager


@hydra_runner(config_path="conf", config_name="matchboxnet_3x1x64_v1")
def main(cfg):
    trainer = pl.Trainer(**cfg.trainer)
    exp_manager(trainer, cfg.get("exp_manager", None))
    asr_model = EncDecClassificationModel(cfg=cfg.model, trainer=trainer)

    trainer.fit(asr_model)

    if hasattr(cfg.model, 'test_ds') and cfg.model.test_ds.manifest_filepath is not None:
        gpu = 1 if cfg.trainer.gpus != 0 else 0
        trainer = pl.Trainer(gpus=gpu)
        if asr_model.prepare_test(trainer):
            trainer.test(asr_model)


if __name__ == '__main__':
    main()  # noqa pylint: disable=no-value-for-parameter
