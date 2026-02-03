# Fine-Tuning Abby on AMD Radeon RX 7900 XTX

This guide covers fine-tuning a custom Abby model on your **RX 7900 XTX (24GB VRAM)**.

## TL;DR Quick Start

```bash
# 1. Install ROCm (Windows/Linux)
# 2. Generate training data
python training/generate_training_data.py -o training/abby_data.jsonl --count 2000

# 3. Fine-tune with unsloth or axolotl
python training/finetune_abby.py
```

---

## Hardware: RX 7900 XTX

- **24GB VRAM** - Perfect for LoRA fine-tuning 7B models
- **ROCm** support required (CUDA won't work on AMD)
- Can handle: Mistral 7B, Llama 3.1 8B, Qwen2.5 7B with LoRA
- May struggle with: Full fine-tuning (QLoRA recommended)

---

## Option 1: ROCm + Unsloth (Recommended)

**Unsloth** is the fastest and most memory-efficient option.

### Install ROCm on Linux

```bash
# Ubuntu 22.04 (recommended)
wget https://repo.radeon.com/amdgpu-install/6.0/ubuntu/jammy/amdgpu-install_6.0.60000-1_all.deb
sudo dpkg -i amdgpu-install_6.0.60000-1_all.deb
sudo amdgpu-install --usecase=rocm

# Verify
rocminfo
```

### Install ROCm on Windows (WSL2)

ROCm has limited Windows support. Best option is WSL2 with Ubuntu:

```powershell
# PowerShell - Install WSL2 with Ubuntu
wsl --install -d Ubuntu-22.04

# Then inside WSL2, install ROCm (same as Linux)
```

### Install Unsloth with ROCm

```bash
# Create virtual environment
python -m venv unsloth_env
source unsloth_env/bin/activate

# Install PyTorch for ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

# Install unsloth
pip install "unsloth[rocm] @ git+https://github.com/unslothai/unsloth.git"
```

### Fine-tune with Unsloth

```python
from unsloth import FastLanguageModel
from datasets import load_dataset

# Load Mistral 7B with 4bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/mistral-7b-instruct-v0.2-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # LoRA rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=32,
    lora_dropout=0.05,
    use_gradient_checkpointing=True,
)

# Load your training data
dataset = load_dataset("json", data_files="training/abby_data.jsonl")

# Train!
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    args=TrainingArguments(
        output_dir="./abby_lora",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100,
    ),
)

trainer.train()
model.save_pretrained("abby_lora_final")
```

---

## Option 2: Axolotl (More Features)

**Axolotl** is more configurable but requires more setup.

### Install

```bash
git clone https://github.com/OpenAccess-AI-Collective/axolotl
cd axolotl
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
pip install -e ".[rocm]"
```

### Config File (abby_config.yml)

```yaml
base_model: mistralai/Mistral-7B-Instruct-v0.2
model_type: MistralForCausalLM
tokenizer_type: LlamaTokenizer

load_in_8bit: true
load_in_4bit: false

datasets:
  - path: training/abby_data.jsonl
    type: sharegpt
    conversation: chatml

dataset_prepared_path: last_run_prepared
val_set_size: 0.05
output_dir: ./abby_axolotl

sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true

adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - v_proj
  - k_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

gradient_accumulation_steps: 4
micro_batch_size: 2
num_epochs: 3
learning_rate: 2e-4
optimizer: adamw_torch
lr_scheduler: cosine
warmup_ratio: 0.1

train_on_inputs: false
group_by_length: false
bf16: false
fp16: true

logging_steps: 10
save_steps: 100
eval_steps: 100

deepspeed:
flash_attention: false  # Not supported on AMD yet
```

### Train

```bash
accelerate launch -m axolotl.cli.train abby_config.yml
```

---

## Option 3: LLaMA Factory (Easiest UI)

**LLaMA Factory** has a nice web UI but may have limited ROCm support.

### Install

```bash
git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
pip install -e ".[torch,metrics]"
```

### Prepare Data

Convert to LLaMA Factory format:

```bash
python training/generate_training_data.py -o training/abby_data.jsonl --format alpaca
```

Then add to `data/dataset_info.json`:

```json
{
  "abby_training": {
    "file_name": "abby_data.jsonl",
    "formatting": "alpaca"
  }
}
```

### Train via CLI

```bash
llamafactory-cli train \
  --model_name_or_path mistralai/Mistral-7B-Instruct-v0.2 \
  --dataset abby_training \
  --template mistral \
  --finetuning_type lora \
  --lora_rank 16 \
  --output_dir abby_llama_factory \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 4 \
  --num_train_epochs 3 \
  --learning_rate 2e-4 \
  --fp16
```

---

## Option 4: DirectML (Windows Native - No ROCm)

If ROCm doesn't work, you can use **DirectML** for Windows-native AMD support.

⚠️ **Caveat**: DirectML is slower and has fewer features, but works on Windows without WSL.

### Install

```bash
pip install torch-directml
pip install transformers accelerate bitsandbytes
```

### Usage

```python
import torch_directml

device = torch_directml.device()
model = model.to(device)
```

---

## Converting for Ollama

After training, convert the LoRA to a full model and quantize for Ollama:

### 1. Merge LoRA with Base Model

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="abby_lora_final",
    load_in_4bit=True,
)

# Merge and save
model.save_pretrained_merged("abby_merged", tokenizer)
```

### 2. Convert to GGUF (for Ollama)

```bash
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Convert
python convert_hf_to_gguf.py ../abby_merged --outfile abby.gguf --outtype q4_k_m
```

### 3. Create Ollama Model

Create `Modelfile`:

```
FROM abby.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""

PARAMETER temperature 0.7
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
PARAMETER stop "<|im_end|>"

SYSTEM """You are Abby. You respond naturally in 1-2 sentences max.
You're warm, genuine, and slightly playful. Match the user's energy."""
```

```bash
ollama create abby -f Modelfile
ollama run abby
```

---

## Training Data Tips

1. **Quality > Quantity**: 500 good examples beats 5000 bad ones
2. **Diversity**: Cover greetings, questions, emotions, coding, errors
3. **Consistent length**: Train Abby to give SHORT responses
4. **Negative examples**: Include DPO data for what NOT to say
5. **Multi-turn**: Include conversation flows, not just single turns

### Generate More Data

```bash
# Generate 2000 examples with augmentation
python training/generate_training_data.py -o training/abby_data.jsonl --count 2000 --augment

# Different formats
python training/generate_training_data.py --format sharegpt  # For unsloth
python training/generate_training_data.py --format alpaca    # For llama-factory
python training/generate_training_data.py --format openai    # For compatibility
```

---

## Memory Requirements

| Model | VRAM (4-bit) | VRAM (8-bit) | VRAM (FP16) |
|-------|-------------|-------------|-------------|
| Mistral 7B | ~6GB | ~10GB | ~16GB |
| Llama 3.1 8B | ~7GB | ~12GB | ~18GB |
| Qwen2.5 7B | ~6GB | ~10GB | ~16GB |

With your **24GB VRAM**, you can:
- ✅ QLoRA training on 7B models (4-bit quantized)
- ✅ LoRA training on 7B models (8-bit)
- ⚠️ Full FP16 training on 7B (tight, may OOM)
- ❌ Full training on 13B+ models

---

## Troubleshooting

### ROCm Not Detecting GPU

```bash
# Check if GPU is visible
rocminfo

# Set HIP visible devices
export HIP_VISIBLE_DEVICES=0
export CUDA_VISIBLE_DEVICES=0  # Some tools still check this
```

### Out of Memory

1. Reduce batch size: `per_device_train_batch_size: 1`
2. Increase gradient accumulation: `gradient_accumulation_steps: 8`
3. Use 4-bit quantization: `load_in_4bit: true`
4. Reduce sequence length: `max_seq_length: 1024`

### Slow Training

1. Enable flash attention (if supported)
2. Use bf16 instead of fp16 (if supported)
3. Increase batch size to use more VRAM
4. Use unsloth instead of vanilla transformers (2-5x speedup)

---

## Expected Training Time

On RX 7900 XTX with 1000 examples:

| Method | Time |
|--------|------|
| Unsloth QLoRA | ~30 mins |
| Axolotl LoRA | ~1 hour |
| Full fine-tune | ~4 hours |

---

## Next Steps

1. Generate training data: `python training/generate_training_data.py`
2. Review and expand the data manually
3. Choose a training method (unsloth recommended)
4. Train the model
5. Convert to GGUF and load in Ollama
6. Test and iterate!
