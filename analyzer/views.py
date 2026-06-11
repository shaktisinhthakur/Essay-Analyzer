import json
import logging
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

PROVIDER_MODELS = {
    "anthropic": ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"],
}

SYSTEM_PROMPT = "You are a UPSC essay evaluator. Respond only in valid JSON, no markdown."

USER_PROMPTS = {
    "language": (
        "Evaluate the language quality of this essay. Check grammar, vocabulary, "
        "sentence structure and writing style. Return JSON:\n"
        '{{"score": <1-10>, "feedback": "<2-3 sentences>", '
        '"mistakes": [{{"tag": "<Grammar|Vocabulary|Spelling>", "issue": "<short description>"}}]}}\n'
        "Max 3 mistakes.\nEssay: {essay}"
    ),
    "analysis": (
        "Evaluate the depth of analysis of this essay. Check multiple perspectives, "
        "use of examples, critical thinking and root cause coverage. Return JSON:\n"
        '{{"score": <1-10>, "feedback": "<2-3 sentences>", '
        '"mistakes": [{{"tag": "<Shallow|Missing Point|Weak Argument>", "issue": "<short description>"}}]}}\n'
        "Max 3 mistakes.\nEssay: {essay}"
    ),
    "clarity": (
        "Evaluate the clarity and structure of this essay. Check introduction, "
        "body, conclusion, paragraph flow and logical coherence. Return JSON:\n"
        '{{"score": <1-10>, "feedback": "<2-3 sentences>", '
        '"mistakes": [{{"tag": "<Structure|Flow|Coherence>", "issue": "<short description>"}}]}}\n'
        "Max 3 mistakes.\nEssay: {essay}"
    ),
}

def parse_llm_response(text):
    cleaned = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned).strip()
    return json.loads(cleaned)


def _extract_error(resp):
    try:
        return resp.json().get("error", {}).get("message", str(resp.reason))
    except Exception:
        return str(resp.reason)


def call_anthropic(essay, api_key, model, system_prompt, user_prompt):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": model,
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=60,
    )
    if resp.status_code in (401, 403):
        raise PermissionError(f"Invalid Anthropic API key. ({_extract_error(resp)})")
    if not resp.ok:
        raise RuntimeError(f"Anthropic API error: {_extract_error(resp)}")
    data = resp.json()
    return parse_llm_response(data["content"][0]["text"])


def call_groq(essay, api_key, model, system_prompt, user_prompt):
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    if resp.status_code in (401, 403):
        raise PermissionError(f"Invalid Groq API key. ({_extract_error(resp)})")
    if not resp.ok:
        msg = _extract_error(resp)
        if "rate" in msg.lower() or "limit" in msg.lower():
            raise RuntimeError("Groq rate limit exceeded. Please wait and try again.")
        raise RuntimeError(f"Groq API error: {msg}")
    return parse_llm_response(resp.json()["choices"][0]["message"]["content"])


def call_openai(essay, api_key, model, system_prompt, user_prompt):
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    if resp.status_code in (401, 403):
        raise PermissionError(f"Invalid OpenAI API key. ({_extract_error(resp)})")
    if not resp.ok:
        raise RuntimeError(f"OpenAI API error: {_extract_error(resp)}")
    return parse_llm_response(resp.json()["choices"][0]["message"]["content"])


def call_gemini(essay, api_key, model, system_prompt, user_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}]
    }
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code in (400, 403, 401):
        raise PermissionError(f"Invalid Gemini API key. ({_extract_error(resp)})")
    if not resp.ok:
        raise RuntimeError(f"Gemini API error: {_extract_error(resp)}")
    data = resp.json()
    return parse_llm_response(data["candidates"][0]["content"]["parts"][0]["text"])


def call_llm(provider, model, api_key, dimension, essay):
    system = SYSTEM_PROMPT
    user = USER_PROMPTS[dimension].format(essay=essay)
    fn = {
        "anthropic": call_anthropic,
        "groq": call_groq,
        "openai": call_openai,
        "gemini": call_gemini,
    }[provider]
    return fn(essay, api_key, model, system, user)


def index(request):
    return render(request, "analyzer/index.html", {
        "providers": PROVIDER_MODELS,
    })


@csrf_exempt
def analyze(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST allowed."}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)

    essay = (body.get("essay") or "").strip()
    api_key = (body.get("api_key") or "").strip()
    provider = (body.get("provider") or "").strip().lower()
    model = (body.get("model") or "").strip()

    logger.info("Analyze request: provider=%s, model=%s, essay_len=%d, key_len=%d", provider, model, len(essay), len(api_key) if api_key else 0)

    if not essay:
        return JsonResponse({"success": False, "error": "Please paste your essay before analyzing."}, status=400)
    if not api_key:
        return JsonResponse({"success": False, "error": "API key is required."}, status=400)

    if provider not in PROVIDER_MODELS:
        return JsonResponse({"success": False, "error": "Invalid provider selected."}, status=400)

    if model not in PROVIDER_MODELS[provider]:
        return JsonResponse({"success": False, "error": "Invalid model for selected provider."}, status=400)

    dimensions = ["language", "analysis", "clarity"]
    results = {}
    errors = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {
            executor.submit(call_llm, provider, model, api_key, dim, essay): dim
            for dim in dimensions
        }
        for future in as_completed(future_map):
            dim = future_map[future]
            try:
                results[dim] = future.result()
            except PermissionError as e:
                logger.error("PermissionError for %s: %s", dim, e)
                errors.append(str(e))
            except requests.exceptions.Timeout:
                logger.error("Timeout for %s", dim)
                errors.append("Request timed out. Try a faster model.")
            except json.JSONDecodeError:
                logger.error("JSON decode error for %s", dim)
                errors.append("Invalid response from LLM. Try a different model.")
            except (KeyError, IndexError, RuntimeError) as e:
                logger.error("%s for %s: %s", type(e).__name__, dim, e)
                errors.append(str(e) if str(e) != "api_error" else "Something went wrong. Please try again.")
            except Exception as e:
                logger.error("Unexpected error for %s: %s\n%s", dim, e, traceback.format_exc())
                errors.append(f"Unexpected error: {e}")

    if errors:
        return JsonResponse({"success": False, "error": errors[0]}, status=400)

    return JsonResponse({
        "success": True,
        "provider": provider,
        "model": model,
        "language": results.get("language"),
        "analysis": results.get("analysis"),
        "clarity": results.get("clarity"),
    })
