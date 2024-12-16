## System Architecture

The overall system architecture can be summarized as follows:

1.  **Edge Device Simulation**
    *   **Function**: Simulates real edge devices, reading pre-recorded videos and performing pedestrian face detection.
    *   **Process**:
        *   After selecting a video, it continuously reads the video and uses YOLOv8 to detect and track pedestrians.
        *   When a face is detected, the face image and other related information (such as timestamp, source, etc.) are sent to the API server.
        *   Requests are sent asynchronously to avoid blocking video reading.
        *   Requests are sent only after accumulating a certain number of face information, reducing the load on the server.
    *   **Programming Language**: Python
    *   **Interface**: Simple UI for selecting different videos.

2.  **Edge Device API Server**
    *   **Function**: Receives data from edge devices, calculates face feature values, and stores all information in a MySQL database.
    *   **Technical Implementation**:
        *   Uses the Flask framework to build the API server, handling requests from edge devices.
        *   Deployed on Kubernetes, automatically scaling up and down based on load.
        *   Uses Docker to package the server into a container for easy deployment and management.

3.  **MySQL Database**
    *   **Function**: Stores all received data, including face feature values, timestamps, and location information.
    *   **Purpose**: Provides efficient data access and retrieval functions to support subsequent queries and analysis.
    *   **Configuration**:
        *   Uses Persistent Volume Claim (PVC) to ensure data persistence.
        *   Uses NodePort to allow the MySQL service to be accessed from outside the Kubernetes cluster.

4.  **Web Search Server**
    *   **Function**: Provides a user interface for searching, allowing users to upload face images to search for matches.
    *   **Process**:
        *   Receives user-uploaded images and converts them into feature values.
        *   Compares the feature values with those stored in the database and displays the results on a webpage.

## Technical Details

*   **Containerization**: Uses Docker to package applications into containers.
*   **Container Orchestration**: Uses Kubernetes for deployment and management, enabling automatic scaling and load balancing.
*   **Programming Languages**: Python, SQL
*   **Frameworks/Libraries**: Flask, YOLOv8, Kubernetes

## Deployment Details

*   **Kubernetes Configuration**:
    *   `Deployment`: Defines the deployment of the application, including containers, replica counts, resource limits, etc.
    *   `Service`: Defines how the service is accessed, using the `LoadBalancer` type for external access to the service.
    *   `Horizontal Pod Autoscaler (HPA)`: Automatically adjusts the number of application replicas based on CPU usage.
*   **MySQL Configuration**:
    *   `PersistentVolume` & `PersistentVolumeClaim`: Uses PVC to ensure data persistence of MySQL.
    *   `NodePort`: Uses `NodePort` to allow external access to the MySQL service from the Kubernetes cluster.

## How it Works

1.  **Simulation**: The edge device simulator continuously reads the video and detects faces.
2.  **Transmission**: The detected face data and related information are sent to the API server.
3.  **Processing**: The API server calculates face feature values and stores all information in the MySQL database.
4.  **Search**: Users upload face images through the web search server to find matching records and display the result.
5.  **Resource Management**: Kubernetes and HPA automatically adjust system resources based on load.

## Experimental Results

*   **Load Test**:
    *   **Initial State**: When idle, server CPU usage is very low.
    *   **Increased Load**: As the number of simulated edge devices increases, HPA automatically increases the number of server replicas, and CPU usage stays balanced.
    *   **Decreased Load**: When the number of simulated edge devices decreases, HPA automatically reduces the number of server replicas to save resources.
<img width="825" alt="image" src="https://github.com/user-attachments/assets/2f8218eb-5455-468c-86ea-bf9004da03eb" />
<img width="819" alt="image" src="https://github.com/user-attachments/assets/884429f8-1bf2-406a-bb3b-0d4a5dd941c1" />
<img width="753" alt="image" src="https://github.com/user-attachments/assets/cdfddd67-28e3-407b-b4cb-2bd787cd2f20" />

 
