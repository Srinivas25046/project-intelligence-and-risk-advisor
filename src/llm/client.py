import os
from openai import OpenAI

PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-3.6-flash",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model": "openai/gpt-oss-20b",
    },
    "cloudflare": {
        "base_url_template": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        "api_key_env": "CLOUDFLARE_API_TOKEN",
        "account_id_env": "CLOUDFLARE_ACCOUNT_ID",
        "model": "@cf/meta/llama-4-scout-17b-16e-instruct",
    },  
}


def _get_client(provider_name: str) -> OpenAI:
    cfg = PROVIDERS[provider_name]
    api_key = os.environ.get(cfg["api_key_env"])
    if not api_key:
        raise RuntimeError(f"Missing {cfg['api_key_env']} — check your .env file")

    if "base_url_template" in cfg:
        account_id = os.environ.get(cfg["account_id_env"])
        if not account_id:
            raise RuntimeError(f"Missing {cfg['account_id_env']} — check your .env file")
        base_url = cfg["base_url_template"].format(account_id=account_id)
    else:
        base_url = cfg["base_url"]

    return OpenAI(api_key=api_key, base_url=base_url)


def call_llm(provider_name: str, prompt: str, temperature: float = 0.2, max_tokens: int = 4096) -> str:
    cfg = PROVIDERS[provider_name]
    client = _get_client(provider_name)

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if not response.choices:
        raise RuntimeError(f"Provider '{provider_name}' returned no choices in response.")

    content = response.choices[0].message.content
    if not content:
        finish_reason = response.choices[0].finish_reason
        raise RuntimeError(
            f"Provider '{provider_name}' returned empty content "
            f"(finish_reason={finish_reason}). Likely ran out of tokens."
        )
    return content


class LLMClient:
    def __init__(self, providers: list[str]):
        self.providers = providers

    def generate(self, prompt: str, temperature: float = 0.2, validate=None) -> str:
        last_error = None
        for provider in self.providers:
            try:
                text = call_llm(provider, prompt, temperature)
                if validate:
                    validate(text)
                return text
            except Exception as e:
                print(f"[LLMClient] Provider '{provider}' failed or gave invalid output: {e}")
                last_error = e
                continue
        raise RuntimeError(f"All providers in the chain failed. Last error: {last_error}") from last_error