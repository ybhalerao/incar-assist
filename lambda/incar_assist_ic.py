import os
import sys
import logging
import json
import boto3
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

import aws_config

#aws pmi settings
aws_bucket = aws_config.data_bucket
model_prefix = f"{aws_config.base_model_location}/{aws_config.intent_classification_model}"
cache_dir = "/tmp/model"
max_len = 128
torch_num_threads = 1

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# ---------- CPU-only, keep threads modest for Lambda ----------
torch.set_num_threads(torch_num_threads)

try:
    s3_resource = boto3.resource('s3')
    _tokenizer = None
    _model_int8 = None
    _id2label = None 
except:
    logger.error("ERROR: Unexpected error: Could not connect to AWS S3.")
    sys.exit()

def _download_prefix(bucket: str, prefix: str, local_dir: str):
    """Download all objects under s3://bucket/prefix/* into local_dir."""
    os.makedirs(local_dir, exist_ok=True)
    continuation_token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            # skip "directory" placeholders
            if key.endswith("/") or key == prefix:
                continue
            rel = key[len(prefix):].lstrip("/")
            dest = os.path.join(local_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.exists(dest):
                s3.download_file(bucket, key, dest)
        if resp.get("IsTruncated"):
            continuation_token = resp.get("NextContinuationToken")
        else:
            break


def _ensure_model():
    global _tokenizer, _model_int8, _id2label
    if _model_int8 is not None and _tokenizer is not None:
        return

    # 1) Pull everything under the prefix (expects config.json, model.safetensors, tokenizer files)
    _download_prefix(S3_BUCKET, S3_PREFIX, CACHE_DIR)

    # 2) Load tokenizer + FP32 model from /tmp
    _tokenizer = AutoTokenizer.from_pretrained(CACHE_DIR)
    model_fp32 = AutoModelForSequenceClassification.from_pretrained(CACHE_DIR).eval()

    # 3) Dynamic INT8 quantization (CPU). Works best on Linear layers.
    _model_int8 = torch.quantization.quantize_dynamic(
        model_fp32, {torch.nn.Linear}, dtype=torch.qint8
    ).eval()

    # 4) Try id2label from config (optional)
    cfg = getattr(_model_int8, "config", None)
    _id2label = getattr(cfg, "id2label", None) if cfg else None


def _parse_event(event):
    """
    Accepts:
      - direct invoke: {"text": "..."}
      - API Gateway (HTTP proxy): {"body": "{\"text\": \"...\"}", "isBase64Encoded": false}
    Returns plain string 'text' or raises.
    """
    if isinstance(event, str):
        # allow raw string
        return event.strip()

    if not isinstance(event, dict):
        raise ValueError("Unsupported event format")

    # API Gateway proxy?
    if "body" in event and isinstance(event["body"], str):
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            raise ValueError("Body must be JSON with a 'text' field")
        text = (body.get("text") or "").strip()
        if not text:
            raise ValueError("Missing 'text' in body")
        return text

    # Direct invoke
    text = (event.get("text") or "").strip()
    if not text:
        raise ValueError("Missing 'text' field")
    return text


def handler(event, context):
    result = {}
    try:
        _ensure_model()
        text = _parse_event(event)

        enc = _tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=MAX_LEN
        )  # CPU tensors by default

        with torch.no_grad():
            logits = _model_int8(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            pred_id = int(torch.argmax(probs, dim=-1))
            confidence = float(probs[0, pred_id])

        label = _id2label.get(pred_id, str(pred_id)) if _id2label else str(pred_id)
        result = {"text": text, "label_id": pred_id, "label": label, "confidence": round(confidence, 4)}

        # API Gateway compatible response (if used)
        if "body" in event:
            return {"statusCode": 200, "body": json.dumps(result)}
        return result

    except:
        msg = sys.exc_info()[0]
        logger.info(msg)
        raise Exception("Error, please check input parameters")
