import base64
import logging
from tempfile import NamedTemporaryFile

import boto3
import google.auth
import google.auth.transport.requests
from configuration.aws.aws_assume_role_manager import AWSAssumeRoleManager
from awscli.customizations.eks.get_token import TokenGenerator, TOKEN_EXPIRATION_MINS, K8S_AWS_ID_HEADER
from datetime import datetime, timedelta
from botocore import session
from google.cloud import container_v1
from kubernetes import client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class STSClientFactory(object):
    def __init__(self, session):
        self._session = session

    def get_sts_client(self, region_name=None, role_arn=None, external_id=None):
        client_kwargs = {'region_name': region_name}
        if role_arn is not None:
            creds = self._get_role_credentials(region_name, role_arn, external_id)
            client_kwargs['aws_access_key_id'] = creds['AccessKeyId']
            client_kwargs['aws_secret_access_key'] = creds['SecretAccessKey']
            client_kwargs['aws_session_token'] = creds['SessionToken']
        sts = self._session.create_client('sts', **client_kwargs)
        self._register_k8s_aws_id_handlers(sts)
        return sts

    def _get_role_credentials(self, region_name, role_arn, external_id):
        sts = self._session.create_client('sts', region_name)
        if external_id:
            logger.info(f'_get_role_credentials with {external_id}')
            return sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName='EKSGetTokenAuth',
                ExternalId=external_id
            )['Credentials']
        else:
            logger.info(f'_get_role_credentials without {external_id}')
            return sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName='EKSGetTokenAuth'
            )['Credentials']

    def _register_k8s_aws_id_handlers(self, sts_client):
        sts_client.meta.events.register(
            'provide-client-params.sts.GetCallerIdentity',
            self._retrieve_k8s_aws_id,
        )
        sts_client.meta.events.register(
            'before-sign.sts.GetCallerIdentity',
            self._inject_k8s_aws_id_header,
        )

    def _retrieve_k8s_aws_id(self, params, context, **kwargs):
        if K8S_AWS_ID_HEADER in params:
            context[K8S_AWS_ID_HEADER] = params.pop(K8S_AWS_ID_HEADER)

    def _inject_k8s_aws_id_header(self, request, **kwargs):
        if K8S_AWS_ID_HEADER in request.context:
            request.headers[K8S_AWS_ID_HEADER] = request.context[K8S_AWS_ID_HEADER]


def get_kube_configuration(project_id: str, cluster_id: str, zone=None, region=None, return_configuration_dict=False):
    location = region
    if zone:
        location = zone
    if not location:
        raise Exception('Please specify zone or region.')
    logger.info('Attempting to init k8s client from cluster response.')
    container_client = container_v1.ClusterManagerClient()
    logger.info(f'Attempting to get cluster {cluster_id} in project {project_id} in region/zone {location}.')
    response = container_client.get_cluster(name=f"/{project_id}/locations/{location}/clusters/{cluster_id}")
    creds, projects = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    certificate_authority_data = response.master_auth.cluster_ca_certificate
    name = f'gke_{project_id}_{location}_{cluster_id}'
    host = f'https://{response.endpoint}'
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    token = creds.token
    configuration = client.Configuration()
    configuration.host = host
    config = {
        'certificate_authority_data': certificate_authority_data,
        'host': host,
        'name': name,
        'token': token,
    }
    if return_configuration_dict:
        return config
    with NamedTemporaryFile(delete=False) as ca_cert:
        ca_cert.write(
            base64.b64decode(certificate_authority_data)
        )
    configuration.ssl_ca_cert = ca_cert.name
    configuration.api_key_prefix['authorization'] = 'Bearer'
    configuration.api_key['authorization'] = token
    logger.info(f'Kube configuration completed for project id {project_id}.')
    return configuration


def get_expiration_time():
    token_expiration = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MINS)
    return token_expiration.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_token(cluster_name: str, role_arn: str = None, external_id=None) -> dict:
    work_session = session.get_session()
    client_factory = STSClientFactory(work_session)
    sts_client = client_factory.get_sts_client(role_arn=role_arn, external_id=external_id)
    _stsClient = boto3.client('sts')
    token = TokenGenerator(sts_client).get_token(cluster_name)
    return {
        "kind": "ExecCredential",
        "apiVersion": "client.authentication.k8s.io/v1alpha1",
        "spec": {},
        "status": {
            "expirationTimestamp": get_expiration_time(),
            "token": token
        }
    }


def get_aws_kube_configuration(
        iam_role_arn: str,
        cluster_id: str,
        region,
        external_id=None,
        return_configuration_dict=False,
        vpc_endpoint_address=None
):
    logger.info(f'Attempting to init k8s client from cluster response. external_id {external_id}.')
    cross_credentials = AWSAssumeRoleManager(role_arn=iam_role_arn, external_id=external_id)
    s = boto3.Session(region_name=region, **cross_credentials.get_response_for_boto3())
    eks = s.client("eks")
    # get cluster details
    cluster = eks.describe_cluster(name=cluster_id)
    certificate_authority_data = cluster["cluster"]["certificateAuthority"]["data"]

    """
    For private VPC use vpc_endpoint_address as a host instead of EKS cluster host.
    """
    if not vpc_endpoint_address:
        host = cluster["cluster"]["endpoint"]
    else:
        logger.info(f'Found vpc_endpoint_address, using it as host in K8 config.')
        host = vpc_endpoint_address
    name = cluster['cluster']['arn']
    logger.info(f"Retrieved all parameters, external_id: {external_id}.")
    token = get_token(cluster_name=cluster_id, role_arn=iam_role_arn, external_id=external_id)['status']['token']
    configuration = client.Configuration()
    configuration.host = host

    config = {
        'certificate_authority_data': certificate_authority_data,
        'host': host,
        'name': name,
        'token': token,
    }
    if return_configuration_dict:
        return config
    with NamedTemporaryFile(delete=False) as ca_cert:
        ca_cert.write(
            base64.b64decode(certificate_authority_data)
        )
    configuration.ssl_ca_cert = ca_cert.name
    configuration.api_key_prefix['authorization'] = 'Bearer'
    if vpc_endpoint_address:
        configuration.verify_ssl = False
    configuration.api_key['authorization'] = token
    return configuration
