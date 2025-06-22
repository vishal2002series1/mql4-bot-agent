import boto3
import os
import json

lambda_client = boto3.client('lambda')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def invoke_lambda(function_name, payload):
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',  # synchronous call
        Payload=json.dumps(payload)
    )
    response_payload = json.loads(response['Payload'].read())
    return response_payload

def get_combined_summary(code_analysis_text, trading_analysis_text):
    prompt = (
        "You are an expert trading system analyst. "
        "Given the following two analyses, provide a combined summary highlighting key issues and actionable recommendations.\n\n"
        "Code Analysis:\n"
        f"{code_analysis_text}\n\n"
        "Trading Results Analysis:\n"
        f"{trading_analysis_text}\n\n"
        "Combined Summary:"
    )

    system_prompt = "You are a helpful assistant specialized in trading system analysis."

    body = json.dumps({
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "system": system_prompt,
        "max_tokens": 1000,
        "temperature": 0.5,
        "anthropic_version": "bedrock-2023-05-31"
    })

    response = bedrock_runtime.invoke_model(
        modelId=os.environ.get('BEDROCK_MODEL_ID'),
        body=body,
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def lambda_handler(event, context):
    try:
        # Invoke Code Analysis Agent
        code_response = invoke_lambda('MQL4CodeAnalysisAgent', {})
        code_body = code_response.get('body')
        if isinstance(code_body, str):
            code_analysis_text = code_body
        else:
            code_analysis_text = json.dumps(code_body)

        # Invoke Trading Result Analysis Agent
        trading_response = invoke_lambda('TradingResultAnalysisAgent', {})
        trading_body = trading_response.get('body')
        if isinstance(trading_body, dict):
            # If body is dict with 'summary' key
            trading_analysis_text = trading_body.get('summary', json.dumps(trading_body))
        else:
            trading_analysis_text = trading_body

        # Generate combined summary using Bedrock LLM
        combined_summary = get_combined_summary(code_analysis_text, trading_analysis_text)

        combined_report = {
            'code_analysis': code_analysis_text,
            'trading_analysis': trading_analysis_text,
            'combined_summary': combined_summary
        }

        return {
            'statusCode': 200,
            'body': combined_report
        }

    except Exception as e:
        print(f"Error in coordinator: {e}")
        return {
            'statusCode': 500,
            'body': str(e)
        }