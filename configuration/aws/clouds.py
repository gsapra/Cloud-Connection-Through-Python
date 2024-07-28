from configuration import get_aws_kube_configuration, get_kube_configuration
from configuration.azure.azure_config import get_azure_kubernetes_config


def _get_configuration(cloud_type):
    if cloud_type == "AWS":
        """
        AWS Kubernetes Configuration
        """
        configuration = get_aws_kube_configuration(
            iam_role_arn="iam_role_arn",
            cluster_id="kube_cluster_name",
            region="region",
            vpc_endpoint_address="get_vpc_endpoint_address" or None,
        )
    elif cloud_type == "GCP":
        """
        GCP Kubernetes Configuration
        """
        configuration = get_kube_configuration(
            project_id="project_id",
            cluster_id="kube_cluster_name",
            zone="zone",
            region="region"
        )
    elif cloud_type == "AZURE":
        configuration = get_azure_kubernetes_config(
            tenant_id="tenant_id",
            client_id="client_id",
            client_secret="client_secret",
            resource_group="resource_group",
            cluster_name="kube_cluster_name",
            subscription_id="subscription_id",
            k8config=True
        )
    return configuration
