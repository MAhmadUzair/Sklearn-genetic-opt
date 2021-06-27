import logging
import os
import time
from copy import deepcopy
from joblib import dump


from .base import BaseCallback
from ..parameters import Metrics

logger = logging.getLogger(__name__)  # noqa

try:
    import tensorflow as tf
except ModuleNotFoundError:  # noqa
    tf = None  # noqa


class LogbookSaver(BaseCallback):
    """
    Saves the estimator.logbook parameter chapter object in a local file system
    """

    def __init__(self, checkpoint_path, **dump_options):
        """
        Parameters
        ----------
        checkpoint_path: str
            Location where checkpoint will be saved to
        dump_options, str
            Valid kwargs from joblib :class:`~joblib.dump`
        """

        self.checkpoint_path = checkpoint_path
        self.dump_options = dump_options

    def on_step(self, record=None, logbook=None, estimator=None):
        try:
            dump_logbook = deepcopy(estimator.logbook.chapters["parameters"])
            dump(dump_logbook, self.checkpoint_path, **self.dump_options)
        except Exception as e:
            logger.error("Could not save the Logbook in the checkpoint")

        return False


class TensorBoard(BaseCallback):
    """Log all the fitness metrics to Tensorboard into log_dir/run_id folder"""

    def __init__(self, log_dir="./logs", run_id=None):
        """
        Parameters
        ----------
        log_dir: str, default="./logs"
            Path to the main folder where the data will be log
        run_id: str, default=None
            Subfolder where the data will be log, if None it will create a folder
            with the current datetime with format time.strftime("%Y_%m_%d-%H_%M_%S")
        """
        if tf is None:
            logger.error(
                "Tensorflow not found, pip install tensorflow to use TensorBoard callback"
            )  # noqa

        self.log_dir = log_dir

        if run_id is None:
            self.run_id = time.strftime("%Y_%m_%d-%H_%M_%S")
        else:
            self.run_id = run_id

        self.path = os.path.join(log_dir, self.run_id)

    def on_step(self, record=None, logbook=None, estimator=None):

        # Get the last metric value
        stats = logbook[-1]

        # Create logs files placeholder
        writer = tf.summary.create_file_writer(self.path)

        # Log the metrics
        with writer.as_default():
            for metric in Metrics.list():
                tf.summary.scalar(name=metric, data=stats[metric], step=stats["gen"])
        writer.flush()

        return False
