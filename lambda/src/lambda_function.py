import boto3
import json
import datetime
import pandas as pd
from io import StringIO
import re
from datetime import datetime


# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
glue_client = boto3.client('glue')

# Replace with your resource names
TABLE_NAME = 'StateTable'
BUCKET_NAME = 'certifications-dinesh-logs'
GLUE_JOB_NAME = 'certificates-log-pipeline-glue-job'

def lambda_handler(event, context):
    try:
        # Initialize DynamoDB table
        table = dynamodb.Table(TABLE_NAME)
        
        # Fetch list of objects in the S3 bucket
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            return {
                'statusCode': 200,
                'body': json.dumps('No files in the bucket.')
            }

        concatenated_data = ""
        
        for obj in response['Contents']:
            # Get the file name
            file_name = obj['Key']
            # Convert the file name into a string (already a string, but this step ensures it)
            file_name_str = str(file_name)
            # Check if the file already exists in DynamoDB
            dynamo_response = table.get_item(Key={'logfile': file_name_str})
            if 'Item' not in dynamo_response:
                # File not in DynamoDB, add it
                timestamp = datetime.utcnow().isoformat()
                now = datetime.now()
                table.put_item(
                    Item={
                        'logfile': file_name_str,  # Match partition key name with table schema
                        'timestamp': timestamp
                    }
                )
                # Read the content of the file and concatenate
                file_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_name_str)
                file_data = file_obj['Body'].read().decode('utf-8')
                concatenated_data += file_data + "\n"
        
        logs = concatenated_data.split('TLSv1.3 - -')
        new_data = []
        for l in logs[:-1]:    
            ip_address = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', l)
            date = re.search(r'(\d{1,2}/[A-Za-z]+/\d{4})', l)
            certificate = re.search(r'JPMC|AWSDEA|databricks', l)
            request = re.search(r'REST\.\S*', l)
            request_code = re.search(r'\s\d{3}\s', l)

            if ip_address and date and certificate and request and request_code:
                new_log = {
                    'ip_address': ip_address.group(),
                    'certificate': certificate.group(),
                    'date': datetime.strptime(date.group(), "%d/%b/%Y").strftime("%Y-%m-%d"),
                    'request': request.group(),
                    'request_code': int(request_code.group().strip())
                }
                new_data.append(new_log)

        df = pd.DataFrame(new_data)
        print(df.head(20))
        # Convert DataFrame to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        # S3 bucket and file details
        bucket_name = 'certifications-dinesh-temp-logs'
        file_name = 'sample.csv'
        
        # Upload the CSV to S3
        # s3_client = boto3.client('s3')
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=file_name,
                Body=csv_buffer.getvalue()
            )
            print(f'Successfully uploaded {file_name} to {bucket_name}')
        except Exception as e:
             print(f'Error uploading to S3: {str(e)}')

        #calling function to update the accesslogs file
        put_data_to_accesslogs_file(df)

        #If there's concatenated data, invoke the Glue job
        if concatenated_data:
            glue_response = glue_client.start_job_run(
                JobName=GLUE_JOB_NAME
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Processed files and triggered Glue job successfully.',
                    'glue_job_run_id': glue_response['JobRunId']
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps('No new files to process.')
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def put_data_to_accesslogs_file(df):
    print('writing data to accesslogs file')
    bucket_name = 'certifications-dinesh'
    file_name = 'accesslogs.csv'
    try:
        # Check if the file exists in S3
        existing_file_obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    
        # Read the existing file into a DataFrame
        existing_csv = existing_file_obj['Body'].read().decode('utf-8')
        existing_df = pd.read_csv(StringIO(existing_csv))
    
        # Append the new data to the existing DataFrame
        updated_df = pd.concat([existing_df, df], ignore_index=True)
    except s3_client.exceptions.NoSuchKey:
        # If the file doesn't exist, start with the new data
        print(f"{file_name} does not exist. Creating a new file.")
        updated_df = df

    # Write the updated DataFrame back to S3
    csv_buffer = StringIO()
    updated_df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())
    print('updated accesslogs file')