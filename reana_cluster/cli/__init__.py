# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017 CERN.
#
# REANA is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# REANA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# REANA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
"""REANA cluster command line interface."""

import logging
import sys

import click

from . import cluster

from ..config import cluster_spec_default_file_path, supported_backends

from ..utils import load_spec_file

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
    type=click.Choice(['debug', 'info']),
    default='info')
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
@click.pass_context
def cli(ctx, loglevel, skip_validation, file):
    """Command line application for managing a REANA cluster."""
    logging.basicConfig(
        format=DEBUG_LOG_FORMAT if loglevel == 'debug' else LOG_FORMAT,
        stream=sys.stderr,
        level=logging.DEBUG if loglevel == 'debug' else logging.INFO)

    try:
        cluster_spec = load_spec_file(click.format_filename(file),
                                      skip_validation)

        ctx.obj = Config()

        cluster_type = cluster_spec['cluster']['type']

        logging.info("Cluster type specified in cluster "
                     "specifications file is '{}'"
                     .format(cluster_type))

        ctx.obj.backend = supported_backends[cluster_type](cluster_spec)

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
