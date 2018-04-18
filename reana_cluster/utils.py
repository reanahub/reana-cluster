# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
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
"""REANA cluster utils."""

import json
import logging

import click
import yaml
from jsonschema import ValidationError, validate

from .config import cluster_spec_schema_file_path


def load_spec_file(filepath, skip_validation=False):
    """Load and validate REANA cluster specification file.

    :param filepath: Filepath where to load REANA cluster spec file.
    :param skip_validation: If set, loaded specifications is not validated
        against schema
    :raises IOError: Error reading REANA cluster spec file from given filepath.
    :raises ValidationError: Given REANA cluster spec file does not validate
        against REANA cluster specification schema.
    """
    try:
        with open(filepath) as f:
            cluster_spec = yaml.load(f.read())

        if not (skip_validation):
            logging.info('Validating REANA cluster specification file: {0}'
                         .format(filepath))
            if _validate_cluster_spec(cluster_spec):
                logging.info('{0} is a valid REANA cluster specification.'
                             .format(filepath))

        return cluster_spec
    except IOError as e:
        logging.info(
            'Something went wrong when reading specifications file from '
            '{filepath} : \n'
            '{error}'.format(filepath=filepath, error=e.strerror))
        raise e
    except Exception as e:
        raise e


def _validate_cluster_spec(cluster_spec):
    """Validate REANA cluster specification file according to jsonschema.

    :param cluster_spec: Dictionary representing REANA cluster spec file.
    :raises ValidationError: Given REANA cluster spec file does not validate
        against REANA cluster specification schema.
    """
    try:
        with open(cluster_spec_schema_file_path, 'r') as f:
            cluster_spec_schema = json.loads(f.read())

            validate(cluster_spec, cluster_spec_schema)

    except IOError as e:
        logging.info(
            'Something went wrong when reading REANA cluster validation '
            'schema from {filepath} : \n'
            '{error}'.format(filepath=cluster_spec_schema_file_path,
                             error=e.strerror))
        raise e
    except ValidationError as e:
        logging.info('Invalid REANA cluster specification: {error}'
                     .format(error=e.message))
        raise e

    return True


def cli_printer(headers, _filter, data):
    """Print a response in a tabulated format."""
    _filter = [h.lower() for h in _filter] + [h.upper() for h in _filter]
    headers = [h for h in headers if not _filter or h in _filter]
    # Maximum header width
    header_widths = [len(h) for h in headers]

    for row in data:
        for idx in range(len(headers)):
            # If a row contains an element which is wider update maximum width
            if header_widths[idx] < len(str(row[idx])):
                header_widths[idx] = len(str(row[idx]))
    # Prepare the format string with the maximum widths
    formatted_output_parts = ['{{:<{0}}}'.format(hw)
                              for hw in header_widths]
    formatted_output = '   '.join(formatted_output_parts)
    # Print the table with the headers capitalized
    click.echo(formatted_output.format(*[h.upper() for h in headers]))
    for row in data:
        click.echo(formatted_output.format(*row))
