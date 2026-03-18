import boto3
import os

def handler(event, context):
    action = event.get('action') # 'START' or 'STOP'
    ec2 = boto3.client('ec2')
    region = os.environ.get('AWS_REGION', 'eu-north-1')
    
    # Filter for instances tagged with Environment=staging
    filters = [
        {
            'Name': 'tag:Environment',
            'Values': ['staging']
        }
    ]
    
    # Get instance IDs
    response = ec2.describe_instances(Filters=filters)
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
            
    if not instance_ids:
        print("No staging instances found to manage.")
        return {"status": "no_instances_found"}
        
    if action == 'START':
        ec2.start_instances(InstanceIds=instance_ids)
        print(f"Started instances: {instance_ids}")
    elif action == 'STOP':
        ec2.stop_instances(InstanceIds=instance_ids)
        print(f"Stopped instances: {instance_ids}")
    else:
        print(f"Invalid action requested: {action}")
        return {"status": "error", "message": f"Invalid action: {action}"}
        
    return {
        "status": "success",
        "action": action,
        "instances": instance_ids
    }
