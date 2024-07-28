import boto3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class AWSAssumeRoleManager:
    """
    Get AWS Access Key, Secret Key and Session Token based on role name.
    """

    def __init__(self, role_arn, external_id=None):
        logger.info(f'AWSAssumeRoleManager: Found external id to {external_id}')
        __stsClient = boto3.client('sts')
        if external_id:
            logger.info(f'AWSAssumeRoleManager: Assuming using external id.')
            __assumed_role_object = __stsClient.assume_role(
                RoleArn=role_arn,
                RoleSessionName="AssumeRoleSession",
                ExternalId=external_id
            )
        else:
            logger.info(f'AWSAssumeRoleManager: Assuming using without external id.')
            __assumed_role_object = __stsClient.assume_role(
                RoleArn=role_arn,
                RoleSessionName="AssumeRoleSession",
            )
        self.__credentials = __assumed_role_object['Credentials']

    @property
    def get_access_key(self) -> str:
        """
        Returns AccessKeyId
        """
        return self.__credentials['AccessKeyId']

    @property
    def get_secret_key(self) -> str:
        """
        Returns SecretAccessKey
        """
        return self.__credentials['SecretAccessKey']

    @property
    def get_session_token(self) -> str:
        """
        Returns SessionToken
        """
        return self.__credentials['SessionToken']

    def get_response_for_boto3(self) -> dict:
        """
        Dict with keys: aws_access_key_id, aws_secret_access_key, aws_session_token
        """
        return dict(
            aws_access_key_id=self.get_access_key,
            aws_secret_access_key=self.get_secret_key,
            aws_session_token=self.get_session_token
        )
