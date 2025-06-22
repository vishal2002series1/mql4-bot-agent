import boto3
import os
import json

s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def lambda_handler(event, context):
    bucket = os.environ.get('BUCKET_NAME')
    key = os.environ.get('MQL4_CODE_FILE')
    model_id = os.environ.get('BEDROCK_MODEL_ID')

    try:
        # Read MQL4 code from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        code_content = response['Body'].read().decode('utf-8')

        print("MQL4 Code read from S3 successfully.")

        # Prepare prompt and system message for Bedrock
        prompt = f"Analyze the following MQL4 Expert Advisor code and provide suggestions to maximize profit:\n\n{code_content}"
        system_prompt = "You are a helpful assistant specialized in MQL4 trading bots."

        # Prepare request body
        body = json.dumps({
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "system": system_prompt,
            "max_tokens": 512,
            "temperature": 0.5,
            "anthropic_version": "bedrock-2023-05-31"
        })

        # Call Bedrock runtime invoke_model API
        bedrock_response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(bedrock_response['body'].read())
        analysis_text = response_body['content'][0]['text']

        print("Bedrock LLM response:")
        print(analysis_text)

        return {
            'statusCode': 200,
            'body': analysis_text
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': str(e)
        }