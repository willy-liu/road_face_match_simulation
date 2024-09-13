# Minikube Config file
There are three main configurations to setup the container(pod) in minikube.

## central_server
Deploy the container(pod) of edge_device_api_server
- deployment configuration
    - cpu: "100m"(limits up to "2" cores)
    - memory: "500Mi"(limits up to "1Gi)
- hpa configuration
    - cpu averageUtilization "900m"
    - maxReplicas: 3
- service configuration
    - port: 5555
    - targetPort: 5555