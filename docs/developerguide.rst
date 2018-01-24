.. _developerguide:

Developer guide
===============

Deploying specific component versions
-------------------------------------

If you want to try different versions of REANA components, you can modify your
``reana-cluster.yaml`` configuration file; see :ref:`configure`.

You can check available released versions on `REANA DockerHub
<https://hub.docker.com/u/reanahub/>`_.

Deploying latest ``master`` branch versions
-------------------------------------------

If you want to use latest ``master`` branch of REANA components and have the
code directly editable within pods, you can use ``reana-cluster-dev.yaml``.

1. Clone the REANA component under ``$HOME/reana/sources`` directory on your laptop.

2. Mount your component source code in minikube under `/code` directory:

.. code-block:: console

   $ ls -d $HOME/reana/sources
   reana-client
   reana-cluster
   reana-job-controller
   reana-message-broker
   reana-server
   reana-workflow-controller
   reana-workflow-engine-cwl
   reana-workflow-engine-yadage
   reana-workflow-monitor
   $ minikube mount $HOME/reana/sources:/code

3. Edit sources on your laptop under ``$HOME/reana/sources/reana-<component>/...`` as usual:

.. code-block:: console

   $ vim $HOME/reana/sources/reana-job-controller/reana_job_controller/app.py

4. Delete your pod and see a new pod being deployed with your changes:

.. code-block:: console

   $ kubectl get pods | grep job-controller
   $ kubectl delete pod job-controller-2461563162-r4hgg
   $ sleep 10 # wait some time...
   $ kubectl get pods | grep job-controller
   $ kubectl exec -i -t job-controller-2461563162-h9ptw /bin/bash
