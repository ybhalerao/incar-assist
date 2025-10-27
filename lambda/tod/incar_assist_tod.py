import os
import sys
import logging
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

#aws pmi settings
max_len = 128

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# ---------- CPU-only, keep threads modest for Lambda ----------
torch.set_num_threads(min(4, os.cpu_count() or 1))

STOP_STRINGS = ("</s>", "[/INST]", "User:", "Assistant:")

#Declare all globals here
_tokenizer = None
_model = None

def _apply_dynamic_quantization(model: torch.nn.Module) -> torch.nn.Module:
    """
    Dynamic int8 quantization for CPU. Helps speed some Linear ops.
    Safe no-op if it fails on this arch/wheel.
    """
    try:
        from torch.ao.quantization import quantize_dynamic
    except Exception:
        try:
            # older import path
            from torch.quantization import quantize_dynamic
        except Exception:
            return model
    try:
        qmodel = quantize_dynamic(
            model,
            {torch.nn.Linear},  # quantize linear layers
            dtype=torch.qint8
        )
        return qmodel
    except Exception:
        return model

try:
    if _model is None and _tokenizer is None:
        __student_model  = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # base student *checkpoint*
        __model_dir = os.path.join(os.environ['LAMBDA_TASK_ROOT'], 'kd_lora_tinymistral_merged')
        #__model_dir = os.path.join("/home/ec2-user/development/incar-assist/notebooks", 'kd_lora_tinymistral_merged')
        print(f"__model_dir: {__model_dir}")

        # 1) Load the *base student tokenizer* (NOT from adapter dir)
        _tokenizer = AutoTokenizer.from_pretrained(__model_dir, use_fast=True)

        # 2) Load the *base student model*
        base = AutoModelForCausalLM.from_pretrained(
            __model_dir,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        #base.eval()
        
        #_model = _apply_dynamic_quantization(base)
        _model = base
        _model.eval()
        print("Model loaded")

except:
    msg = sys.exc_info()[0]
    logger.info(msg)
    sys.exit()
    
def handler(event, context):
    result = {}
    try:
        max_new = 64
        history = event['text']
        print(f"text: {history}")
        
        inputs = _tokenizer(history, return_tensors="pt")
        input_len = inputs["input_ids"].size(1)
        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=False,
                temperature=0.0,
                top_p=1.0,
                pad_token_id=_tokenizer.eos_token_id,
                eos_token_id=_tokenizer.eos_token_id,
            )
        new_tokens = out[0, input_len:]
        reply = _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        for stop in ("</s>", "[/INST]"):
            idx = reply.find(stop)
            if idx != -1:
                reply = reply[:idx].strip()        
        
        result = {"text": reply}
        
    except:
        msg = sys.exc_info()[0]
        logger.info(msg)
        raise Exception("Error, please check input parameters")
    return result
