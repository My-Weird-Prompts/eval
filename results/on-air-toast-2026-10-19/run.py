"""On-air mini-eval (2026-10-19): one short MWP-style prompt, four writers, raw outputs saved verbatim.
Aired as an offline episode; not part of the bakeoff scoring."""
import json, sys, time, os, concurrent.futures as cf, urllib.request

SYSTEM = ("You write scripts for My Weird Prompts, a podcast hosted by two brothers. "
          "Corn is the curious one with a cheeky edge who asks probing questions. "
          "Herman Poppleberry is the nerdy one who reads the papers and gets excited about details. "
          "A listener named Daniel sends in a prompt and the brothers discuss it. "
          "Write a complete three-minute episode (about 450 words) as dialogue. "
          "Format every line as 'Name: text'. No stage directions, no sound effects, no markdown.")
USER = ("Daniel's prompt: Is it actually true that toast lands butter-side down more often than not? "
        "Or is that just the one we remember? I'd love to know if anyone has really tested it.")
# Reasoning mirrors how each model ran as a pipeline writer: pool models with
# reasoning off, Sol at low effort (mandatory). The first run used provider
# defaults and DeepSeek spent all 2000 tokens reasoning, returning no text.
REASONING = {"openai/gpt-6.1-sol": {"effort": "low"}, "deepseek/deepseek-v4.1-flash": {"enabled": False},
             "anthropic/claude-haiku-5.5": {"enabled": False}}
MODELS = ["deepseek/deepseek-v4.1-flash", "openai/gpt-6.1-sol", "anthropic/claude-haiku-5.5", "openai/gpt-3.5-turbo-0613"]

def call(model):
    body = {"model": model, "max_tokens": 2000,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]}
    if model in REASONING:
        body["reasoning"] = REASONING[model]
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
        {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=300))
    return {"requested": model, "served": r.get("model"), "seconds": round(time.time() - t, 1),
            "usage": r.get("usage"), "text": r["choices"][0]["message"]["content"]}

with cf.ThreadPoolExecutor(4) as ex:
    out = list(ex.map(call, MODELS))
json.dump({"date": "2026-10-19", "system": SYSTEM, "user": USER, "outputs": out}, open("outputs.json", "w"), indent=2)
for o in out:
    print(f"\n===== {o['requested']} (served {o['served']}, {o['seconds']}s, {len(o['text'].split())} words)\n{o['text']}")
