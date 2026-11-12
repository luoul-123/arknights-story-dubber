"""Run upstream GPT training on one GPU without Windows DDP networking."""
import argparse
import importlib.util
from functools import partial
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--config_file', required=True)
    args = parser.parse_args()
    import torch
    from pytorch_lightning import Trainer
    from pytorch_lightning.callbacks import Callback
    from pytorch_lightning.strategies import SingleDeviceStrategy
    from AR.data import data_module

    # Upstream defaults to distributed sampling even when only one GPU exists.
    data_module.DistributedBucketSampler = partial(
        data_module.DistributedBucketSampler, num_replicas=1, rank=0)
    original_loader = data_module.DataLoader

    def loader(*values, **kwargs):
        if kwargs.get('num_workers', 0) == 0:
            kwargs.pop('prefetch_factor', None)
            kwargs['persistent_workers'] = False
        return original_loader(*values, **kwargs)

    data_module.DataLoader = loader
    spec = importlib.util.spec_from_file_location('voice_upstream_s1', Path(args.source))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class EpochProgress(Callback):
        def on_train_epoch_end(self, trainer, pl_module):
            print(f'VOICE_EPOCH={trainer.current_epoch+1}', flush=True)

    def single_trainer(**kwargs):
        kwargs['callbacks'].append(EpochProgress())
        kwargs['devices'] = 1
        kwargs['strategy'] = SingleDeviceStrategy(device='cuda:0' if torch.cuda.is_available() else 'cpu')
        return Trainer(**kwargs)

    module.Trainer = single_trainer
    module.main(argparse.Namespace(config_file=args.config_file))


if __name__ == '__main__':
    main()
