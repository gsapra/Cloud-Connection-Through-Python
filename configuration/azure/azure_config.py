import base64
from pathlib import Path
from tempfile import NamedTemporaryFile
import requests
import logging
import kubernetes.client  # Update these to auth as your Azure AD App

from azure.mgmt.containerservice import ContainerServiceClient
from azure.identity import ClientSecretCredential
import yaml

BASE_DIR = Path(__file__).resolve().parent

def get_oauth_token(resource, tenant_id, client_id, client_secret):
    login_url = 'https://login.microsoftonline.com/%s/oauth2/token' % tenant_id
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'Content-Type': 'x-www-form-urlencoded',
        'resource': resource
    }
    response = requests.post(login_url, data=payload, verify=False).json()
    logging.info('Got OAuth token for AKS')
    return response['access_token']


def get_azure_kubernetes_config(
        tenant_id: str,
        client_id: str,
        client_secret: str,
        resource_group: str,
        cluster_name: str,
        subscription_id: str,
        k8config=True
):
    logging.info('Retrieving cluster endpoint…')
    token = get_oauth_token(
        resource='https://management.azure.com',
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    mgmt_url = 'https://management.azure.com/subscriptions/%s' % subscription_id
    mgmt_url += '/resourceGroups/%s' % resource_group
    mgmt_url += '/providers/Microsoft.ContainerService/managedClusters/%s' % cluster_name
    cluster = requests.get(
        mgmt_url,
        params={'api-version': '2022-11-01', 'PropertyName': 'properties.certificate'},
        headers={'Authorization': 'Bearer %s' % token}
    ).json()

    props = cluster['properties']
    fqdn = props.get('fqdn') or props.get('privateFQDN')
    api_endpoint = 'https://%s:443' % fqdn
    logging.info('Got cluster endpoint', endpoint=api_endpoint)

    logging.info('Requesting OAuth token for AKS…')
    # magic resource ID that works for all AKS clusters
    AKS_RESOURCE_ID = '6dae42f8-4368-4678-94ff-3960e28e3630'
    api_token = get_oauth_token(
        resource=AKS_RESOURCE_ID,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    client = ContainerServiceClient(
        credential=credential,
        subscription_id=subscription_id
    )

    result = client.managed_clusters.list_cluster_user_credentials(
        resource_group, cluster_name
    ).kubeconfigs[0]
    kubeconfig: str = result.value.decode("utf-8")
    d = yaml.safe_load(kubeconfig)
    cert = d.get('clusters')[0].get('cluster').get('certificate-authority-data')
    server = d.get('clusters')[0].get('cluster').get('server')
    cluster_name = d.get('clusters')[0].get('name')
    user = f'clusterUser_{resource_group}_{cluster_name}'
    with NamedTemporaryFile(delete=False) as ca_cert:
        ca_cert.write(
            base64.b64decode(cert)
        )
    logging.info('Building K8s API client')
    configuration = kubernetes.client.Configuration()
    configuration.api_key['authorization'] = api_token
    configuration.api_key_prefix['authorization'] = 'Bearer'
    configuration.host = api_endpoint
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = ca_cert.name
    config={
            'certificate_authority_data': cert,
            'host': server,
            'user_name': user,
            'name': cluster_name,
            'token': api_token,
        }
    if k8config:
        return configuration
    else:
        return config
