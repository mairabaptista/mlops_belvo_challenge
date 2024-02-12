import pandas as pd
from airflow.contrib.hooks.aws_hook import AwsHook
from pydantic import ValidationError
import os, io

from utils.data_model import CreditCardDataModel

def read_data_from_s3(**kwargs) -> pd.DataFrame:
    """
    Reads data from s3 bucket as a Pandas DataFrame
    Parameters:
        **kwargs (dict): Keyword arguments passed by Airflow

    Returns:
        df (pd.DataFrame): loaded Pandas DataFrame
    """
    s3_key = os.environ['S3_KEY']
    s3_bucket = os.environ['S3_BUCKET']

    aws_hook = AwsHook(os.environ['AWS_CONN_ID'])
    s3_client = aws_hook.get_client_type('s3')

    s3_object = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
    s3_data = s3_object['Body'].read().decode('utf-8')

    df = pd.read_csv(io.StringIO(s3_data))
    return df

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates the data DataFrame using Pydantic.
    Parameters:
        df: (pd.DataFrame): inpute DataFrame

    Returns:
        df (pd.DataFrame): validated DataFrame
    """
    try:
        rows = df.to_dict(orient='records')
        validated_data = [CreditCardDataModel(**row) for row in rows]
        print("Data validation successful!")
        return df
    except ValidationError as e:
        print(f"Validation error: {e}")

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs any data preparation tasks. Only a simple lowercase transform is included here for simplification
    Parameters:
        df: (pd.DataFrame): inpute DataFrame

    Returns:
        df (pd.DataFrame): validated DataFrame
    """
    df["cidade"] = df["cidade"].str.lower()
    return df