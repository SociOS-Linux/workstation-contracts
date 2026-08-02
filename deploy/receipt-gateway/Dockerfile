# Receipt-emitting inference gateway — deployable service.
# Build from the repo root:  podman build -f deploy/receipt-gateway/Dockerfile -t receipt-gateway .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir "jsonschema>=4.0.0"

COPY tools/inference_receipt_emitter.py tools/receipt_gateway.py /app/tools/
COPY schemas/model-plane/InferenceReceipt.schema.json /app/schemas/model-plane/

# Ledger persists on a mounted volume (SEAM-011: durable, non-local ledger).
ENV RECEIPT_GATEWAY_LEDGER=/var/lib/receipt-gateway/ledger.jsonl \
    RECEIPT_GATEWAY_HOST=0.0.0.0 \
    RECEIPT_GATEWAY_PORT=8898 \
    RECEIPT_GATEWAY_BACKEND=http://127.0.0.1:8899
VOLUME ["/var/lib/receipt-gateway"]
EXPOSE 8898

# RECEIPT_GATEWAY_MODEL_DIGEST must be provided at run time (the deployed model's digest).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8898/health',timeout=2).status==200 else 1)"]

ENTRYPOINT ["python", "tools/receipt_gateway.py", "--serve"]
