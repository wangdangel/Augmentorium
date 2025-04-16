from flask import Flask, request, jsonify
import yaml
import os

app = Flask(__name__)

def load_indexer_config():
    # Assume config.yaml is at the project root (one directory up from this script)
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'))
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    indexer_cfg = config.get("indexer", {})
    host = indexer_cfg.get("host", "localhost")
    port = indexer_cfg.get("port", 6656)
    return host, port

@app.route('/reindex', methods=['POST'])
def trigger_reindex():
    data = request.json
    project_name = data.get('project_name')
    # TODO: Add logic to trigger reindex for the given project_name
    print(f"Received reindex request for project: {project_name}")
    return jsonify({"status": "reindex triggered", "project": project_name})

if __name__ == "__main__":
    host, port = load_indexer_config()
    app.run(host=host, port=port)