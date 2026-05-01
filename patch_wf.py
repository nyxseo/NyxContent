import json

with open("G:/NyxContent/SEO-Content-Engine-n8n-workflow.json", "r", encoding="utf-8") as f:
    wf = json.load(f)

CREDS = {
    "serpapi":   {"id": "RRUPcI2BNZAxEBQH", "name": "SerpAPI"},
    "firecrawl": {"id": "rIsNpxMq2JTNzOc5", "name": "Firecrawl"},
    "anthropic": {"id": "RTRtODLK5XxhhT6D", "name": "Anthropic Claude API"},
}

for node in wf.get("nodes", []):
    creds = node.get("credentials", {})
    name = node.get("name", "")

    if "httpQueryAuth" in creds:
        node["credentials"]["httpQueryAuth"] = {"id": CREDS["serpapi"]["id"], "name": CREDS["serpapi"]["name"]}

    if "httpHeaderAuth" in creds:
        if any(k in name for k in ["Firecrawl","Crawl","Scrape","Web Search"]):
            node["credentials"]["httpHeaderAuth"] = {"id": CREDS["firecrawl"]["id"], "name": CREDS["firecrawl"]["name"]}
        elif any(k in name for k in ["Claude","Metadata","Article","Anthropic"]):
            node["credentials"]["httpHeaderAuth"] = {"id": CREDS["anthropic"]["id"], "name": CREDS["anthropic"]["name"]}

wf.pop("id", None)
wf["active"] = False

out = "G:/NyxContent/workflow_ready.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(wf, f, indent=2)
print(f"Saved to {out}, nodes={len(wf['nodes'])}")
