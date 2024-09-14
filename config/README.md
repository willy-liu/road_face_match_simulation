# Minikube Config file
There are three main configurations to setup the container(pod) in minikube.

## central_server
Deploy the container(pod) of edge_device_api_server
- deployment configuration
    - image refer to edge_device_api_server folder
    - cpu: "100m"(limits up to "2" cores)
    - memory: "500Mi"(limits up to "1Gi)
- hpa configuration
    - cpu averageUtilization "900m"
    - maxReplicas: 3
- service configuration
    - port: 5555
    - targetPort: 5555

## database
Deploy the mysql database and phpmyadmin for easy access
- mysql deployment configuration
    - image: mysql:8.0
    - port: 3306
- mysql pv(persist volume) configuration
    - storage: 5Gi
    - mountPath: /mnt/data/mysql
- mysql service configuration
    - port: 3306
    - targetPort: 3306
- phpmyadmin deployment configuration
    - image: phpmyadmin/phpmyadmin:latest
- phpmyadmin service configuration
    - port: 80
    - targetPort: 80