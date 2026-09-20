Live demo
https://readytosubmit.vercel.app


# ReadyToSubmit

An eight-screen scholarship document review frontend based on the supplied wireframes. React + Vite, custom responsive CSS, Lucide icons, and on-demand pdf-lib export. Designed for an eventual AWS-backed implementation; no alternative hosting resources were created.

## Run

`npm install` then `npm run dev`. The server listens on port 4173 on the local network; use the Network URL shown by Vite. `npm run build` creates static output in `dist`. `npm test` checks the review and upload validation logic.

## Working features

- Landing page, scholarship search, document upload, detail confirmation, findings, evidence viewer, replacement/recheck, and final summary.
- Local PDF/image preview, drag/drop upload, extension/size validation, remove/replace, manual field entry, source preview zoom, finding filters, and a downloaded PDF review summary.
- Fictional samples exercise name mismatch and ambiguous roll-number findings. A corrected bank sample clears the name issue; a corrected academic sample clears the roll issue.
- Responsive design, keyboard controls, native modal focus trapping, reduced-motion support, and scroll reveals.

## AWS-backed review mode

Set `VITE_REVIEW_API_URL` to the deployed API URL before running or building the frontend. Personal uploads then follow this path:

`Browser → short-lived S3 PUT URL → private S3 object → Textract async analysis → Lambda deterministic checks → existing findings UI/PDF summary`

The SAM stack in `infra/template.yaml` creates a private, encryption-at-rest S3 bucket, an HTTP API + Lambda function, and a DynamoDB review-session store. Objects use a 24-hour lifecycle rule. The Lambda asks Textract for document-specific fields (name, IDs, bank details, marks and roll number), stores Textract confidence/page/bounding-box evidence, and runs the same name and roll-number checks used by the frontend. Replacing a document starts a new extraction job for that document; the latest successful values drive the next review.

Deploy after AWS credentials are available:

`sam build --template-file infra/template.yaml`

`sam deploy --guided --stack-name ready-to-submit --region eu-north-1 --parameter-overrides AllowedOrigin=http://localhost:4173`

Copy the `ApiUrl` output into `.env.local` as `VITE_REVIEW_API_URL=<ApiUrl>` and restart Vite. For a deployed frontend, set `AllowedOrigin` to its exact HTTPS origin and rebuild with the same API URL.

## Honest scope and limitations

This is a hackathon MVP, not an official scholarship service. It has no user account or government-portal affiliation. Access to a review is protected by an unguessable browser-held capability token rather than full authentication; production use needs Cognito or another identity/consent layer, per-user deletion, rate limiting, malware/content scanning, audit logging, and tighter API origin policy. The 24-hour S3 lifecycle is useful for demos but object deletion is not immediate.

Textract results are extraction aids, not facts: users must review the original document and may need to type corrections. The current deterministic rules only flag missing documents, a normalized application/bank name mismatch, and blank/uncertain roll numbers. They do not decide eligibility, validate a current official checklist, verify document authenticity, or submit an application. The SVMCM content and sample values are illustrative; a clear review is never an acceptance guarantee. Google Fonts is requested for typography, but document bytes are sent only to the configured AWS services in live mode.

## Local-only fallback

Without `VITE_REVIEW_API_URL`, the existing frontend behaviour is deliberately preserved: files stay in browser memory and details are manual. This makes the visual demo usable without AWS, while live mode activates private upload and Textract extraction.

The design uses a lightweight CSS perspective treatment for document previews instead of a WebGL canvas. No fabricated statistics, testimonials, acceptance scores, or official audit credentials are shown.
