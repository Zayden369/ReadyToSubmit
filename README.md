# ReadyToSubmit

An eight-screen scholarship document review frontend based on the supplied wireframes. React + Vite, custom responsive CSS, Lucide icons, and on-demand pdf-lib export. Designed for an eventual AWS-backed implementation; no alternative hosting resources were created.

## Run

`npm install` then `npm run dev`. The server listens on port 4173 on the local network; use the Network URL shown by Vite. `npm run build` creates static output in `dist`. `npm test` checks the review and upload validation logic.

## Working features

- Landing page, scholarship search, document upload, detail confirmation, findings, evidence viewer, replacement/recheck, and final summary.
- Local PDF/image preview, drag/drop upload, extension/size validation, remove/replace, manual field entry, source preview zoom, finding filters, and a downloaded PDF review summary.
- Fictional samples exercise name mismatch and ambiguous roll-number findings. A corrected bank sample clears the name issue; a corrected academic sample clears the roll issue.
- Responsive design, keyboard controls, native modal focus trapping, reduced-motion support, and scroll reveals.

## Honest scope

This is a frontend prototype, not an operational scholarship verification service. Uploaded files stay in tab memory and are not extracted or authenticated. No AWS calls, accounts, persistence, official checklist validation, or automatic submission exist. The SVMCM checklist, document limits, sample values, and source highlights are demonstration content, not current scheme requirements. Personal files must be manually transcribed; sample evidence is explicitly labelled fictional. A clear review is not an acceptance or eligibility decision. Google Fonts is requested for typography, but document data is never sent there.

## AWS integration boundary

Replace manual/sample ingestion with an authenticated upload API, private S3 objects and Textract extraction (retaining page/box coordinates). Keep deterministic checks in `src/review.js`; supply a verified, versioned checklist. Add Bedrock only for evidence-grounded explanations. Before enabling real submissions, implement per-user authorization, deletion and retention, file-content validation, error handling, and extraction accuracy evaluation. Update privacy copy to reflect server-side processing.

The design uses a lightweight CSS perspective treatment for document previews instead of a WebGL canvas. No fabricated statistics, testimonials, acceptance scores, or official audit credentials are shown.
