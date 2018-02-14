.. _userguide:

User guide
==========

Prerequisites
-------------

REANA cloud uses `Kubernetes <https://kubernetes.io/>`_ container orchestration
system. The best way to try it out locally on your laptop is to set up `Minikube
<https://kubernetes.io/docs/getting-started-guides/minikube/>`_. How to do this
depends on your operating system.

Arch Linux
~~~~~~~~~~

For example, on Arch Linux, you should install the following packages:

- `docker <https://www.archlinux.org/packages/community/x86_64/docker/>`_
- `kubectl-bin (AUR) <https://aur.archlinux.org/packages/kubectl-bin/>`_
- `minikube (AUR) <https://aur.archlinux.org/packages/minikube/>`_

Moreover, if you plan to run Minikube via the VirtualBox hypervisor, you should
install also:

- `virtualbox <https://www.archlinux.org/packages/community/x86_64/virtualbox/>`_
- `virtualbox-guest-iso <https://www.archlinux.org/packages/community/x86_64/virtualbox-guest-iso/>`_
- `virtualbox-host-modules-arch <https://www.archlinux.org/packages/community/x86_64/virtualbox-host-modules-arch/>`_

Alternatively, if you plan to run Minikube using the KVM2 hypervisor:

- `docker-machine <https://www.archlinux.org/packages/community/x86_64/docker-machine/>`_
- `docker-machine-driver-kvm2 (AUR) <https://aur.archlinux.org/packages/docker-machine-driver-kvm2/>`_
- `libvirt <https://www.archlinux.org/packages/community/x86_64/libvirt/>`_
- `qemu <https://www.archlinux.org/packages/extra/x86_64/qemu/>`_

Here is one example of well-working versions for REANA v0.1.0:

.. code-block:: console

   $ pacman -Q | grep -iE '(docker|virtualbox|kube|qemu|libvirt)'
   docker 1:18.02.0-1
   docker-compose 1.18.0-2
   docker-machine 0.13.0-2
   docker-machine-driver-kvm2 0.25.0-1
   docker-machine-kvm 0.7.0-2
   kubectl-bin 1.9.1-1
   libvirt 4.0.0-1
   minikube 0.23.0-1
   python-docker 2.7.0-1
   python-docker-pycreds 0.2.1-2
   python-dockerpty 0.4.1-2
   qemu 2.11.0-4
   virtualbox 5.2.6-2
   virtualbox-guest-iso 5.2.7-1
   virtualbox-host-modules-arch 5.2.6-11

Start minikube
--------------

Once you have installed ``kubectl`` and ``minikube``, you can start minikube by
running:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.6.4"

or, in case of KVM2 hypervisor:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.6.4" --vm-driver=kvm2

You will see an output like:

.. code-block:: console

   Starting local Kubernetes v1.6.4 cluster...
   Starting VM...
   Getting VM IP address...
   Moving files into cluster...
   Setting up certs...
   Connecting to cluster...
   Setting up kubeconfig...
   Starting cluster components...
   Kubectl is now configured to use the cluster.

As seen from the output, Minikube startup routines already configured
``kubectl`` to interact with the newly created Kubernetes deployment, but it
best to test whether ``kubectl`` is indeed configured properly:

.. code-block:: console

   $ kubectl get all
   NAME             TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
   svc/kubernetes   ClusterIP   10.0.0.1     <none>        443/TCP   1m

Install ``reana-cluster`` CLI tool
----------------------------------

``reana-cluster`` command line interface tool is easily installable from PyPI:

.. code-block:: console

   $ pip install reana-cluster

.. _configure:

Configure REANA cluster
-----------------------

Main function of reana-cluster command line tool is to
initialize a working REANA cluster, ready to run workflows
you submit to it using reana-client.

In order to achieve this reana-cluster needs to know how
REANA cluster should be set up; e.g. what versions of REANA
components should be deployed and how the configuration of each
component should be set up.

``reana-cluster`` expects to get information via REANA cluster specification
file that comes with the package:

.. code-block:: yaml

    cluster:
      type: "kubernetes"
      version: "v1.6.4"
      url: "http://localhost"

    components:
      reana-workflow-controller:
        type: "docker"
        image: "reanahub/reana-workflow-controller:0.1.0"
        environment:
          - SHARED_VOLUME_PATH: "/reana"
          - ORGANIZATIONS: "default,alice,atlas,cms,lhcb"

      reana-job-controller:
        type: "docker"
        image: "reanahub/reana-job-controller:0.1.0"
        environment:
          - REANA_STORAGE_BACKEND: "LOCAL"

      reana-server:
        type: "docker"
        image: "reanahub/reana-server:0.1.0"

      reana-message-broker:
        type: "docker"
        image: "reanahub/reana-message-broker:0.1.0"

      reana-workflow-monitor:
        type: "docker"
        image: "reanahub/reana-workflow-monitor:0.1.0"
        environment:
          - ZMQ_PROXY_CONNECT: "tcp://zeromq-msg-proxy.default.svc.cluster.local:8667"

      reana-workflow-engine-yadage:
        type: "docker"
        image: "reanahub/reana-workflow-engine-yadage:0.1.0"
        environment:
          - ZMQ_PROXY_CONNECT: "tcp://zeromq-msg-proxy.default.svc.cluster.local:8666"

You can use the supplied ``reana-cluster.yaml``, or create use ``-f``
command-line option and specify your own file.

Initialize a REANA cluster
--------------------------

After downloading the specifications file it is just a matter of
running `init` with reana-cluster:

.. code-block:: console

   $ reana-cluster init
   [INFO] Validating REANA cluster specification file: /home/simko/.virtualenvs/reana-cluster/lib/python3.6/site-packages/reana_cluster/configurations/reana-cluster.yaml
   [INFO] /home/simko/.virtualenvs/reana-cluster/lib/python3.6/site-packages/reana_cluster/configurations/reana-cluster.yaml is a valid REANA cluster specification.
   [INFO] Cluster type specified in cluster specifications file is 'kubernetes'
   [INFO] Connecting to Kubernetes at https://192.168.39.115:8443
   Init complete

Verify REANA components
-----------------------

You can verify that components deployed to REANA cluster are set up according
to what is defined in REANA cluster specifications file `verify`:

.. code-block:: console

   $ reana-cluster verify components

Verify REANA cluster readiness
------------------------------

You can verify whether the REANA cluster is ready to serve the user requests by
using the ``kubectl`` tool:

.. code-block:: console

   $ kubectl get pods
   NAME                                     READY     STATUS              RESTARTS   AGE
   job-controller-3230226419-fxw6v          1/1       Running             0          1m
   message-broker-1926055025-bsh5p          1/1       Running             0          1m
   server-1390351625-0m7l8                  1/1       Running             0          1m
   wdb-3285397567-zzwfg                     0/1       ContainerCreating   0          1m
   workflow-controller-2663988704-d1q29     0/1       CrashLoopBackOff    2          1m
   workflow-monitor-855857361-blm56         0/1       ContainerCreating   0          1m
   yadage-alice-worker-150038894-txjq2      0/1       ContainerCreating   0          1m
   yadage-atlas-worker-3355863567-c8gkr     0/1       ContainerCreating   0          1m
   yadage-cms-worker-2408997969-dz6k4       0/1       ContainerCreating   0          1m
   yadage-default-worker-3471536063-slg1j   0/1       ContainerCreating   0          1m
   yadage-lhcb-worker-3838731947-pzkww      0/1       ContainerCreating   0          1m
   zeromq-msg-proxy-2640677031-gggp1        0/1       ContainerCreating   0          1m

In the above example, some containers are still being created. You should wait
until all the components are in the "Running" status. The REANA cluster will be
then ready for serving user requests.


Get information about a deployed REANA component
------------------------------------------------

To print component specific information, for example URLs that can
be used to interact with the component run
``reana-cluster get <COMPONENT_NAME>``.
When REANA cluster is deployed on minikube ``get``-command returns
an IP-address+port combination. This information can be used to construct URL
to access component's API or user-interface in case component provides one.

.. code-block:: console

   $ reana-cluster get reana-server
   [INFO] Validating REANA cluster specification file: /home/simko/.virtualenvs/reana-cluster/lib/python3.6/site-packages/reana_cluster/configurations/reana-cluster.yaml
   [INFO] /home/simko/.virtualenvs/reana-cluster/lib/python3.6/site-packages/reana_cluster/configurations/reana-cluster.yaml is a valid REANA cluster specification.
   [INFO] Cluster type specified in cluster specifications file is 'kubernetes'
   internal_ip: None
   ports: ['31329']
   external_ip_s: 192.168.39.115
   external_name: None

.. note::
   You can use ``get``-command if you need to configure reana-client
   (`$REANA_SERVER_URL`) or access reana-workflow-monitor:
   \http://``<external_ip_s>``:``<ports>``


Delete REANA cluster deployment
-------------------------------

To bring the cluster deployment down, i.e. delete all REANA components that
were deployed during `init`, you run:

.. code-block:: console

   $ reana-cluster down
