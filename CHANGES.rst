Changes
=======

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
