# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA cluster command line interface."""

import logging
import sys

import click
from reana_cluster.cli import cluster
from reana_cluster.config import (cluster_spec_default_file_path,
                                  supported_backends)
from reana_cluster.utils import load_spec_file

DEBUG_LOG_FORMAT = '[%(asctime)s] p%(process)s ' \
                   '{%(pathname)s:%(lineno)d} ' \
                   '%(levelname)s - %(message)s'

LOG_FORMAT = '[%(levelname)s] %(message)s'


class Config(object):
    """Configuration object to share across commands."""

    def __init__(self):
        """Initialize config variables."""
        self.backend = None
        self.cluster_spec = None


@click.group()
@click.option(
    '--loglevel',
    '-l',
    help='Sets log level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING']),
    default='WARNING')
@click.option(
    '-f',
    '--file',
    type=click.Path(exists=True, resolve_path=True),
    default=cluster_spec_default_file_path,
    help='REANA cluster specifications file describing configuration '
         'for the cluster and for REANA components')
@click.option(
    '-s',
    '--skip-validation', is_flag=True,
    help='If set, specifications file is not validated before '
         'starting the initialization.')
@click.option(
    '--eos', is_flag=True,
    help='If EOS is available in the deployed cluster, this config will '
         'make it available inside the REANA jobs.')
@click.option(
    '--cephfs', is_flag=True,
    help='Set cephfs volume for cluster storage.')
@click.option(
    '--cephfs-volume-size',
    type=int,
    help='Set cephfs volume size in GB.')
@click.option(
    '--cephfs-storageclass',
    help='A preset cephfs storageclass.')
@click.option(
    '--cephfs-os-share-id',
    help='Manila share id.')
@click.option(
    '--cephfs-os-share-access-id',
    help='Manila share access id.')
@click.option(
    '--debug', is_flag=True,
    help='If set, deploy REANA in debug mode.')
@click.option(
    '-u',
    '--url',
    help='Set REANA cluster URL')
@click.option(
    '--ui', is_flag=True,
    help='Deploy the REANA-UI inside the REANA Cluster.')
@click.pass_context
def cli(ctx, loglevel, skip_validation, file, eos,
        cephfs, cephfs_volume_size, cephfs_storageclass, cephfs_os_share_id,
        cephfs_os_share_access_id, debug, url, ui):
    """Command line application for managing a REANA cluster."""
    logging.basicConfig(
        format=DEBUG_LOG_FORMAT if loglevel == 'debug' else LOG_FORMAT,
        stream=sys.stderr,
        level=loglevel)

    try:
        cluster_spec = load_spec_file(click.format_filename(file),
                                      skip_validation)
        cephfs_options = [cephfs_volume_size, cephfs_storageclass,
                          cephfs_os_share_id, cephfs_os_share_access_id]
        if any(cephfs_options) and not cephfs:
            cephfs_volume_size = None
            cephfs_storageclass = None
            click.echo(click.style('CEPHFS configuration not taken into '
                                   ' account because of missing `--cephfs`'
                                   ' flag', fg='yellow'))
        ctx.obj = Config()

        cluster_type = cluster_spec['cluster']['type']

        logging.info("Cluster type specified in cluster "
                     "specifications file is '{}'"
                     .format(cluster_type))
        ctx.obj.backend = supported_backends[cluster_type](
            cluster_spec,
            eos=eos,
            cephfs=cephfs,
            cephfs_volume_size=cephfs_volume_size,
            cephfs_storageclass=cephfs_storageclass,
            cephfs_os_share_id=cephfs_os_share_id,
            cephfs_os_share_access_id=cephfs_os_share_access_id,
            debug=debug,
            url=url,
            ui=ui)

    # This might be unnecessary since validation of cluster specifications
    # file is done against schema and schema should include the supported
    # cluster (backend) types.
    # On the other hand there is --skip-validation flag.
    except KeyError as e:
        logging.info('Unsupported value for cluster type in '
                     'reana cluster specifications file: {}'
                     .format(cluster_type))
        raise e

    except Exception as e:
        logging.debug(str(e))


cli.add_command(cluster.init)
cli.add_command(cluster.verify)
cli.add_command(cluster.down)
cli.add_command(cluster.restart)
cli.add_command(cluster.get)
cli.add_command(cluster.env)
cli.add_command(cluster.status)
cli.add_command(cluster.version)
