"""
Fine-tune Abby Model

This script fine-tunes Mistral 7B (or similar) with Abby's personality.
Optimized for AMD RX 7900 XTX with ROCm.

Usage:
    python training/finetune_abby.py
    python training/finetune_abby.py --base-model mistralai/Mistral-7B-Instruct-v0.2
    python training/finetune_abby.py --quantize 4  # 4-bit quantization
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Check for required packages
def check_dependencies():
    """Check if training dependencies are installed"""
    missing = []
    
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__}")
        if torch.cuda.is_available():
            print(f"  CUDA available: {torch.cuda.get_device_name(0)}")
        elif hasattr(torch, 'hip') and torch.cuda.is_available():
            print(f"  ROCm/HIP available")
        else:
            print("  ⚠️ No GPU detected - training will be SLOW")
    except ImportError:
        missing.append("torch")
    
    try:
        import transformers
        print(f"✓ Transformers {transformers.__version__}")
    except ImportError:
        missing.append("transformers")
    
    try:
        import datasets
        print(f"✓ Datasets {datasets.__version__}")
    except ImportError:
        missing.append("datasets")
    
    try:
        import peft
        print(f"✓ PEFT {peft.__version__}")
    except ImportError:
        missing.append("peft")
    
    try:
        import trl
        print(f"✓ TRL {trl.__version__}")
    except ImportError:
        missing.append("trl")
    
    try:
        import bitsandbytes
        print(f"✓ bitsandbytes {bitsandbytes.__version__}")
    except ImportError:
        print("  ⚠️ bitsandbytes not found (optional, for quantization)")
    
    try:
        from unsloth import FastLanguageModel
        print("✓ Unsloth available (recommended)")
        return "unsloth"
    except ImportError:
        print("  ⚠️ Unsloth not found (will use standard training)")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install torch transformers datasets peft trl")
        sys.exit(1)
    
    return "standard"


def train_with_unsloth(
    base_model: str,
    training_data: str,
    output_dir: str,
    quantize: int = 4,
    lora_rank: int = 16,
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    max_seq_length: int = 2048,
):
    """Fine-tune using Unsloth (fastest)"""
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments
    
    print(f"\n🚀 Training with Unsloth")
    print(f"   Base model: {base_model}")
    print(f"   Quantization: {quantize}-bit")
    print(f"   LoRA rank: {lora_rank}")
    print(f"   Epochs: {epochs}")
    
    # Load model
    print("\n📦 Loading model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        load_in_4bit=(quantize == 4),
        load_in_8bit=(quantize == 8),
    )
    
    # Add LoRA adapters
    print("🔧 Adding LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=lora_rank * 2,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing=True,
        random_state=42,
    )
    
    # Load dataset
    print(f"📊 Loading training data from {training_data}...")
    dataset = load_dataset("json", data_files=training_data, split="train")
    print(f"   {len(dataset)} examples loaded")
    
    # Format function for ShareGPT format
    def format_prompt(example):
        text = ""
        for turn in example.get("conversations", []):
            if turn["from"] == "system":
                text += f"<|im_start|>system\n{turn['value']}<|im_end|>\n"
            elif turn["from"] == "human":
                text += f"<|im_start|>user\n{turn['value']}<|im_end|>\n"
            elif turn["from"] == "gpt":
                text += f"<|im_start|>assistant\n{turn['value']}<|im_end|>\n"
        return {"text": text}
    
    dataset = dataset.map(format_prompt)
    
    # Training arguments
    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        fp16=True,
        bf16=False,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        optim="adamw_8bit",
        weight_decay=0.01,
        report_to="none",
    )
    
    # Train
    print("\n🏋️ Starting training...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        args=args,
    )
    
    trainer.train()
    
    # Save
    print(f"\n💾 Saving to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("\n✅ Training complete!")
    return output_dir


def train_standard(
    base_model: str,
    training_data: str,
    output_dir: str,
    quantize: int = 4,
    lora_rank: int = 16,
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    max_seq_length: int = 2048,
):
    """Fine-tune using standard transformers + PEFT"""
    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM, 
        AutoTokenizer, 
        TrainingArguments,
        BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    
    print(f"\n🚀 Training with standard transformers + PEFT")
    print(f"   Base model: {base_model}")
    print(f"   Quantization: {quantize}-bit")
    print(f"   LoRA rank: {lora_rank}")
    print(f"   Epochs: {epochs}")
    
    # Quantization config
    if quantize == 4:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
    elif quantize == 8:
        bnb_config = BitsAndBytesConfig(load_in_8bit=True)
    else:
        bnb_config = None
    
    # Load model
    print("\n📦 Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Prepare for training
    if bnb_config:
        model = prepare_model_for_kbit_training(model)
    
    # LoRA config
    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_rank * 2,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    print("🔧 Adding LoRA adapters...")
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load dataset
    print(f"📊 Loading training data from {training_data}...")
    dataset = load_dataset("json", data_files=training_data, split="train")
    print(f"   {len(dataset)} examples loaded")
    
    # Format function
    def format_prompt(example):
        text = ""
        for turn in example.get("conversations", []):
            if turn["from"] == "system":
                text += f"<|im_start|>system\n{turn['value']}<|im_end|>\n"
            elif turn["from"] == "human":
                text += f"<|im_start|>user\n{turn['value']}<|im_end|>\n"
            elif turn["from"] == "gpt":
                text += f"<|im_start|>assistant\n{turn['value']}<|im_end|>\n"
        return {"text": text}
    
    dataset = dataset.map(format_prompt)
    
    # Training arguments
    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        fp16=True,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        report_to="none",
    )
    
    # Train
    print("\n🏋️ Starting training...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        args=args,
    )
    
    trainer.train()
    
    # Save
    print(f"\n💾 Saving to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("\n✅ Training complete!")
    return output_dir


def merge_and_export(lora_dir: str, output_dir: str, base_model: str):
    """Merge LoRA with base model and export for Ollama"""
    try:
        from unsloth import FastLanguageModel
        print("\n🔀 Merging LoRA with base model (using Unsloth)...")
        
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=lora_dir,
            load_in_4bit=True,
        )
        
        model.save_pretrained_merged(output_dir, tokenizer, save_method="merged_16bit")
        print(f"✅ Merged model saved to {output_dir}")
        
    except ImportError:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        
        print("\n🔀 Merging LoRA with base model (using transformers)...")
        
        base = AutoModelForCausalLM.from_pretrained(base_model, device_map="auto")
        model = PeftModel.from_pretrained(base, lora_dir)
        model = model.merge_and_unload()
        
        tokenizer = AutoTokenizer.from_pretrained(lora_dir)
        
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        print(f"✅ Merged model saved to {output_dir}")
    
    print("\nTo convert to GGUF for Ollama:")
    print(f"  1. git clone https://github.com/ggerganov/llama.cpp")
    print(f"  2. python llama.cpp/convert_hf_to_gguf.py {output_dir} --outfile abby.gguf --outtype q4_k_m")
    print(f"  3. ollama create abby -f Modelfile")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Abby model")
    parser.add_argument("--base-model", type=str, 
                        default="mistralai/Mistral-7B-Instruct-v0.2",
                        help="Base model to fine-tune")
    parser.add_argument("--training-data", type=str,
                        default="training/abby_data.jsonl",
                        help="Training data file (JSONL)")
    parser.add_argument("--output-dir", type=str,
                        default="models/abby_lora",
                        help="Output directory for LoRA weights")
    parser.add_argument("--quantize", type=int, choices=[4, 8, 16], default=4,
                        help="Quantization bits (4, 8, or 16 for none)")
    parser.add_argument("--lora-rank", type=int, default=16,
                        help="LoRA rank (higher = more capacity, more VRAM)")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4,
                        help="Learning rate")
    parser.add_argument("--max-seq-length", type=int, default=2048,
                        help="Maximum sequence length")
    parser.add_argument("--merge", action="store_true",
                        help="Merge LoRA with base and export")
    parser.add_argument("--merged-output", type=str, default="models/abby_merged",
                        help="Output directory for merged model")
    args = parser.parse_args()
    
    # Check paths
    project_root = Path(__file__).parent.parent
    training_data = project_root / args.training_data
    output_dir = project_root / args.output_dir
    
    if not training_data.exists():
        print(f"❌ Training data not found: {training_data}")
        print("Generate it first with:")
        print("  python training/generate_training_data.py -o training/abby_data.jsonl")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🎯 Abby Model Fine-tuning")
    print("=" * 60)
    
    # Check dependencies
    trainer_type = check_dependencies()
    
    # If just merging
    if args.merge:
        merged_output = project_root / args.merged_output
        merge_and_export(str(output_dir), str(merged_output), args.base_model)
        return
    
    # Train
    if trainer_type == "unsloth":
        train_with_unsloth(
            base_model=args.base_model,
            training_data=str(training_data),
            output_dir=str(output_dir),
            quantize=args.quantize,
            lora_rank=args.lora_rank,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_seq_length=args.max_seq_length,
        )
    else:
        train_standard(
            base_model=args.base_model,
            training_data=str(training_data),
            output_dir=str(output_dir),
            quantize=args.quantize,
            lora_rank=args.lora_rank,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_seq_length=args.max_seq_length,
        )
    
    print("\n" + "=" * 60)
    print("🎉 Training Complete!")
    print("=" * 60)
    print(f"\nLoRA weights saved to: {output_dir}")
    print("\nNext steps:")
    print(f"  1. Merge and export: python training/finetune_abby.py --merge")
    print(f"  2. Convert to GGUF (see FINETUNING_AMD.md)")
    print(f"  3. Create Ollama model and test!")


if __name__ == "__main__":
    main()
