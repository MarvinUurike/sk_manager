import boto3
import os
from botocore.config import Config

# Global cache for resources
_resources = {}

def get_resource(service_name):
    """Lazily load and cache a boto3 resource"""
    if service_name not in _resources:
        _resources[service_name] = boto3.resource(service_name)
    return _resources[service_name]

def get_client(service_name, region=None):
    """Lazily load and cache a boto3 client with regional config if needed"""
    cache_key = f"client_{service_name}_{region}"
    if cache_key not in _resources:
        config = None
        if service_name == 's3':
            # S3v4 signature for eu-north-1 compatibility
            config = Config(signature_version='s3v4', s3={'addressing_style': 'virtual'})
        
        _resources[cache_key] = boto3.client(
            service_name, 
            region_name=region or os.environ.get('REGION', 'eu-north-1'),
            config=config
        )
    return _resources[cache_key]

def get_table(table_env_var):
    """Get a DynamoDB table object from an environment variable name"""
    table_name = os.environ.get(table_env_var)
    if not table_name:
        raise ValueError(f"Environment variable {table_env_var} not set")
    return get_resource('dynamodb').Table(table_name)
