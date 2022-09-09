"""
Flix - Challenge

Author: André Junior
Maintaner: André Junior
Date: 2022-09-09
Last Modified: 2022-09-09
Description: Workflow (DAG) to fetch twittes from Twitter, sink to S3 RAW layer, run Spark job and put back on S3 on DATAHUB layer.
Steps:
 - Call Twitter API to retrieve data
 - Sink result to RAW layer on S3 (MinIO)
 - Load data from AWS S3 (minio) 
        Regular =>  PATH: flix/raw/twitter/regular/{year}/{month}/{day}
        Reprocessing  =>  PATH: flix/raw/twitter/reprocessing/{year}/{month}/{day}
 - Execute transformations and actions with Spark cluster
 - Write out to DATAHUB layer on S3 (MinIO)

 For further information please consider read the file flix_challenge.pdf available on docs folder (root).

"""

import os
import requests
from datetime import date, datetime, timedelta
from airflow import models
from airflow.utils.dates import datetime
from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.helpers import chain
from airflow.macros import ds_format
from airflow.utils.task_group import TaskGroup

###############################################
# Parameters
###############################################

# DAG START DATE
now = datetime.now()
START_DATE = datetime(now.year, now.month, now.day)
# DAG END DATE
END_DATE = None
# Default S3 Bucket
S3_BUCKET = os.environ.get("S3_BUCKET", "flix")
# S3 Bucket RAW layer
S3_RAW_KEY = os.environ.get("S3_KEY", "raw")
# S3 CONNECTION ENV VARIABLE
S3_CONN = os.environ.get("S3_CONN", "minio_conn")
# Default S3 Bucket
S3_BUCKET = os.environ.get("S3_BUCKET", "flix")
# S3 Bucket RAW layer
S3_RAW_KEY = os.environ.get("S3_KEY", "raw")
# Path on S3 Bucket for the current execution
DAG_EXECUTION_TIME = datetime.now().strftime("%Y/%m/%d/")

# Spark
spark_conn = os.environ.get("spark_conn", "spark_conn")
spark_master = "spark://spark:7077"
spark_packages = "org.apache.hadoop:hadoop-aws:3.3.1"
minio_jar = "/usr/local/spark/assets/jars/spark-select_2.11-2.0.jar"

# MinIO
minio_user = "flix"
minio_pwd = "flix#Pass#2022"

# Default args DAG
default_args = {
    "owner": "andrejr",
    "depends_on_past": False,
    "start_date": START_DATE,
    "email": ["andrejnevesjr@gmail.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

###############################################
# Workflow Functions
###############################################


def get_date_part(current_date: date):
    """Format date to use as partition on S3 Bucket

    Args:
        ds : Airflow variable replaced by execution date

    Returns:
        str: Formated date
    """
    return ds_format(current_date, '%Y-%m-%d', '%Y/%m/%d/')


# def upload_file(**kwargs) -> None:
#     """Upload file to S3 Bucket

#     Args:
#         ds (date): Airflow variable replaced by execution date
#         source_filename (str): Original filename placed on Airflow storage
#         bucket (str): S3 Bucket that we are going to write data
#         s3_conn (str): Airflow variable to connect to S3
#     """

#     # Airflow S3 Connection variable
#     s3_conn = kwargs.get("s3_conn")

#     # S3 Bucket
#     bucket = kwargs.get("bucket")

#     # File within Airflow local storage
#     source_filename = os.path.join(STORAGE, kwargs.get("source_filename"))

#     # Generate partition by date into S3
#     date_part = get_date_part(kwargs.get('ds'))

#     # Join full key to write to S3 using original filename
#     dest_filename = os.path.join(
#         S3_RAW_KEY, kwargs.get("folder"), date_part, kwargs.get("source_filename"))

#     # Upload generated file to Minio
#     s3 = S3Hook(s3_conn)
#     s3.load_file(source_filename,
#                  key=dest_filename,
#                  bucket_name=bucket,
#                  replace=True)


# ###############################################
# # DAG Definition
# ###############################################


with models.DAG(
    "flix_pipeline",
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

    start = DummyOperator(
        task_id='start',
        dag=dag,
    )

    end = DummyOperator(
        task_id='end',
        trigger_rule='all_success',
        dag=dag,
    )

    start >> end
