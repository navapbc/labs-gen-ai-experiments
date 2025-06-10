#!/bin/sh

# `--host 0.0.0.0` is needed to allow external access to the server
hayhooks run --host 0.0.0.0

# LOG=DEBUG hayhooks run --additional-python-path . --host 0.0.0.0

# sleep 5
# hayhooks pipeline deploy-files -n my_pipeline --overwrite --skip-saving-files hayhooks_pipelines
# hayhooks pipeline deploy-files -n my_pipeline --overwrite hayhooks_pipelines
# hayhooks status

# sleep infinity
