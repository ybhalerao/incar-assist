from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import torch

#aws pmi settings
max_len = 128
torch_num_threads = 1

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# ---------- CPU-only, keep threads modest for Lambda ----------
torch.set_num_threads(torch_num_threads)

#Declare all globals here
_tokenizer = None
_model = None

try:
    if _model is None and _tokenizer is None:
        __teacher_model  = "mistralai/Mistral-7B-Instruct-v0.2"
        __student_model  = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # base student *checkpoint*
        __output_dir = os.path.join(os.environ['LAMBDA_TASK_ROOT'], 'kd_lora_tinymistral')
        MODEL_DIR        = __output_dir

        # 1) Load the *base student tokenizer* (NOT from adapter dir)
        _tokenizer = AutoTokenizer.from_pretrained(__student_model, use_fast=True)
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token

        # (Optional) 8-bit load to save RAM for inference
        bnb = BitsAndBytesConfig(load_in_8bit=True)

        # 2) Load the *base student model*
        _model = AutoModelForCausalLM.from_pretrained(
            __student_model,
            device_map="auto",
            quantization_config=bnb,                 # or remove if you want full-precision
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        )

        # 3) Apply the LoRA adapter saved in MODEL_DIR
        _model = PeftModel.from_pretrained(_model, MODEL_DIR)
        _model.eval()
        
        
        
except:
    logger.error("ERROR: Unexpected error: Could not connect to AWS S3.")
    sys.exit()

def handler(event, context):
    result = {}
    try:
        max_new = 256
        history = event['text']
        print(f"text: {text}")

        inputs = _tokenizer(history, return_tensors="pt").to(_model.device)
        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tok.eos_token_id,
            )
        result = {"text": _tokenizer.decode(out[0], skip_special_tokens=True)}
    except:
        msg = sys.exc_info()[0]
        logger.info(msg)
        raise Exception("Error, please check input parameters")
    return result
