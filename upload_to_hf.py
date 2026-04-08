import subprocess
import os
subprocess.run(["pip", "install", "huggingface_hub", "-q"])

from huggingface_hub import HfApi

api   = HfApi()
token = os.environ.get("HF_TOKEN", "")

api.upload_folder(
    folder_path="bug_triage_env",
    repo_id="swasss0/bug-triage-env",
    repo_type="space",
    token=token,
    ignore_patterns=["*.pyc", "__pycache__", ".git", "upload_to_hf.py", ".env"],
)

print("HF DONE: https://huggingface.co/spaces/swasss0/bug-triage-env")
