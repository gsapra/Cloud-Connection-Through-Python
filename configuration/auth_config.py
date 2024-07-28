import base64
import logging
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import boto3
import google.auth
import google.auth.transport.requests
from google.cloud import container_v1
from jinja2 import FileSystemLoader, Environment
from kubernetes import client as kubernetes_client

from configuration.aws.aws_assume_role_manager import AWSAssumeRoleManager
from configuration import get_token

logging.basicConfig(level=logging.INFO)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

BASE_DIR = Path(__file__).resolve().parent


def get_auth_config_path_for_gcp(project_id, cluster_id, zone=None, region=None, return_config=False):
    location = region
    if zone:
        location = zone
    logger.info('Attempting to init k8s client from cluster response.')
    container_client = container_v1.ClusterManagerClient()
    logger.info(f'Attempting to get cluster {cluster_id} in project {project_id} in region/zone {location}.')
    response = container_client.get_cluster(name=f"/{project_id}/locations/{location}/clusters/{cluster_id}")
    certificate_authority_data = response.master_auth.cluster_ca_certificate
    name = f'gke_{project_id}_{location}_{cluster_id}'
    host = f'https://{response.endpoint}'
    creds, projects = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    token = creds.token
    config = {
        'certificate_authority_data': certificate_authority_data,
        'host': host,
        'name': name,
        'token': token,
    }
    if return_config:
        return config

    configuration = kubernetes_client.Configuration()
    logger.info(f'Found endpoint {response.endpoint}')
    configuration.host = f'https://{response.endpoint}'
    with NamedTemporaryFile(delete=False) as ca_cert:
        ca_cert.write(
            base64.b64decode(response.master_auth.cluster_ca_certificate)
        )
    configuration.ssl_ca_cert = ca_cert.name
    configuration.api_key_prefix['authorization'] = 'Bearer'
    configuration.api_key['authorization'] = creds.token

    logger.info('Received token')
    template_path = os.path.join(BASE_DIR)
    loader = FileSystemLoader(template_path)
    env = Environment(loader=loader)
    template = env.get_template('config.yaml.j2')
    template_output = template.render(config)
    rendered_yaml_path = os.path.join(template_path, f'template_{time.time()}.yaml')
    with open(rendered_yaml_path, 'w') as fh:
        fh.write(template_output)
    logger.info(f'Created config file at {rendered_yaml_path}')
    # redis_conn.set(rkey, rendered_yaml_path, 60 * 60 * 24)
    return rendered_yaml_path


def get_auth_config_path_for_aws(cluster_id, region, iam_role_arn, return_config=False, external_id=None):
    logger.info(f'Attempting to init k8s client from cluster response. external_id {external_id}.')
    cross_credentials = AWSAssumeRoleManager(role_arn=iam_role_arn, external_id=external_id)
    s = boto3.Session(region_name=region, **cross_credentials.get_response_for_boto3())
    eks = s.client("eks")
    # get cluster details
    cluster = eks.describe_cluster(name=cluster_id)
    certificate_authority_data = cluster["cluster"]["certificateAuthority"]["data"]
    host = cluster["cluster"]["endpoint"]
    name = cluster['cluster']['arn']
    logger.info(f"Retrieved all parameters, external_id: {external_id}.")
    token = get_token(cluster_name=cluster_id, role_arn=iam_role_arn, external_id=external_id)['status']['token']
    config = {
        'certificate_authority_data': certificate_authority_data,
        'host': host,
        'name': name,
        'token': token,
    }
    if return_config:
        return config
    template_path = os.path.join(BASE_DIR)
    loader = FileSystemLoader(template_path)
    env = Environment(loader=loader)
    template = env.get_template('config.yaml.j2')
    template_output = template.render(config)
    rendered_yaml_path = os.path.join(template_path, f'template_{time.time()}.yaml')
    with open(rendered_yaml_path, 'w') as fh:
        fh.write(template_output)
    return rendered_yaml_path
