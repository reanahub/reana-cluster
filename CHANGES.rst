Changes
=======

Version 0.6.0 (2019-12-27)
--------------------------

- Upgrades to Kubernetes 1.16.
- Moves Traefik installation to Helm 3.0.0.
- Creates a new Kubernetes service account for REANA with appropriate
  permissions.
- Makes database connection details configurable so that REANA can connect to
  databases external to the cluster.
- Adds an interactive mode on cluster initialisation to allow providing
  deployment secrets such as OAuth integration, GitLab integration or
  external database details.
- Autogenerates deployment secrets if not provided by the administrator at
  cluster creation time.
- Adds CERN specific Kerberos configuration files.
- Adds new flag and configuration to optionally deploy with CERN EOS storage.
- Renames ``reana-cluster.yaml`` to ``reana-cluster-minikube.yaml`` for local
  developments.
- Adds Python 3.8 support.

Version 0.5.0 (2019-04-24)
--------------------------

- Upgrades to Kubernetes 1.14, Helm 2.13 and Minikube 1.0.
- Separates cluster infrastructure pods from runtime workflow engine pods that
  will be created by workflow controller.
- Adds support for exposing user interactive sessions such as Jupyter notebook
  via Traefik ingress controller.
- Introduces configurable CVMFS and CephFS shared volume mounts. Changes
  ``SHARED_VOLUME_PATH`` to ``/var/reana/``.
- Adds support for optional HTTPS protocol termination at the ``REANA-Server``
  component.
- Improves workflow execution queuing and scheduling via ``REANA-Server``
  sidecar.
- Removes unused ``REANA-Workflow-Monitor`` component and ``ZeroMQ`` service.
- Enables Flask debugging mode for the cluster development configuration by
  setting ``FLASK_ENV`` accordingly.

Version 0.4.0 (2018-11-07)
--------------------------

- Improves AMQP re-connection handling. Switches from ``pika`` to ``kombu``.
- Enhances test suite and increases code coverage.
- Changes license to MIT.

Version 0.3.4 (2018-10-10)
--------------------------

- Fixes default storage method to use Local instead of CephFS.

Version 0.3.3 (2018-09-27)
--------------------------

- Adds configuration and cluster component templates for mounting CephFS volumes.

Version 0.3.2 (2018-09-25)
--------------------------

- Bug fix in ``reana-cluster status`` command.

Version 0.3.1 (2018-09-07)
--------------------------

- Upgrades to Kubernetes 1.11.2 and Minikube 0.28.2.
- Renames ``reana-cluster env --all`` to ``reana-cluster env --include-admin-token`` for additional safety.
- Pins REANA-Commons and third-party dependencies such as Click and Jinja2.
- Adds support for Python 3.7.

Version 0.3.0 (2018-08-10)
--------------------------

- Adds REANA Workflow Engine Serial component.
- Upgrades to latest Kubernetes version.
- Allows ``ipdb`` debugging on components running inside the cluster.

Version 0.2.0 (2018-04-19)
--------------------------

- Adds support for Common Workflow Language workflows.
- Adds new ``status`` command to display health status of the cluster.
- Adds new ``env`` command to help setting client environments.
- Reduces verbosity level for commands.
- Enriches documentation about KVM2 hypervisors or running multiple clusters.

Version 0.1.1 (2018-01-31)
--------------------------

- Fixes Python packaging problem related to classifier list.
- Fixes REANA-Workflow-Monitor component configuration related to environment
  variables and ``ZMQ_PROXY_CONNECT`` settings.
- Fixes ``reana-cluster verify backend`` version comparison.
- Adds developer documentation on how to use Minikube on remote hosts.

Version 0.1.0 (2018-01-30)
--------------------------

- Initial public release.

.. admonition:: Please beware

   Please note that REANA is in an early alpha stage of its development. The
   developer preview releases are meant for early adopters and testers. Please
   don't rely on released versions for any production purposes yet.
