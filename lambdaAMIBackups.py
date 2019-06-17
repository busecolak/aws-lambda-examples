import boto3
import datetime 

client = boto3.client('ec2', region_name='eu-central-1')
ec2 = boto3.resource('ec2', region_name='eu-central-1')

create_time = datetime.datetime.now()
create_fmt = create_time.strftime('%d-%m-%Y')

def lambda_handler(event, context):
    
    print "Creating new AMIs"
    createAMIs()
    
    print "Deleting older AMIs"
    deleteAMIs()
    
    
def createAMIs():
    
    instance_filters = [ {'Name': 'tag-key', 'Values': ['Backup']}, {'Name': 'instance-state-name', 'Values': ['running']} ]

    instances = ec2.instances.filter(Filters=instance_filters)
    print "Found %d instances that need backing up" % len(list(instances.all()))
    
    for instance in instances:
        
        instanceName = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Name']
        instanceID = instance.id
        print "FOUND INSTANCE " + instanceID + " - " + instanceName[0] 
        
        print "Creating image for instance " + instanceID + " on " + create_fmt
        AMIid = client.create_image(InstanceId= instanceID, Name="Lambda - " + instanceName[0] + " - " + " From " + create_fmt, Description="Lambda created AMI of instance " + instanceID, NoReboot=True, DryRun=False)
        print AMIid
        
def deleteAMIs():
    
    images = ec2.images.filter(Owners=["748784772711"])
    for image in images:
        
        if image.name.startswith('Lambda - ') and not image.name.endswith(create_fmt):
            
            imageID = image.id
            print "FOUND IMAGE " + imageID + " - " + image.name + " : " + image.description
            
            snapshotList = []
            for bdm in image.block_device_mappings:
                snapshotID = bdm["Ebs"]["SnapshotId"]
                snapshotList.append(snapshotID)
                print "FOUND SNAPSHOT " + snapshotID + " associated with an AMI " + imageID
            
            print "Deregistering image %s" % image
            response = client.deregister_image(DryRun=False,ImageId=imageID)
            print response
            
            for snapshotID in snapshotList:
                print "Deleting snapshot " + snapshotID
                response = client.delete_snapshot(SnapshotId=snapshotID)
                print response
            