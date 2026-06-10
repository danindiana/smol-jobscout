# Optional containerized run. Reaches Ollama on the host via --network host
# (or set OLLAMA_API_BASE to the host address).
#
# SECURITY: this container runs a code-executing agent. It is NOT a sandbox for
# the code executor unless you set executor_type accordingly in config/agent.py.
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -e ".[ui]"

ENV OLLAMA_API_BASE=http://host.docker.internal:11434
EXPOSE 7860

CMD ["python", "-m", "smol_jobscout.ui"]
