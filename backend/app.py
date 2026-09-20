import boto3
import hashlib
import json
import os
import re
import time
import uuid

s3 = boto3.client('s3')
textract = boto3.client('textract')
table = boto3.resource('dynamodb').Table(os.environ['REVIEWS_TABLE'])
bucket = os.environ['DOCUMENT_BUCKET']
origin = os.environ.get('ALLOWED_ORIGIN', '*')
allowed = {'application': {'application/pdf'}, 'bank': {'application/pdf', 'image/jpeg', 'image/png'}, 'academic': {'application/pdf'}}

def reply(status, value):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Headers': 'content-type,x-review-token', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'}, 'body': json.dumps(value)}

def payload(event):
    try: return json.loads(event.get('body') or '{}')
    except json.JSONDecodeError as exc: raise ValueError('Request body must be JSON.') from exc

def route_id(event): return (event.get('pathParameters') or {}).get('reviewId')
def token(event):
    headers = event.get('headers') or {}
    return headers.get('x-review-token') or headers.get('X-Review-Token')
def hashed(value): return hashlib.sha256(value.encode()).hexdigest()
def save(item): table.put_item(Item=item)
def safe_name(name): return re.sub(r'[^A-Za-z0-9._-]', '_', name or 'document')[-120:]

def get_review(event):
    item = table.get_item(Key={'reviewId': route_id(event)}).get('Item')
    if not item or not token(event) or item.get('tokenHash') != hashed(token(event)):
        raise PermissionError('This review session is unavailable. Start a new review.')
    return item

def query_set(kind):
    shared = [{'Text': 'What is the full name of the applicant?', 'Alias': 'name'}]
    specific = {'application': [{'Text': 'What is the application ID or application number?', 'Alias': 'applicationId'}], 'bank': [{'Text': 'What is the account number?', 'Alias': 'account'}, {'Text': 'What is the IFSC code?', 'Alias': 'ifsc'}], 'academic': [{'Text': 'What is the roll number?', 'Alias': 'roll'}, {'Text': 'What is the marks percentage or percentage obtained?', 'Alias': 'marks'}]}
    return shared + specific[kind]

def unpack(blocks):
    fields, evidence = {}, {}
    for block in blocks:
        if block.get('BlockType') == 'QUERY_RESULT' and block.get('Text') and block.get('Query', {}).get('Alias'):
            alias = block['Query']['Alias']
            fields[alias] = block['Text'].strip()
            evidence[alias] = {'page': block.get('Page', 1), 'confidence': round(block.get('Confidence', 0), 1), 'box': block.get('Geometry', {}).get('BoundingBox', {})}
    return fields, evidence

def check(documents, fields):
    result = []
    for kind in ('application', 'bank', 'academic'):
        if kind not in documents: result.append({'id': 'missing-' + kind, 'type': 'Documents', 'title': kind.title() + ' is missing', 'doc': kind, 'status': 'attention', 'description': 'Upload this required document before submitting.'})
    normal = lambda value: re.sub(r'[.]', '', (value or '').lower()).strip()
    if documents.get('application') and documents.get('bank') and fields.get('applicationName') and fields.get('bankName') and normal(fields['applicationName']) != normal(fields['bankName']):
        result.append({'id': 'name', 'type': 'Name consistency', 'title': 'A small difference. Worth a second look.', 'doc': 'bank', 'status': 'attention', 'description': 'The name in the bank document differs from the application. Check the originals before submitting.'})
    if documents.get('academic') and (not fields.get('roll') or '?' in fields.get('roll', '')):
        result.append({'id': 'roll', 'type': 'Legibility', 'title': 'One digit needs your eyes.', 'doc': 'academic', 'status': 'review', 'description': 'Please read and confirm the roll number on the original marksheet.'})
    return result

def hydrate(item):
    changed = False
    for kind, document in item.get('documents', {}).items():
        if document.get('status') != 'PROCESSING': continue
        result = textract.get_document_analysis(JobId=document['jobId'], MaxResults=1000)
        if result['JobStatus'] == 'SUCCEEDED':
            blocks, next_token = result.get('Blocks', []), result.get('NextToken')
            while next_token:
                page = textract.get_document_analysis(JobId=document['jobId'], MaxResults=1000, NextToken=next_token)
                blocks.extend(page.get('Blocks', [])); next_token = page.get('NextToken')
            extracted, evidence = unpack(blocks)
            document.update({'status': 'SUCCEEDED', 'answers': extracted, 'evidence': evidence}); changed = True
        elif result['JobStatus'] in ('FAILED', 'PARTIAL_SUCCESS'):
            document.update({'status': result['JobStatus'], 'error': result.get('StatusMessage', 'Textract could not finish this document.')}); changed = True
    if changed:
        mapping = {'application': {'name': 'applicationName', 'applicationId': 'applicationId'}, 'bank': {'name': 'bankName', 'account': 'account', 'ifsc': 'ifsc'}, 'academic': {'name': 'academicName', 'roll': 'roll', 'marks': 'marks'}}
        fields = item.get('fields', {})
        for kind, document in item['documents'].items():
            for key, destination in mapping[kind].items():
                if document.get('answers', {}).get(key): fields[destination] = document['answers'][key]
        item['fields'] = fields; item['findings'] = check(item['documents'], fields); item['updatedAt'] = int(time.time()); save(item)
    return item

def present(item):
    item = hydrate(item)
    return {'reviewId': item['reviewId'], 'documents': item.get('documents', {}), 'fields': item.get('fields', {}), 'findings': item.get('findings', []), 'updatedAt': item.get('updatedAt')}

def handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod')
    path = event.get('rawPath') or event.get('path', '')
    if method == 'OPTIONS': return reply(204, {})
    try:
        if method == 'POST' and path.endswith('/reviews'):
            review_id, review_token = str(uuid.uuid4()), str(uuid.uuid4()) + str(uuid.uuid4())
            save({'reviewId': review_id, 'tokenHash': hashed(review_token), 'createdAt': int(time.time()), 'updatedAt': int(time.time()), 'documents': {}, 'fields': {}, 'findings': []})
            return reply(201, {'reviewId': review_id, 'reviewToken': review_token})
        item = get_review(event)
        if method == 'GET': return reply(200, present(item))
        data = payload(event)
        if path.endswith('/upload-url'):
            kind, content_type, size = data.get('type'), data.get('contentType'), int(data.get('size', 0))
            if kind not in allowed or content_type not in allowed[kind] or size <= 0 or size > (2 if kind == 'bank' else 5) * 1024 * 1024: return reply(400, {'message': 'Unsupported document, MIME type, or file size.'})
            key = f"reviews/{item['reviewId']}/{kind}/{uuid.uuid4()}-{safe_name(data.get('filename'))}"
            url = s3.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': key, 'ContentType': content_type, 'ServerSideEncryption': 'AES256'}, ExpiresIn=600)
            return reply(200, {'uploadUrl': url, 'key': key})
        if '/documents/' in path and path.endswith('/process'):
            kind, key = (event.get('pathParameters') or {}).get('type'), data.get('key')
            if kind not in allowed or not key or not key.startswith(f"reviews/{item['reviewId']}/{kind}/"): return reply(400, {'message': 'Invalid document reference.'})
            s3.head_object(Bucket=bucket, Key=key)
            job = textract.start_document_analysis(DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}}, FeatureTypes=['FORMS', 'QUERIES'], QueriesConfig={'Queries': query_set(kind)})
            item.setdefault('documents', {})[kind] = {'key': key, 'name': safe_name(data.get('filename')), 'contentType': data.get('contentType'), 'status': 'PROCESSING', 'jobId': job['JobId'], 'uploadedAt': int(time.time())}
            item['updatedAt'] = int(time.time()); save(item); return reply(202, {'status': 'PROCESSING', 'reviewId': item['reviewId']})
        if path.endswith('/recheck'):
            item['findings'] = check(item.get('documents', {}), item.get('fields', {})); item['updatedAt'] = int(time.time()); save(item); return reply(200, present(item))
        return reply(404, {'message': 'Route not found.'})
    except PermissionError as error: return reply(401, {'message': str(error)})
    except ValueError as error: return reply(400, {'message': str(error)})
    except Exception as error:
        print(repr(error)); return reply(500, {'message': 'Unable to process this document right now.'})
