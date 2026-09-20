# Security and privacy

The planned SAM stack uses a private S3 bucket with Block Public Access, SSE-S3 encryption, restrictive Lambda IAM and a one-day object lifecycle. Raw bucket URLs are never returned: uploads use 10-minute presigned PUT URLs. Filenames are sanitized and object keys are UUID-scoped per review.

The MVP uses a browser-held opaque review token. It prevents casual cross-session access but is **not a production identity system**. Before handling real student documents, add user authentication (for example Cognito), token rotation, per-user authorization, file signature/content scanning, deletion APIs, audit controls and restrictive production CORS. Lambda returns generic error text and should never log OCR text, bank details or document bytes.

CloudShell deployment is currently blocked by the AWS account provisioning message shown in the Console; no AWS resources have been created by this repository yet.
