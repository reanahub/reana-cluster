# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REANA cluster administration (init, restart, etc.) commands."""

import errno
import logging
import os
import sys
import traceback

import click
import yaml

from ..config import (generated_cluster_conf_default_path,
                      reana_env_exportable_info_components,
                      reana_cluster_ready_necessary_components)
from reana_cluster.utils import build_component_url
from reana_commons.utils import click_table_printer


@click.command(help='Bring REANA cluster down, i.e. delete all '
                    'deployed components.')
@click.option(
    '--remove-persistent-storage',
    is_flag=True,
    help='NOT IMPLEMENTED.\n'
         'If set, also persistent storage inside the cluster is deleted.')
@click.pass_context
def down(ctx, remove_persistent_storage):
    """Bring REANA cluster down, i.e. deletes all deployed components."""
    try:
        ctx.obj.backend.down()
    except Exception as e:
        logging.debug(str(e))


@click.command(help='Fetch information (e.g. URLs) about a REANA component '
                    'deployed in REANA cluster.')
@click.argument('component')
@click.option(
    '--namespace',
    default='default',
    help='Namespace of the component which URL should be resolved.')
@click.pass_context
def get(ctx, component, namespace):
    """Fetch URL for a REANA component running in REANA cluster."""
    try:
        component_info = ctx.obj.backend.get_component(component, namespace)

        for key, value in component_info.items():
            click.echo('{}: {}'.format(key, value))

    except Exception as e:
        logging.debug(str(e))


@click.command(help='Display the commands to set up the environment for the '
                    'REANA client.')
@click.option(
    '--namespace',
    default='default',
    help='Namespace of the components which configuration should be produced.')
@click.option(
    '--insecure-url', is_flag=True,
    help='REANA Server URL with HTTP.')
@click.option(
    '--include-admin-token',
    is_flag=True,
    help='Display also commands how to set REANA_ACCESS_TOKEN for '
         'administrator access. Use with care! Do no share with regular '
         'users.')
@click.pass_context
def env(ctx, namespace, insecure_url, include_admin_token):
    """Produce shell exportable list of REANA components' urls."""
    try:
        export_lines = []
        component_export_line = 'export {env_var_name}={env_var_value}'
        for component in reana_env_exportable_info_components:
            component_info = ctx.obj.backend.get_component(
                component, namespace)

            export_lines.append(component_export_line.format(
                env_var_name='{0}_URL'.format(
                    component.upper().replace('-', '_')),
                env_var_value=build_component_url(
                    component_info['external_ip_s'][0],
                    component_info['ports'],
                    insecure=insecure_url),
            ))
        if include_admin_token:
            get_admin_token_sql_query_cmd = [
                'psql', '-U', 'reana', 'reana', '-c',
                'SELECT access_token FROM user_']
            sql_query_result = \
                ctx.obj.backend.exec_into_component(
                    'db',
                    get_admin_token_sql_query_cmd)
            # We get the token from the SQL query result
            admin_access_token = sql_query_result.splitlines()[2].strip()
            export_lines.append(component_export_line.format(
                env_var_name='REANA_ACCESS_TOKEN',
                env_var_value=admin_access_token))

        click.echo('\n'.join(export_lines))
    except Exception as e:
        logging.debug(traceback.format_exc())
        logging.debug(str(e))
        click.echo(
            click.style('Environment variables could not be generated: \n{}'
                        .format(str(e)), fg='red'),
            err=True)


@click.command(help='NOT IMPLEMENTED.\n'
                    'Restart components running in REANA cluster.')
@click.option(
    '--remove-persistent-storage',
    is_flag=True,
    help='NOT IMPLEMENTED.\n'
         'If set, also persistent storage inside the cluster is deleted.')
@click.pass_context
def restart(ctx, remove_persistent_storage):
    """Restart all components running in REANA cluster."""
    try:
        ctx.obj.backend.restart()
    except Exception as e:
        logging.debug(str(e))


@click.command(help="Initialize REANA cluster, i.e. deploy all REANA "
                    "components to cluster type (e.g. 'kubernetes') "
                    "defined in REANA cluster specifications file")
@click.option(
    '--skip-initialization', is_flag=True,
    help='If set, configuration files for selected cluster type are '
         'generated, but cluster is not initialized.')
@click.option(
    '-o',
    '--output',
    type=click.Path(exists=False, resolve_path=False),
    help='Path where generated cluster configuration files should be saved.'
         'If no value is given no files are outputted.')
@click.option(
    '-t',
    '--traefik', is_flag=True,
    help='Install and initialize Traefik')
@click.pass_context
def init(ctx, skip_initialization, output, traefik):
    """Initialize REANA cluster."""
    try:
        backend = ctx.obj.backend
        if not skip_initialization:
            logging.info('Connecting to {cluster} at {url}'
                         .format(cluster=backend.cluster_type,
                                 url=backend.cluster_url))
            backend.init(traefik)
            click.echo(
                click.style("REANA cluster is initialised.", fg='green'))

        if output:
            path = click.format_filename(output)
            click.echo(click.style(
                'Writing deployable REANA cluster configuration '
                'to {0}.'.format(path), fg='green'))

            for manifest in backend.cluster_conf:

                folder = os.path.join(path, manifest['kind'].lower() + 's')
                filename = manifest['metadata']['name'] + '-manifest.yaml'
                filepath = os.path.join(folder, filename)

                # Create folders if they don't exist
                # Based on: https://stackoverflow.com/a/12517490
                if not os.path.exists(os.path.dirname(filepath)):
                    try:
                        os.makedirs(os.path.dirname(filepath))
                    except OSError as exc:  # Guard against race condition
                        if exc.errno != errno.EEXIST:
                            raise

                with click.open_file(filepath, mode='w+') as output_file:
                    yaml.dump(manifest, output_file, default_flow_style=False)

    except Exception as e:
        logging.exception(str(e))


@click.group(chain=True,
             invoke_without_command=True,
             help='Verify that configuration of REANA cluster and '
                  'components deployed there are set up according to '
                  'REANA cluster specifications file.')
@click.pass_context
def verify(ctx):
    """Verify configuration of running cluster and deployed components."""
    try:
        # If user didn't supply any sub-commands execute complete verification
        if ctx.invoked_subcommand is None:
            cli_verify_backend(ctx)
            cli_verify_components(ctx)

    except Exception as e:
        logging.debug(str(e))


@click.command('backend',
               help='Only verify that configuration of REANA cluster matches '
                    'to what is specified in REANA cluster specifications '
                    'file.')
@click.pass_context
def cli_verify_backend(ctx):
    """Verify configuration of running cluster backend."""
    logging.debug(ctx.obj.backend.cluster_spec)
    backend_compatibility = ctx.obj.backend.verify_backend()
    data = []
    headers = ['kubernetes version', 'is compatible']
    data.append(list(map(str, [backend_compatibility['current_version'],
                               backend_compatibility['is_compatible']])))
    click_table_printer(headers, [], data)


@click.command('components',
               help='Only verify that configuration of REANA components '
                    'deployed to REANA cluster matches to what is specified '
                    'in REANA cluster specifications file.')
@click.pass_context
def cli_verify_components(ctx):
    """Verify configuration of components deployed in a running cluster."""
    logging.debug(ctx.obj.backend.cluster_spec)
    matching_components = ctx.obj.backend.verify_components()
    data = []
    headers = ['component', 'image']
    for component_name in matching_components:
        image_matches = 'match' if matching_components[component_name] \
            else 'mismatch'
        data.append(list(map(str, [component_name, image_matches])))
    click_table_printer(headers, [], data)


@click.command(help='Display the status of each component'
               ' and if the cluster is ready.')
@click.option(
    '--component',
    default=None,
    help='Specify for which component you want the status'
         'e.g. job-controller.')
@click.pass_context
def status(ctx, component):
    """Display the status of cluster components and if the cluster is ready."""
    components_status = ctx.obj.backend.get_components_status(component)

    # detect if all components are in running state:
    all_running = True
    data = []
    headers = ['component', 'status']
    for component_name in components_status:
        data.append(list(map(str, [component_name,
                                   components_status[component_name]])))
        if components_status[component_name] != 'Running':
            all_running = False

    # detect if all necessary components are present:
    all_present = True
    if component:
        if component not in components_status:
            all_present = False
    else:
        for component_name in reana_cluster_ready_necessary_components:
            if component_name not in components_status:
                all_present = False

    # print component status table:
    click_table_printer(headers, [], data)

    # produce final report:
    if all_running and all_present:
        if component:
            click.echo(click.style('REANA component {0} is ready.'
                                   .format(component), fg='green'))
        else:
            click.echo(click.style('REANA cluster is ready.', fg='green'))
    else:
        if component:
            click.echo(click.style('REANA component {0} is not ready.'.
                                   format(component), fg='yellow'))
        else:
            click.echo(click.style('REANA cluster is not ready.', fg='yellow'))
        sys.exit(1)


verify.add_command(cli_verify_backend)
verify.add_command(cli_verify_components)
