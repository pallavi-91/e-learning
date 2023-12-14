import boto3
from django.conf import settings
from botocore.exceptions import ClientError

session = boto3.Session(aws_access_key_id= settings.AWS_ACCESS_KEY_ID, 
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME)
# create an SNS client
sns_client = session.client('sns')
ses_client = session.client('ses')
try:
    # create the SMTP configuration set
    configuration_set_name = 'MySMTPConfigurationSet'
    response = ses_client.create_configuration_set(
        ConfigurationSet={
            'Name': configuration_set_name,
        }
    )
except ClientError as e:
    if e.response['Error']['Code'] == 'ConfigurationSetAlreadyExistsException':
        print('SMTP Configuration Set already exists:', configuration_set_name)
    else:
        print('Error:', e)

# retrieve the configuration set name from the response
# set the SMTP configuration set name

smtp_configuration_set_name = configuration_set_name

response = sns_client.create_topic(
    Name='CourseAnnouncement',
    Attributes={
        'DisplayName': 'Course Announcement'
    },
    Tags=[
        {
            'Key': 'Course',
            'Value': 'Announcement'
        },
    ],
    # DataProtectionPolicy='string'
)

# set the topic ARN
mail_topic_arn = response.get('TopicArn')

# set the message and subject
message = 'Hello, this is a test email'
subject = 'Test Email'
to_email = 'python.devo@gmail.com'

# subscribe an email address to the topic

# sns_client.subscribe(
#     TopicArn=mail_topic_arn,
#     Protocol='email',
#     Endpoint=to_email
# )

# publish the message using the SMTP configuration set
response = sns_client.publish(
    TopicArn=mail_topic_arn,
    Subject=subject,
    Message=message
)

# print the response
print(response)