import logging
import boto3
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('iam')

def lambda_handler(event, context):

    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            response = client.tag_role(
                RoleName=event['ResourceProperties']['RoleName'],
                Tags=event['ResourceProperties']['Tags']
            )
        elif event['RequestType'] == 'Delete':
            response = client.tag_role(
                RoleName=event['ResourceProperties']['RoleName'],
                Tags=event['ResourceProperties']['Tags']
            )
        logger.info(response)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})

    except Exception as e:
        logger.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, {})