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
 - Write out to MongoDB

 For further information please consider read the file flix_challenge.pdf available on docs folder (root).

"""

from modules.custom_exceptions import KeywordNotFound
from modules.twitter import Twitter
import os
import sys
import configparser
import json
from io import BytesIO
from datetime import date, datetime, timedelta
from airflow import models
from airflow.utils.dates import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.macros import ds_format
from airflow.utils.log.logging_mixin import LoggingMixin
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

# Sensors
###############################################
# Parameters
###############################################
# Parse credentials file
config = configparser.ConfigParser()
config.read('/usr/local/airflow/dags/credentials.ini')
print(f"Current dir => {os.path.dirname(os.path.abspath(__file__))}")
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
# Twitter API credentials
api_consumer_key = config.get('Twitter', "consumer_key")
api_consumer_secret = config.get('Twitter', "consumer_secret")
api_access_token = config.get('Twitter', "access_token")
api_access_token_secret = config.get('Twitter', "access_token_secret")
# Twitter Endpoints
search_url = "https://api.twitter.com/2/tweets/search/recent"


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


def upload_to_s3(ti) -> None:
    """Upload data to S3 Bucket

    Args:
        ds (date): Airflow variable replaced by execution date
        source_filename (str): Original filename placed on Airflow storage
        bucket (str): S3 Bucket that we are going to write data
        s3_conn (str): Airflow variable to connect to S3
    """

    LoggingMixin().log.info("XCOM - Getting data")

    # get last execution from XCOM
    api_data = ti.xcom_pull(task_ids=['fetch_tweets'])[0]
    # Check if data exists on XCOM or raise error
    if not api_data:
        raise ValueError('No value currently stored in XComs.')

    LoggingMixin().log.info("Data - Preparing to write to S3")

    data_to_write = json.dumps(api_data).encode('utf-8')
    data_buffer = BytesIO(data_to_write)

    # File within Airflow local storage
    source_filename = f"flix_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Generate partition by date into S3
    date_part = date.today().strftime('%Y/%m/%d/')

    # # Join full key to write to S3 using original filename
    bucket_key = os.path.join(
        S3_RAW_KEY, "flix", date_part, source_filename)

    LoggingMixin().log.info("Conn - Getting S3 credentials")
    # # Upload generated file to Minio
    s3 = S3Hook(S3_CONN)

    data_buffer.seek(0, 0)

    LoggingMixin().log.info("S3 - Writing data - Start")
    s3.load_file_obj(data_buffer, bucket_key, S3_BUCKET, False)
    LoggingMixin().log.info("S3 - Writing data - End")


def twitter_authentication():
    """Initialize Twitter session using credentials

    Returns:
        twitter_session: Twitter session
    """

    LoggingMixin().log.info("Twitter API - Getting Session")

    twitter_session = Twitter(
        consumer_key=api_consumer_key,
        consumer_secret=api_consumer_secret,
        access_token=api_access_token,
        access_token_secret=api_access_token_secret)

    return twitter_session


def get_data_from_api(**kwargs):
    """Retrieve data from Twitter API according to parameters provided.
    Keyword Args:
        hashtags (str): Keywords to find on Twitter

    Returns:
        Bool: If everything is ok returns True
    """
    # Auxiliar variables to trigger single day or range from UI
    start_date_param = ""
    end_date_param = ""
    response = ""

    if kwargs.get("params") and len(kwargs.get("params")) >= 2:
        # Set start and end from parameters
        start_date_param = kwargs.get("params")['ui_start_date']
        start_end_param = kwargs.get("params")['ui_end_date']

    elif kwargs.get("params") and len(kwargs.get("params")) == 1:
        # Handling single day
        start_date_param = kwargs.get("params")['ui_start_date']
        # Set same values to beginning and ending
        start_end_param = kwargs.get("params")['ui_start_date']

    LoggingMixin().log.info("Query Twitter API - Start")

    # Get text to search on API
    text_to_search = kwargs.get("text_to_search", "")
    if len(text_to_search) == 0:
        raise KeywordNotFound

    # Attempt to authenticate on API
    session = twitter_authentication()

    # Try use authorization and attempt to proceed with the search.
    for word in text_to_search:
        response = session.get_posts_from_range(text_query=text_to_search,
                                                startDate=start_date_param,
                                                endDate=end_date_param)

    LoggingMixin().log.info("Query Twitter API - END")

    return response


def check_api():
    session = twitter_authentication()
    session.is_api_available
    return True


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

    is_api_available = PythonOperator(
        task_id='is_api_available',
        python_callable=check_api,
        provide_context=True,
        dag=dag,
    )

    error_api_status = DummyOperator(
        task_id='error_api_status',
        trigger_rule='all_failed',
        dag=dag,
    )

    # In case of errors a notification could be publish on Slack or
    # other communication channel about the issue.
    notification_slack = DummyOperator(
        task_id='notification_slack',
        trigger_rule='one_failed',
        dag=dag,
    )

    fetch_tweets = PythonOperator(
        task_id='fetch_tweets',
        python_callable=get_data_from_api,
        provide_context=True,
        trigger_rule='all_success',
        op_kwargs={
            'text_to_search': ['#FlixBus']
        },
        do_xcom_push=True,
        dag=dag,
    )
    error_search_api = DummyOperator(
        task_id='error_search_api',
        trigger_rule='all_failed',
        dag=dag,
    )

    upload_to_s3 = PythonOperator(
        task_id='upload_to_s3',
        python_callable=upload_to_s3,
        trigger_rule='all_success',
        dag=dag,
    )

    tasks_done = DummyOperator(
        task_id='tasks_done',
        trigger_rule='all_success',
        dag=dag,
    )

    end = DummyOperator(
        task_id='end',
        trigger_rule='all_success',
        dag=dag,
    )

    is_api_available >> error_api_status >> notification_slack
    fetch_tweets >> error_search_api >> notification_slack
    start >> is_api_available >> fetch_tweets >> upload_to_s3 >> tasks_done >> end
