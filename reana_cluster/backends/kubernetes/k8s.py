# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018, 2019 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Abstract Base Class representing REANA cluster backend."""

import json
import logging
import os
import shlex
import subprocess

import pkg_resources
import yaml
from jinja2 import (Environment, FileSystemLoader, TemplateNotFound,
                    TemplateSyntaxError)
from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes.client import Configuration
from kubernetes.client.rest import ApiException
from pkg_resources import parse_version

from reana_cluster.reana_backend import ReanaBackendABC


class KubernetesBackend(ReanaBackendABC):
    """A class for interacting with Kubernetes.

    Attributes:
        __cluster_type  Type of the backend this class implements support for.
        _conf   Configuration.

    """

    __cluster_type = 'Kubernetes'

    _conf = {
        'templates_folder': pkg_resources.resource_filename(
            __name__, '/templates'),
        'min_version': 'v1.16.3',
        'max_version': 'v1.16.3',
    }

    def __init__(self,
                 cluster_spec,
                 cluster_conf=None,
                 kubeconfig=None,
                 kubeconfig_context=None,
                 eos=False,
                 cephfs=False,
                 cephfs_volume_size=None,
                 cephfs_storageclass=None,
                 cephfs_os_share_id=None,
                 cephfs_os_share_access_id=None,
                 debug=False,
                 url=None,
                 ui=None):
        """Initialise Kubernetes specific ReanaBackend-object.

        :param cluster_spec: Dictionary representing complete REANA
            cluster spec file.

        :param cluster_conf: A generator/iterable of Kubernetes YAML manifests
            of REANA components as Python objects. If set to `None`
            cluster_conf will be generated from manifest templates in
            `templates` folder specified in `_conf.templates_folder`

        :param kubeconfig: Name of the kube-config file to use for configuring
            reana-cluster. If set to `None` then `$HOME/.kube/config` will be
            used.
            Note: Might pickup a config-file defined in $KUBECONFIG as well.

        :param kubeconfig_context: set the active context. If is set to `None`,
            current_context from config file will be used.
        :param eos: Boolean flag toggling the mount of EOS volume for jobs.
        :param cephfs: Boolean flag toggling the usage of a cephfs volume as
            storage backend.
        :param cephfs_volume_size: Int number which represents cephfs volume
            size (GB)
        :param cephfs_storageclass: Name of an existing cephfs storageclass.
        :param cephfs_os_share_id: CephFS Manila share id.
        :param cephfs_os_share_access_id: CephFS Manila share access id.
        :param debug: Boolean flag setting debug mode.
        :param url: REANA cluster url.
        :param ui: Should REANA be deployed with REANA-UI?.
        """
        logging.debug('Creating a ReanaBackend object '
                      'for Kubernetes interaction.')

        # Load Kubernetes cluster configuration. If reana-cluster-minikube.yaml
        # doesn't specify this K8S Python API defaults to '$HOME/.kube/config'
        self.kubeconfig = kubeconfig or \
            cluster_spec['cluster'].get('config', None)
        self.kubeconfig_context = kubeconfig_context or \
            cluster_spec['cluster'].get('config_context', None)

        k8s_api_client_config = Configuration()

        k8s_config.load_kube_config(kubeconfig, self.kubeconfig_context,
                                    k8s_api_client_config)

        Configuration.set_default(k8s_api_client_config)

        # Instantiate clients for various Kubernetes REST APIs
        self._corev1api = k8s_client.CoreV1Api()
        self._versionapi = k8s_client.VersionApi()
        self._appsv1api = k8s_client.AppsV1Api()
        self._rbacauthorizationv1api = k8s_client.RbacAuthorizationV1Api()
        self._storagev1api = k8s_client.StorageV1Api()
        self._networkingv1api = k8s_client.NetworkingV1beta1Api()

        self.k8s_api_client_config = k8s_api_client_config

        self.cluster_spec = cluster_spec
        self.cluster_conf = cluster_conf or \
            self.generate_configuration(
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

    @property
    def cluster_type(self):
        """."""
        return self.__cluster_type

    @property
    def cluster_url(self):
        """Return URL of Kubernetes instance `reana-cluster` connects to."""
        return self.k8s_api_client_config.host

    @property
    def current_config(self):
        """Return Kubernetes configuration (e.g. `~/.kube/config`)."""
        return self.k8s_api_client_config

    @property
    def current_kubeconfig_context(self):
        """Return K8S kubeconfig context used to initialize K8S Client(s)."""
        return self.kubeconfig_context

    @property
    def current_kubeconfig(self):
        """Return K8S kubeconfig used to initialize K8S Client(s).

        (e.g. `~/.kube/config`)

        """
        return self.kubeconfig

    @classmethod
    def generate_configuration(
            cls, cluster_spec, cephfs=False, eos=False,
            cephfs_volume_size=None,
            cephfs_storageclass=None,
            cephfs_os_share_id=None,
            cephfs_os_share_access_id=None,
            debug=False, url=None, ui=None):
        """Generate Kubernetes manifest files used to init REANA cluster.

        :param cluster_spec: Dictionary representing complete REANA
            cluster spec file.
        :param eos: Boolean flag toggling the mount of EOS volume for jobs.
        :param cephfs: Boolean which represents whether REANA is
            deployed with CEPH or not.
        :param cephfs_volume_size: Int to set CEPH volume size in GB.
        :param cephfs_storageclass: Name of an existing cephfs storageclass.
        :param cephfs_os_share_id: CephFS Manila share id.
        :param cephfs_os_share_access_id: CephFS Manila share access id.
        :param debug: Boolean which represents whether REANA is
            deployed in debug mode or not.
        :param url: REANA cluster url.
        :param ui: Boolean which represents whether REANA is
            deployed with the User Interface or not.

        :return: A generator/iterable of generated Kubernetes YAML manifests
            as Python objects.
        """
        # Setup an Environment for Jinja
        env = Environment(
            loader=FileSystemLoader(
                cls._conf['templates_folder']),
            keep_trailing_newline=False
        )

        # Define where are backend conf params needed when rendering templates.
        be_conf_params_fp = cls._conf['templates_folder'] + '/config.yaml'

        try:
            with open(be_conf_params_fp) as f:

                # Load backend conf params
                backend_conf_parameters = yaml.load(f.read(),
                                                    Loader=yaml.FullLoader)
                # Configure CephFS is chosen as shared storage backend
                if cephfs or cluster_spec['cluster'].get('cephfs'):
                    backend_conf_parameters['CEPHFS'] = True
                    backend_conf_parameters['CEPHFS_STORAGECLASS'] = \
                        cephfs_storageclass or 'manila-csicephfs-share'
                    backend_conf_parameters['CEPHFS_VOLUME_SIZE'] = \
                        cluster_spec['cluster'].get(
                            'cephfs_volume_size', cephfs_volume_size)
                    backend_conf_parameters['CEPHFS_OS_SHARE_ID'] = \
                        cluster_spec['cluster'].get(
                            'cephfs_os_share_id', cephfs_os_share_id)
                    backend_conf_parameters['CEPHFS_OS_SHARE_ACCESS_ID'] = \
                        cluster_spec['cluster'].get(
                            'cephfs_os_share_access_id',
                            cephfs_os_share_access_id)

                if eos or cluster_spec['cluster'].get('eos'):
                    backend_conf_parameters['EOS'] = \
                        cluster_spec['cluster'].get('eos', eos)

                if debug or cluster_spec['cluster'].get('debug'):
                    backend_conf_parameters['DEBUG'] = True

                if ui or cluster_spec['cluster'].get('ui'):
                    backend_conf_parameters['UI'] = True

                if cluster_spec['cluster'].get('root_path'):
                    backend_conf_parameters['ROOT_PATH'] = \
                        cluster_spec['cluster'].get('root_path')

                if cluster_spec['cluster'].get('shared_volume_path'):
                    backend_conf_parameters['SHARED_VOLUME_PATH'] = \
                        cluster_spec['cluster'].get('shared_volume_path')

                if cluster_spec['cluster'].get('db_persistence_path'):
                    backend_conf_parameters['DB_PERSISTENCE_PATH'] = \
                        cluster_spec['cluster'].get('db_persistence_path')

                # Would it be better to combine templates or populated
                # templates in Python code for improved extensibility?
                # Just drop a .yaml template and add necessary to config.yaml
                # without changing anything?

                # Load template combining all other templates from
                # templates folder
                template = env.get_template('backend_conf.yaml')

                components = cluster_spec['components']
                rs_img = components['reana-server']['image']
                rwfc_img = components['reana-workflow-controller']['image']
                rmb_img = components['reana-message-broker']['image']

                rs_environment = components['reana-server']\
                    .get('environment', [])
                rwfc_environment = components['reana-workflow-controller'] \
                    .get('environment', [])
                rmb_environment = components['reana-message-broker'] \
                    .get('environment', [])

                rs_mountpoints = components['reana-server']\
                    .get('mountpoints', [])
                rwfc_mountpoints = components['reana-workflow-controller']\
                    .get('mountpoints', [])
                rmb_mountpoints = components['reana-message-broker'] \
                    .get('mountpoints', [])

                # Render the template using given backend config parameters
                cluster_conf = template.\
                    render(backend_conf_parameters,
                           REANA_URL=cluster_spec['cluster'].get(
                               'reana_url',
                               url),
                           SERVER_IMAGE=rs_img,
                           WORKFLOW_CONTROLLER_IMAGE=rwfc_img,
                           MESSAGE_BROKER_IMAGE=rmb_img,
                           RS_MOUNTPOINTS=rs_mountpoints,
                           RWFC_MOUNTPOINTS=rwfc_mountpoints,
                           RMB_MOUNTPOINTS=rmb_mountpoints,
                           RS_ENVIRONMENT=rs_environment,
                           RWFC_ENVIRONMENT=rwfc_environment,
                           RMB_ENVIRONMENT=rmb_environment,
                           REANA_SERVICE_ACCOUNT_NAME='reana-system'
                           )
                # Strip empty lines for improved readability
                cluster_conf = '\n'.join(
                    [line for line in cluster_conf.splitlines() if
                     line.strip()])
                # Should print the whole configuration in a loop
                # Now prints just memory address of generator object
                logging.debug('Loaded K8S config successfully: \n {}'
                              .format(yaml.load_all(cluster_conf,
                                                    Loader=yaml.FullLoader)))

        except TemplateNotFound as e:
            logging.info(
                'Something wrong when fetching K8S config file templates from '
                '{filepath} : \n'
                '{error}'.format(
                    filepath=cls._conf['templates_folder'],
                    error=e.strerror))
            raise e
        except TemplateSyntaxError as e:
            logging.info(
                'Something went wrong when parsing K8S template from '
                '{filepath} : \n'
                '{error}'.format(
                    filepath=e.filename,
                    error=e.strerror))
            raise e
        except IOError as e:
            logging.info(
                'Something wrong when reading K8S config parameters-file from '
                '{filepath} : \n'
                '{error}'.format(filepath=be_conf_params_fp,
                                 error=e.strerror))
            raise e

        # As Jinja rendered string is basically multiple YAML documents in one
        # string parse it with YAML-library and return a generator containing
        # independent YAML documents (split from `---`) as Python objects.
        return yaml.load_all(cluster_conf, Loader=yaml.FullLoader)

    def init(self, traefik, interactive):
        """Initialize REANA cluster, i.e. deploy REANA components to backend.

        :param traefik: Boolean flag determines if traefik should be
            initialized.
        :type traefik: bool
        :param interactive: Boolean flag determines if configuration should be
            provided by the user via interactive prompt.
        :type interactive: bool

        :return: `True` if init was completed successfully.
        :rtype: bool

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        if not self._cluster_running():
            pass

        # Should check that cluster is not already initialized.
        # Maybe use `verify_components()` or `get()` each component?

        if traefik is True:
            self.initialize_traefik()

        from reana_cluster.utils import check_needed_secrets_are_created
        check_needed_secrets_are_created(interactive=interactive)

        for manifest in self.cluster_conf:
            try:

                logging.debug(json.dumps(manifest))

                if manifest['kind'] == 'Deployment':
                    self._appsv1api.create_namespaced_deployment(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'Namespace':
                    self._corev1api.create_namespace(body=manifest)

                elif manifest['kind'] == 'ResourceQuota':
                    self._corev1api.create_namespaced_resource_quota(
                        body=manifest,
                        namespace=manifest['metadata']['namespace'])

                elif manifest['kind'] == 'Service':
                    self._corev1api.create_namespaced_service(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))
                elif manifest['kind'] == 'ClusterRole':
                    self._rbacauthorizationv1api.create_cluster_role(
                            body=manifest)
                elif manifest['kind'] == 'ClusterRoleBinding':
                    self._rbacauthorizationv1api.create_cluster_role_binding(
                            body=manifest)

                elif manifest['kind'] == 'Ingress':
                    self._networkingv1api.create_namespaced_ingress(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'ServiceAccount':
                    self._corev1api.create_namespaced_service_account(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'StorageClass':
                    self._storagev1api.create_storage_class(body=manifest)

                elif manifest['kind'] == 'PersistentVolumeClaim':
                    self._corev1api.create_namespaced_persistent_volume_claim(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'ConfigMap':
                    self._corev1api.create_namespaced_config_map(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

            except ApiException as e:  # Handle K8S API errors

                if e.status == 409:
                    logging.info(
                        '{0} {1} already exists, continuing ...'.format(
                            manifest['kind'],
                            manifest['metadata'].get('name')))
                    continue

                if e.status == 400:
                    pass

                raise e

        return True

    def initialize_traefik(self):
        """Install and initialize traefik via Helm.

        Traefik dashboard service is not accessible by default, to make it
        accessible inside Minikube service type is changed to NodePort.
        """
        from reana_cluster.config import (traefik_configuration_file_path,
                                          traefik_release_name)
        try:
            add_helm_repo_cmd = \
                ('helm repo add stable'
                 ' https://kubernetes-charts.storage.googleapis.com/')
            add_helm_repo_cmd = shlex.split(add_helm_repo_cmd)
            subprocess.check_output(add_helm_repo_cmd)
            namespace = 'kube-system'
            label_selector = 'app=traefik'
            cmd = ('helm install {} stable/traefik --namespace {} '
                   ' --values {} ').format(
                       traefik_release_name,
                       namespace,
                       traefik_configuration_file_path,
                       traefik_release_name)
            cmd = shlex.split(cmd)
            subprocess.check_output(cmd)
            traefik_objects = self._corev1api.list_namespaced_service(
                namespace=namespace,
                label_selector=label_selector,
                limit=2)
            traefik_dashboard_body = None
            for traefik_object in traefik_objects.items:
                if 'dashboard' in traefik_object.metadata.name:
                    traefik_dashboard_body = traefik_object
                    break
            traefik_dashboard_body.spec.type = 'NodePort'
            self._corev1api.patch_namespaced_service(
                name=traefik_dashboard_body.metadata.name,
                namespace=namespace,
                body=traefik_dashboard_body
            )
        except Exception as e:
            logging.error('Traefik initialization failed \n {}.'.format(e))
            raise e

    def _cluster_running(self):
        """Verify that interaction with cluster backend is possible.

        THIS IS CURRENTLY JUST A MOCKUP. NO REAL CHECKS ARE DONE.

        Verifies that Kubernetes deployment is reachable through it's REST API.
        Only very basic checking is done and it is not guaranteed that REANA
        cluster can be initialized, just that interaction with the specified
        Kubernetes deployment is possible.

        :return: `True` if Kubernetes deployment is reachable through
            it's REST API.
        """
        # Maybe just do a request to `/healthz/ping` -endpoint at cluster_url?
        # i.e no kubernetes-python client interaction?
        return True

    def restart(self):
        """Restarts all deployed components. NOT CURRENTLY IMPLEMENTED.

        :raises NotImplementedError:

        """
        raise NotImplementedError()

    def down(self, delete_traefik=False, delete_secrets=False):
        """Bring REANA cluster down, i.e. deletes all deployed components.

        Deletes all Kubernetes Deployments, Namespaces, Resourcequotas and
        Services that were created during initialization of REANA cluster.

        :param delete_traefik: Whether REANA traefik should be deleted or not.
        :type delete_traefik: bool
        :param delete_secrets: Whether REANA secrets should be deleted or not.
        :type delete_secrets: bool

        :return: `True` if all components were destroyed successfully.
        :rtype: bool

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        # What is a good propagationPolicy of `V1DeleteOptions`?
        # Default is `Orphan`
        # https://kubernetes.io/docs/concepts/workloads/controllers/garbage-collection/
        # https://github.com/kubernetes-incubator/client-python/blob/master/examples/notebooks/create_deployment.ipynb

        if not self._cluster_running():
            pass

        # All K8S objects seem to use default -namespace.
        # Is this true always, or do we create something for non-default
        # namespace (in the future)?

        for manifest in self.cluster_conf:
            try:
                logging.debug(json.dumps(manifest))

                if manifest['kind'] == 'Deployment':
                    self._appsv1api.delete_namespaced_deployment(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions(
                            propagation_policy="Foreground",
                            grace_period_seconds=5),
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'Namespace':
                    self._corev1api.delete_namespace(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions())

                elif manifest['kind'] == 'ResourceQuota':
                    self._corev1api.delete_namespaced_resource_quota(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions(),
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'Service':
                    self._corev1api.delete_namespaced_service(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions(),
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'ClusterRole':
                    self._rbacauthorizationv1api.delete_cluster_role(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions())

                elif manifest['kind'] == 'ClusterRoleBinding':
                    self._rbacauthorizationv1api.\
                        delete_cluster_role_binding(
                            name=manifest['metadata']['name'],
                            body=k8s_client.V1DeleteOptions())

                elif manifest['kind'] == 'Ingress':
                    self._networkingv1api.delete_namespaced_ingress(
                            name=manifest['metadata']['name'],
                            body=k8s_client.V1DeleteOptions(),
                            namespace=manifest['metadata'].get('namespace',
                                                               'default'))

                elif manifest['kind'] == 'ServiceAccount':
                    self._corev1api.delete_namespaced_service_account(
                        name=manifest['metadata']['name'],
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'StorageClass':
                    self._storagev1api.delete_storage_class(
                            name=manifest['metadata']['name'],
                            body=k8s_client.V1DeleteOptions(),
                            namespace=manifest['metadata'].get('namespace',
                                                               'default'))

                elif manifest['kind'] == 'PersistentVolumeClaim':
                    self._corev1api.\
                        delete_namespaced_persistent_volume_claim(
                            name=manifest['metadata']['name'],
                            body=k8s_client.V1DeleteOptions(),
                            namespace=manifest['metadata'].get('namespace',
                                                               'default'))

            except ApiException as e:  # Handle K8S API errors

                if e.status == 409:  # Conflict, object probably already exists
                    pass

                if e.status == 404:
                    pass

                if e.status == 400:
                    pass

        # delete all CVMFS persistent volume claims
        pvcs = self._corev1api.list_namespaced_persistent_volume_claim(
            'default')
        for pvc in pvcs.items:
            if pvc.metadata.name.startswith('csi-cvmfs-'):
                self._corev1api.\
                        delete_namespaced_persistent_volume_claim(
                            name=pvc.metadata.name,
                            body=k8s_client.V1DeleteOptions(),
                            namespace=manifest['metadata'].get('namespace',
                                                               'default'))
        # delete all CVMFS storage classes
        scs = self._storagev1api.list_storage_class()
        for sc in scs.items:
            if sc.metadata.name.startswith('csi-cvmfs-'):
                self._storagev1api.delete_storage_class(
                    name=sc.metadata.name,
                    body=k8s_client.V1DeleteOptions())

        if delete_traefik:
            from reana_cluster.config import traefik_release_name
            namespace = 'kube-system'
            helm_ls_cmd = 'helm ls -n {}'.format(namespace)
            helm_ls_cmd = shlex.split(helm_ls_cmd)
            helm_ls_output = \
                subprocess.check_output(helm_ls_cmd).decode('UTF-8')
            if traefik_release_name in helm_ls_output:
                cmd = 'helm del --namespace {} {}'.format(
                    namespace,
                    traefik_release_name)
                cmd = shlex.split(cmd)
                subprocess.check_output(cmd)
        if delete_secrets:
            from reana_cluster.utils import delete_reana_secrets
            delete_reana_secrets()

        return True

    def get_component(self, component_name, component_namespace='default'):
        """Fetch info (e.g.URL) about deployed REANA component.

        Fetches information such as URL(s) of a REANA component deployed to
        REANA cluster.

        :param component_name: Name of the REANA component whose information
            is to be fetched.
        :type component_name: string

        :param component_namespace: Namespace where REANA component specified
            with `component_name` is deployed. Kubernetes specific information.
        :type component_namespace: string

        :return: Information (e.g. URL(s)) about a deployed REANA component.
        :rtype: dict

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        comp_info = {
            'internal_ip': '',
            'ports': [],
            'external_ip_s': [],
            'external_name': '',
        }

        try:

            # Strip reana-prefix from component name if it is there.
            component_name_without_prefix = None
            if not component_name.startswith('reana-'):
                component_name_without_prefix = component_name
            else:
                component_name_without_prefix = component_name[len('reana-'):]

            minikube_ip = None

            # If running on Minikube, ip-address is Minikube VM-address
            nodeconf = self._corev1api.list_node()

            # There can be many Nodes. Is this a problem?
            # (i.e. How to know which is the one should be connected to?)
            for item in nodeconf.items:
                if item.metadata.name == 'minikube' or \
                        item.metadata.name == self.kubeconfig_context:

                    # Running on minikube --> get ip-addr
                    minikube_ip = subprocess.check_output(['minikube', 'ip'])
                    minikube_ip = minikube_ip.decode("utf-8")
                    minikube_ip = minikube_ip.replace('\n', '')

            # Get ip-addresses and ports of the component (K8S service)
            comp = self._corev1api.read_namespaced_service(
                component_name_without_prefix,
                component_namespace)

            logging.debug(comp)
            comp_info['external_name'] = comp.spec.external_name
            comp_info['external_ip_s'] = [minikube_ip] or \
                comp.spec.external_i_ps
            comp_info['internal_ip'] = comp.spec.external_i_ps

            if component_name_without_prefix == 'server':
                traefik_ports = self.get_traefik_ports()
            else:
                traefik_ports = None

            if traefik_ports:
                comp_info['ports'].extend(traefik_ports)
            else:
                for port in comp.spec.ports:
                    if minikube_ip:
                        comp_info['ports'].append(str(port.node_port))
                    else:
                        comp_info['ports'].append(str(port.port))

            logging.debug(comp_info)

        except ApiException as e:  # Handle K8S API errors

            if e.status == 409:  # Conflict
                pass

            if e.status == 404:
                pass

            if e.status == 400:
                pass

            raise e

        return comp_info

    def get_traefik_ports(self):
        """Return the list of Traefik ports if Traefik is present."""
        namespace = 'kube-system'
        label_selector = 'app=traefik'
        try:
            traefik_objects = self._corev1api.list_namespaced_service(
                namespace=namespace,
                label_selector=label_selector,
                limit=2)
            ports = []
            for object in traefik_objects.items:
                for port in object.spec.ports:
                    if port.name == 'http':
                        ports.append(port.node_port)
                    elif port.name == 'https':
                        ports.append(port.node_port)
            return ports
        except ApiException as e:
            if e.reason == "Not Found":
                logging.error("K8s traefik objects were not found.")
            else:
                logging.error('Exception when calling '
                              'CoreV1Api->list_namespaced_service:\n {e}'
                              .format(e))
            return None
        except Exception as e:
            logging.error('Something went wrong. Traefik port '
                          'was not found:\n {e}'.format(e))
            return None

    def verify_components(self):
        """Verify that REANA components are setup according to specifications.

        Verifies that REANA components are set up as specified in REANA
        cluster specifications file.
        Components must be deployed first, before verification can be done.

        Currently verifies only that docker image (<NAME>:<TAG> -string) of a
        deployed component matches to docker image specified in REANA cluster
        specification file.

        :return: Dictionary with component names for keys and booleans
        for values stating if verification was successful.
        :rtype: dict

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        if not self._cluster_running():
            pass

        try:
            matching_components = dict()
            for manifest in self.cluster_conf:

                # We are only interested in Deployment manifests since
                # these define docker images that Kubernetes Pods based on
                # these Deployments should be using.
                if manifest['kind'] == 'Deployment':
                    component_name = manifest['metadata']['name']

                    # Kubernetes Deployment manifest could have multiple
                    # containers per manifest file. Current implementation
                    # expects only one container per manifest file.
                    spec_img = manifest['spec'][
                        'template']['spec']['containers'][0]['image']

                    deployed_comp = self._appsv1api. \
                        read_namespaced_deployment(component_name, 'default')

                    logging.debug(deployed_comp)

                    # Kubernetes Deployment could have multiple containers per
                    # Deployment. Current implementation expects only one
                    # container per deployment.
                    # THIS WILL CAUSE PROBLEM if there are two Pods and one
                    # of them is (even temporarily, e.g. update situation)
                    # based on "old" image defined in older REANA cluster
                    # specification file.
                    deployed_img = deployed_comp.spec.template.spec.containers[
                        0].image

                    logging.info('Component name: {}\n'
                                 'Specified image: {}\n'
                                 'Currently deployed image: {}\n'
                                 .format(component_name,
                                         spec_img,
                                         deployed_img))

                    matching_components[component_name] = True
                    if not spec_img == deployed_img:
                        matching_components[component_name] = False
                        logging.error('Mismatch between specified and '
                                      'deployed image of {}. \n'
                                      'Specified image: {}\n'
                                      'Currently deployed image: {}\n'
                                      .format(component_name,
                                              spec_img,
                                              deployed_img))

        except ApiException as e:  # Handle K8S API errors

            if e.status == 409:
                pass

            if e.status == 404:
                pass

            if e.status == 400:
                pass

            raise e

        return matching_components

    def verify_backend(self):
        """Verify that cluster backend is compatible with REANA.

        Verifies that REANA cluster backend is 1) compatible with REANA and
        2) set up as specified in REANA cluster specifications file.

        Currently includes just a version check.

        :return: `True` if verification of backend was successful.
        :rtype: bool

        """
        return self._verify_k8s_version()

    def _verify_k8s_version(self):
        """Verify version of K8S instance is compatible with REANA cluster.

        Verifies that the version of Kubernetes instance `reana-cluster` is
        connecting to is compatible with REANA (min, max versions in config)
        and that version is compatible with target version in REANA cluster
        specifications file.

        Version strings are parsed according to PEP440, which seems to support
        semantic versioning style what Kubernetes uses.
        (PEP440 not fully compliant with semver)

        :return: Dictionary containing the current version, if it is compatible
        and the maximum compatible version.
        :rtype: dict

        """
        if not self._cluster_running():
            pass

        curr_ver = parse_version(self._versionapi.get_code().git_version)
        expected_ver = parse_version(
            self.cluster_spec['cluster']['version'])
        max_ver = parse_version(self._conf['max_version'])
        min_ver = parse_version(self._conf['min_version'])

        logging.info('Current K8S version: {}\n'
                     'Specified K8S version: {}\n'
                     'Max supported K8S version: {}\n'
                     'Min supported K8S version: {}'
                     .format(curr_ver, expected_ver, max_ver, min_ver))

        k8s_version_compatibility = dict(current_version=curr_ver,
                                         is_compatible=True,
                                         max_version=max_ver)
        # Compare current K8S version to max / min
        if curr_ver > max_ver:
            k8s_version_compatibility['is_compatible'] = False
            logging.error('Your Kubernetes version is too new: {cur} \n'
                          'Newest version REANA supports is: {max}'
                          .format(cur=curr_ver, max=max_ver))

        elif curr_ver < min_ver:
            k8s_version_compatibility['is_compatible'] = False
            logging.error('Your Kubernetes version is too old: {cur} \n'
                          'Oldest version REANA supports is: {min}'
                          .format(cur=curr_ver, min=min_ver))

        # Compare specified version to max/min
        elif expected_ver > max_ver:
            k8s_version_compatibility['is_compatible'] = False
            logging.error('Specified Kubernetes version is too new: {cur} \n'
                          'Newest version REANA supports is: {max}'
                          .format(cur=curr_ver, max=max_ver))

        elif expected_ver < min_ver:
            k8s_version_compatibility['is_compatible'] = False
            logging.error('Specified Kubernetes version is too old: {cur} \n'
                          'Oldest version REANA supports is: {min}'
                          .format(cur=curr_ver, min=min_ver))

        # Compare specified version to current K8S version
        elif expected_ver < curr_ver:
            k8s_version_compatibility['is_compatible'] = False
            logging.error('Your Kubernetes version is too new: {cur} \n'
                          'Specification expects: {expected}'
                          .format(cur=curr_ver, expected=expected_ver))

        elif expected_ver > curr_ver:
            k8s_version_compatibility['is_compatible'] = False
            logging.error('Your Kubernetes version is too old: {cur} \n'
                          'Specification expects: {expected}'
                          .format(cur=curr_ver, expected=expected_ver))

        return k8s_version_compatibility

    def get_components_status(self, component=None):
        """Return status for components in cluster.

        Gets all pods in the k8s namespace and matches them with the
        equivalent component, writing their status in a dictionary.

        :return: Dictionary containing each component and its status
        :rtype: dict

        """
        def _write_status(pod, component_name, components_status):
            """Determine the component status."""
            if pod.status.container_statuses:
                if pod.status.container_statuses[0].ready:
                    components_status[component_name] = 'Running'
                elif pod.status.container_statuses[0].\
                        state.waiting is not None:
                    components_status[component_name] = \
                        pod.status.container_statuses[0].\
                        state.waiting.reason
                else:
                    components_status[component] = 'Unavailable'

        if component and component.startswith('reana-'):
            component = component.replace('reana-', '')
        all_pods = self._corev1api.list_namespaced_pod('default')
        components_status = dict()

        if component:
            for current_pod in all_pods.items:
                if current_pod.metadata.name.startswith(component):
                    _write_status(current_pod, component, components_status)
                    break
        else:
            deployment_manifests = [m for m in self.cluster_conf
                                    if m['kind'] == 'Deployment']
            for manifest in deployment_manifests:
                current_pod = None
                for pod in all_pods.items:
                    if pod.metadata.name.startswith(
                            manifest['metadata']['name']):
                        current_pod = pod
                        break
                if current_pod:
                    _write_status(current_pod, manifest['metadata']['name'],
                                  components_status)
        return components_status

    def exec_into_component(self, component_name, command):
        """Execute a command inside a component.

        :param component_name: Name of the component where the command will be
            executed.
        :param command: String which represents the command to execute inside
            the component.
        :return: Returns a string which represents the output of the command.
        """
        available_components = [manifest['metadata']['name'] for manifest in
                                self.cluster_conf
                                if manifest['kind'] == 'Deployment']

        if component_name not in available_components:
            raise Exception('{0} does not exist.'.format(component_name))

        component_pod_name = subprocess.check_output([
            'kubectl', 'get', 'pods',
            '-l=app={component_name}'.format(component_name=component_name),
            '-o', 'jsonpath="{.items[0].metadata.name}"'
        ]).decode('UTF-8').replace('"', '')

        component_shell = [
            'kubectl', 'exec', '-t', component_pod_name, '--']

        command_inside_component = []
        command_inside_component.extend(component_shell)
        command_inside_component.extend(command)

        output = subprocess.check_output(command_inside_component)
        return output.decode('UTF-8')
