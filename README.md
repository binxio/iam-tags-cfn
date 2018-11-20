# Using IAM Tags

This blog post is an example how to protect CloudFormation create/update stacks and the resources belonging to the stack. 

Situation: you have 2 teams working on the same AWS account. Team Purple and Team Red. They get their own Role, so PurpleRole and RedRole. Both these roles got a IAM tag: Team=Red and Team=Purple. They are allowed to create stacks, and for some resources we want to enforce the use of Tags. Team Purple can only create Ec2 Instances with tag Team=Purple. Otherwise the creation of the stack will fail. Once the Stack is deployed, only the PurpleRole is able to stop the instance. Team Red is not able to stop the instance.

In case you want to protect creating, updating or deleting CloudFormation stacks, you should use a CloudFormation Role and give the Role (Purple and Red) different CloudFormation Roles to pass. When the Team Red created a CloudFormation Stack with Role CfnRed, team Purple is not allowed to update or delete the stack because they are not allowed to pass the role.

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

Here we use a CloudFormation Custom Resource to add a Tag to the Role. We need a Custom Resource, because IAM tagging is not yet supported in CloudFormation. This will probably be available soon, so we can remove the Custom Resource.

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

This is the Policy. As you can see I use the NotAction to give full admin permissions, except for 3 actions. So a team Red member can create a stack, but he must add a tag Team=Red. Otherwise the creation will fail. When de deployment is successful, the team Read member can only stop the machine deployed with the Tag Team=Red. And the user is not able to change the Tag to for example Team=Purple, or change Tags part of other stacks.

```yaml
  FullAccessManagedPolicy:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - 
            Sid: "AllowEverythingExceptForExplicitAllow"
            Effect: "Allow"
            NotAction:
              - "ec2:StopInstances"
              - "ec2:CreateTags"
              - "ec2:DeleteTags"
            Resource: "*"
          - 
            Sid: "ExplicitAllowWithConditionResourceTag"
            Effect: "Allow"
            Action:
              - "ec2:StopInstances"
              - "ec2:CreateTags"
              - "ec2:DeleteTags"
            Resource: "*"
            Condition:
              StringEquals:
                "ec2:ResourceTag/Team": "${aws:PrincipalTag/Team}"
          - 
            Sid: "ExplicitAllowWithConditionRequestTag"
            Effect: "Allow"
            Action:
              - "ec2:StopInstances"
              - "ec2:CreateTags"
              - "ec2:DeleteTags"
            Resource: "*"
            Condition:
              StringEquals:
                "aws:RequestTag/Team": "${aws:PrincipalTag/Team}"
      Roles:
        - !Ref TeamRedRole
        - !Ref TeamPurpleRole
```

Now this is deployed, we can assume one of the new roles. For example: RedRole.

Let's deploy a server, with a CloudFormation tag "Team=Red". All resources supporting Tags will get this Tag too. For example the Ec2 Instance.

```yaml
Resources:
  Ec2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0627e141ce928067c
      InstanceType: t2.micro
```

Or you can deploy the instance with explicitly configured Tags. The result will be the same.

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

Clean up by deleting the three stacks.

## Conclusion

We have learned:

* How to use IAM tagging to protect our deployed resources, in this example: Ec2 instances
* To use python3.7 for our CloudFormation Custom Resource (launched November 11)
* Looked into Drift Detection

In the future we will add CloudFormation protection, once this [is supported](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_tags.html#access_tags_control-tag-keys) (or we found a work around). And we will add more examples besides EC2 to make it more useful. Tags on a Stack are automatically set on every Resource part of the Stack, making it very easy to extend this solution. So a RedRole can only create CloudFormation stacks with a tag Team=Red and because the resources get the tag Team=Red too, all resources can easily be protected. This was actually the reason I started this expiriment, but found out CloudFormation tags are not supported in IAM conditions.