#!/bin/sh
set -e

DIM="${EMBED_DIM:-384}"
API="http://meilisearch:7700"
KEY="${MEILI_KEY}"

echo "Creating indexes and applying settings..."

curl -v -X POST "$API/indexes" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"uid":"documents","primaryKey":"id"}' || true

curl -v -X POST "$API/indexes" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"uid":"chunks","primaryKey":"id"}' || true

COMMON_SETTINGS="\"searchableAttributes\":[\"content\",\"title\"],\"displayedAttributes\":[\"id\",\"content\",\"title\",\"metadata\",\"source\",\"tags\",\"document_id\",\"chunk_index\",\"total_chunks\",\"page_number\"],\"filterableAttributes\":[\"source\",\"tags\",\"metadata.sha\",\"metadata.lang\"],\"sortableAttributes\":[\"created_at\",\"updated_at\"]"
# Only chunks carry vectors: whole documents are indexed for full-text search only
DOC_PAYLOAD="{$COMMON_SETTINGS}"
CHUNK_PAYLOAD="{\"embedders\":{\"default\":{\"source\":\"userProvided\",\"dimensions\":$DIM}},$COMMON_SETTINGS}"

curl -v -X PATCH "$API/indexes/documents/settings" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d "$DOC_PAYLOAD" || true

curl -v -X PATCH "$API/indexes/chunks/settings" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d "$CHUNK_PAYLOAD" || true

echo "✅ Meilisearch initialization completed."
