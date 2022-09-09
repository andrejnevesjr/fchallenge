# Flix - Challenge

## Table of contents
- [Flix - Challenge](#flix---challenge)
  - [Table of contents](#table-of-contents)
  - [Project Requirements](#project-requirements)
  - [Project Structure](#project-structure)
  - [High Level Architecture](#high-level-architecture)
  - [:ship: Containers](#ship-containers)
  - [Step-by-Step](#step-by-step)
    - [1. Clone the Repository](#1-clone-the-repository)
    - [2. Setup environment](#2-setup-environment)
    - [3. Airflow: Create user for UI](#3-airflow-create-user-for-ui)
    - [3.1 Airflow: MongoDB, MinIO & Spark connections configuration](#31-airflow-mongodb-minio--spark-connections-configuration)
      - [MongoDB](#mongodb)
      - [MinIO](#minio)
      - [Spark](#spark)
  - [Pipeline](#pipeline)
  - [Stack](#stack)
  - [References](#references)

## Project Requirements

This project was develop and tested using the following environment.


|   Item             |        Version        |
|----------------|-------------------------------|
|Ubuntu          |`22.04.1 LTS`|
|Docker|`20.10.17, build 100c701`            |
|Docker Compose          |`1.29.2, build 5becea4c`            |
|Visual Studio Code          |`1.71.0`|
|Python          |`3.10.4`|
|OpenJDK          |`11.0.16`|
|Git          |`2.34.1`|

> If due to license issues you are not allowed to use Docker it's possible to replace it with [Podman](https://podman.io/) which is an alternative highly recommended for companies such as RedHat.

## Project Structure
 

This challenge is currently structured with the following specifications.

|   Path             |        Description        |
|----------------|-------------------------------|
|airflow|`Contains Airflow Dags (Pipelines)`            |
|docs          |`Project docs and pipelines (step-by-step)`            |
|imgs          |`Auxiliar folder to hold images used on this repo`|

  

## High Level Architecture

  
![](./imgs/HLA.png "HLA")
  



## :ship: Containers

  

*  **airflow-webserver**: Airflow v2.2.4 (Webserver & Scheduler)

   - image: andrejunior/airflow-spark:latest | Based on python:3.8-buster

   - port: 8085

*  **MongoDB**: NoSQL 

   - image: mongo:5.0


*  **MinIO**: Object storage

   - image: bitnami/minio:latest

  

*  **spark-master**: Spark Master

   - image: bitnami/spark:3.2.1

   - port: 8081

  

*  **spark-worker**: Spark workers

   - image: bitnami/spark:3.2.1


  

## Step-by-Step

  

### 1. Clone the Repository

 
`git clone https://github.com/ajnevesjr/flix-challenge`

### 2. Setup environment

  
```
cd flix-challenge
docker-compose -f docker-compose.yml up -d
```
 

### 3. Airflow: Create user for UI

To access Airflow UI is required to create a new user account, so in our case, we are going to create an fictional user with an Admin role attached.

  

> **NOTE**: Before **RUN** the command below please confirm that Airflow is up and running, it can be checked by accessing the URL [http://localhost:8085](http://localhost:8085). Have in mind that in the first execution it may take 2 to 3 minutes :stuck_out_tongue_winking_eye:

![](./imgs/airflow_up.png "airflow_up")

```
docker-compose run airflow-webserver airflow users create --role Admin --username flix \
--email flix@challenge.example --firstname flix --lastname service --password flix
```
  
Expected output:

  

![](./imgs/user_created.png "user_created")
  

### 3.1 Airflow: MongoDB, MinIO & Spark connections configuration

  

1. Open the service in your browser at http://localhost:8085

Use the credentials

```
User: flix
Password: flix
```

2. Click on Admin -> Connections in the top bar.
    ![](./imgs/connections.png "connections")

3. Click on + sign and fill in the necessary details for each source below:
    ![](./imgs/add_conn.png "add_conn")
  

#### MongoDB
  

    Conn ID: mongo_conn    
    Conn Type: Amazon S3    
    Extra: consists of the JSON below:

```

```

Click on save:

![](./imgs/minio.png "minio")


#### MinIO
  

    Conn ID: minio_conn    
    Conn Type: Amazon S3    
    Extra: consists of the JSON below:

```
{ 
"aws_access_key_id":"flix",
"aws_secret_access_key": "flix#Pass#2022",
"host": "http://bucket:9000"
}
```

Click on save:

![](./imgs/minio.png "minio")

  

#### Spark

  

    Conn ID: spark_conn    
    Host: spark://spark    
    Port: 7077
    Extra: consists of the JSON below:

```
{"queue": "root.default"}
```

Click on save:

![](./imgs/spark.png "spark")
  


  

## Pipeline

Please check out the documentation available on folder docs under the file [flix_tutorial.pdf](./docs/flix_tutorial.pdf)

  

![](./imgs/pipeline.png "pipeline")

 


## Stack

|        Application        |URL                          |Credentials                         |
|----------------|-------------------------------|-----------------------------|
|Airflow| [http://localhost:8085](http://localhost:8085) | ``` User: flix``` <br> ``` Pass: flix``` |         |
|MinIO| [http://localhost:9001](http://localhost:9001) | ``` User: flix``` <br> ``` Pass: flix#Pass#2022``` |           |
|Spark (Master) | [http://localhost:8081](http://localhost:8081)|  |         |
  

## References

[airflow.apache.org](https://airflow.apache.org/docs/apache-airflow/stable/)

[puckel/docker-airflow](https://github.com/puckel/docker-airflow)

[cordon-thiago/airflow-spark](https://github.com/cordon-thiago/airflow-spark/)

[pyjaime/docker-airflow-spark](https://github.com/pyjaime/docker-airflow-spark/)

