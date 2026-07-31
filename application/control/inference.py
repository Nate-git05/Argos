from fastapi import HTTPException
from transformers import AutoTokenizer

from application.server.local.config.config import HF_CLIENT


def load_tokenizer(entry: dict):
    tokenizer_repo = entry.get("tokenizer_repo")
    if not tokenizer_repo:
        raise HTTPException(
            status_code=400,
            detail="this model has no tokenizer_repo set in the catalog yet",
        )

    try:
        return AutoTokenizer.from_pretrained(tokenizer_repo, token=HF_CLIENT.token)
    except OSError as e:
        # AutoTokenizer.from_pretrained wraps huggingface_hub's GatedRepoError
        # into a plain OSError before it reaches here -- catching
        # GatedRepoError directly does NOT work for this call path.
        if "gated repo" in str(e).lower():
            raise HTTPException(
                status_code=403,
                detail=(
                    f"tokenizer repo {tokenizer_repo!r} is gated -- accept its license at "
                    f"https://huggingface.co/{tokenizer_repo} with the account matching "
                    "HUGGING_FACE_TOKEN, then try again."
                ),
            )
        raise HTTPException(status_code=502, detail=f"failed to load tokenizer {tokenizer_repo!r}: {e}")
