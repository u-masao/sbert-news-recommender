import logging
from pathlib import Path

import click
import mlflow
import pandas as pd

from src.models import Embedder, VectorEngine
from src.utils import get_device_info


def embedding(kwargs):
    # init logging
    logger = logging.getLogger(__name__)

    # load dataset
    df = pd.read_parquet(kwargs["input_filepath"])

    # make features
    df["sentence"] = df["title"] + "\n" + df["content"]

    # embedding
    embedder = Embedder(kwargs["model_name_or_filepath"])
    embeddings = embedder.encode(
        df["sentence"], method=kwargs["embedding_method"]
    )

    # build vector engine
    engine = VectorEngine(df["id"], embeddings)

    # output
    Path(kwargs["engine_filepath"]).parent.mkdir(exist_ok=True, parents=True)
    engine.save(kwargs["engine_filepath"])
    Path(kwargs["sentences_filepath"]).parent.mkdir(
        exist_ok=True, parents=True
    )
    df.to_parquet(kwargs["sentences_filepath"])

    # logging
    log_params = {
        "output.length": len(df),
        "output.columns": df.shape[1],
    }
    mlflow.log_params(log_params)
    logger.info(log_params)
    logger.info(f"output dataframe: \n{df}")
    logger.info(f"output columns: \n{df.columns}")


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("engine_filepath", type=click.Path())
@click.argument("sentences_filepath", type=click.Path())
@click.option(
    "--model_name_or_filepath",
    type=str,
    default="oshizo/sbert-jsnli-luke-japanese-base-lite",
)
@click.option("--embedding_method", type=str, default="chunk_split")
@click.option("--mlflow_run_name", type=str, default="develop")
def main(**kwargs):
    # init logging
    logger = logging.getLogger(__name__)
    logger.info("start process")
    mlflow.set_experiment("recommend")
    mlflow.start_run(run_name="mlflow_run_name")

    # log cli options
    logger.info(f"args: {kwargs}")
    mlflow.log_params({f"args.{k}": v for k, v in kwargs.items()})
    mlflow.log_params(get_device_info())

    # process
    embedding(kwargs)

    # cleanup
    mlflow.end_run()
    logger.info("complete process")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()
