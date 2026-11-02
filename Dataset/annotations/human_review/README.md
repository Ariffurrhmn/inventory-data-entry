# Human annotation reviews

The local app in services/annotation_portal/ stores real reviewer saves in reviews.sqlite3. Every save appends a revision, with the latest revision defining current status. Use the app's Export reviews button for portable JSON and Export all text to include existing OCR and references. Unsaved browser drafts are separate from this database.

No records have been automatically declared human verified. Verification requires a reviewer name and explicit image/text/class confirmation. Raw images, original/corrected reference editions and classifier splits are preserved. These saved reviews do not modify training labels or retrain a model; adopting reviewed annotations is a later explicit versioned step.

For backups, keep the database when the app is stopped and retain JSON exports. Browser UI test records live separately in services/annotation_portal/.runtime/qa/ and are not human ground truth.

This store now includes user-authorized AI visual reviews with reviewer_type=ai, human_verified=false and status=needs_review, alongside person-entered drafts. The human_review folder name does not imply that every stored revision was authored or verified by a human. Review provenance is explicit in each AI record; older person-entered portal records may have no reviewer_type field.
