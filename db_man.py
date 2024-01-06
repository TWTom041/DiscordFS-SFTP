#!/usr/bin/env python3
import click
from pymongo import MongoClient
import bson
import yaml

# MongoDB connection parameters
DB_NAME = "dsdrive"
COLLECTION_NAME = "tree"

# Default MongoDB connection parameters
DEFAULT_MONGO_HOST = "localhost"
DEFAULT_MONGO_PORT = 27017
DEFAULT_DB_NAME = "your_database_name"
DEFAULT_COLLECTION_NAME = "your_collection_name"

@click.group()
@click.option('--mongourl', default=DEFAULT_MONGO_HOST, help='MongoDB url')
@click.option('--config', default=None, help='Config file, if provided, other options will be ignored.')
@click.pass_context
def cli(ctx, mongourl, config):
    """Simple CLI for dumping and loading MongoDB data."""
    ctx.ensure_object(dict)
    ctx.obj['client'] = MongoClient(mongourl)
    with open(config, "r") as file:
        _config = yaml.load(file.read(), Loader=yaml.FullLoader)
        mongodb_config = _config.get("MongoDB", {})
        prefix = mongodb_config.get("Prefix", "mongodb://")
        MONGO_HOST = mongodb_config.get("Host", "127.0.0.1")
        MONGO_PORT = mongodb_config.get("Port", "27017")
        mgdb_url = f"{prefix}{MONGO_HOST}:{MONGO_PORT}"
        ctx.obj['client'] = MongoClient(mgdb_url)
    ctx.obj['db'] = ctx.obj['client'][DB_NAME]
    ctx.obj['collection'] = ctx.obj['db'][COLLECTION_NAME]


@cli.command()
@click.argument("output_file", type=click.File("wb"))
@click.option("-k", "--key", default=False, help="Include SFTP host private key.")
@click.option("-w", "--webhooks", default=False, help="Include webhooks.")
@click.option("-e", "--encrypt", default=False, help="Encrypt the output file.")
@click.pass_context
def dump(ctx, output_file, key, webhooks, encrypt):
    """Dump MongoDB data to a file."""
    data = {}
    data["database"] = list(ctx.obj['collection'].find())
    if key:
        with open(".conf/host_key", "rb") as file:
            data["key"] = file.read()
    if webhooks:
        with open(".conf/webhooks.txt", "rb") as file:
            data["webhooks"] = file.read()
    bson_data = bson.BSON.encode(data)
    output_file.write(bson_data)
    click.echo("Data dumped successfully.")


@cli.command()
@click.argument("input_file", type=click.File("rb"))
@click.pass_context
def load(ctx, input_file):
    """Load MongoDB data from a BSON file."""
    bson_data = input_file.read()
    data = list(bson.decode_all(bson_data)[0]["data"])
    ctx.obj['collection'].insert_many(data)
    click.echo("Data loaded successfully.")


if __name__ == "__main__":
    cli()