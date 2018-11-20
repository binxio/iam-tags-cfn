# Using IAM Tags

This blog post is an example how to protect your resources created with CloudFormation, and using the recently introduced IAM Tags.

We will create two roles: PurpleRole and RedRole. Both are full admin, except, we don't give them access to shutdown an instance, when the instance doesn't have an equal Team tag.

At this moment we cannot use Conditions for CloudFormation Stack Tags. This probably will be added in the future, so we can not only prevent users of terminating an instance, but also from deleting a Stack they not own.

Also, CloudFormation does not support IAM Tagging yet, so we use a custom resource to create the IAM tags.

This is the CloudFormation Resource to create a Role. Nothing special here.

```yaml
  TeamRedRole:
    Type: AWS::IAM::Role
    Properties: 
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS:
                - !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: sts:AssumeRole
```

Here we use a CloudFormation Custom Resource to add a Tag to the Role.

```yaml
  TeamRedRoleTags:
    Type: Custom::Tags
    Properties:
      ServiceToken:
        !GetAtt Tagging.Arn
      RoleName: !Ref TeamRedRole
      Tags:
        - Key: Team
          Value: Red
```

This Custom Resource Function looks like this. We use python3.7, just because this is a second recently introduced feature.

```python
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
```

Now this is deployed, we can assume one of the new roles. For example: RedRole.

Let's deploy a server, with a tag "Team=Red". We are allowed to terminate this instance.

```yaml
Resources:
  Ec2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0627e141ce928067c
      InstanceType: t2.micro
      Tags:
        - Key: Team
          Value: Red
```

Now try to stop the instance, because the resource has the tag "Team=Red" we are allowed to stop the instance.

Now switch to the PurpleRole and try to terminate the instance. It's denied. Also try to change the tag, it's denied either.

In this case you can assume both roles, but it's a good practice to create a different role for each team. They can have the same ManagedPolicy, but still have access to only their Ec2 Resources.

When switching back to your admin account (not using the PurpleRole or RedRole), you are allowed to update the tag, so do this. Just do this to check out the third cool feature: Drift Detection. Now go to CloudFormation, click on the Stack of this instance and Click Drift Detection. Now view the details and visisble is the Tag has been changed manually. 

## Conclusion

We have learned:

* How to use IAM tagging to protect our deployed assets
* To use python3.7 for our CloudFormation Custom Resource (launched November 11)
* Looked into Drift Detection

In the future we will add CloudFormation protection, once this is supported (or we found a work around). And we will add more examples besides Ec2 to make it more useful. 
