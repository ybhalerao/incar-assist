import os
import sys
import logging
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

#aws pmi settings
max_len = 128
torch_num_threads = 1

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# ---------- CPU-only, keep threads modest for Lambda ----------
torch.set_num_threads(min(4, os.cpu_count() or 1))

#Declare all globals here
_tokenizer = None
_model_int8 = None
_id2label = None 

try:
    if _model_int8 is None and _tokenizer is None:
        lambda_file_path = os.path.join(os.environ['LAMBDA_TASK_ROOT'], 'roberta-student-distilled')
        
        _tokenizer = AutoTokenizer.from_pretrained(lambda_file_path)
        model_fp32 = AutoModelForSequenceClassification.from_pretrained(lambda_file_path).eval()

        # 3) Dynamic INT8 quantization (CPU). Works best on Linear layers.
        _model_int8 = torch.quantization.quantize_dynamic(
            model_fp32, {torch.nn.Linear}, dtype=torch.qint8
        ).eval()

        # 4) Try id2label from config (optional)
        cfg = getattr(_model_int8, "config", None)
        _id2label = getattr(cfg, "id2label", None) if cfg else None        
except:
    msg = sys.exc_info()[0]
    logger.info(msg)
    sys.exit()

def handler(event, context):
    result = {}
    try:
        text = event['text']
        print(f"text: {text}")
        
        enc = _tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=max_len
        )  # CPU tensors by default
        print(f"enc: {enc}")

        with torch.no_grad():
            logits = _model_int8(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            pred_id = int(torch.argmax(probs, dim=-1))
            confidence = float(probs[0, pred_id])

        print(f"pred_id: {pred_id}, confidence: {confidence}")
        
        label = _id2label.get(pred_id, str(pred_id)) if _id2label else str(pred_id)
        result = {"text": text, "label_id": pred_id, "label": label, "confidence": round(confidence, 4)}
    except:
        msg = sys.exc_info()[0]
        logger.info(msg)
        raise Exception("Error, please check input parameters")
    return result
