import { apiFetch } from "./client";

export function listReceipts() {
  return apiFetch("/receipts");
}

export function getReceipt(receiptId) {
  return apiFetch(`/receipts/${receiptId}`);
}

export function presignUpload(contentType) {
  return apiFetch("/receipts/presign", {
    method: "POST",
    body: JSON.stringify({ contentType }),
  });
}

export function updateReceipt(receiptId, fields) {
  return apiFetch(`/receipts/${receiptId}`, {
    method: "PUT",
    body: JSON.stringify(fields),
  });
}

export function deleteReceipt(receiptId) {
  return apiFetch(`/receipts/${receiptId}`, { method: "DELETE" });
}

/**
 * Uploads a File object directly to S3 using a pre-signed URL.
 * This does NOT go through apiFetch/API Gateway - it's a direct PUT to S3.
 */
export async function uploadToS3(uploadUrl, file) {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!response.ok) {
    throw new Error("Upload to S3 failed");
  }
}
