from mitmproxy.io import FlowReader
import json
corpus = []
with open("/captures/session.flows", "rb") as f:
    for flow in FlowReader(f).stream():
        if "/v1/chat/completions" in flow.request.path:
            corpus.append(json.loads(flow.request.get_text()))
json.dump(corpus, open("/captures/corpus.json", "w"), indent=1)
print(f"{len(corpus)} requests exported")
