# One image shared by all four TicketPilot Lambdas (arm64 / Graviton).
# Each function overrides the handler via ImageConfig.Command in template.yaml.
FROM public.ecr.aws/lambda/python:3.12

# Dependencies first so the layer caches across code changes.
COPY infra/requirements-lambda.txt ./
RUN pip install --no-cache-dir -r requirements-lambda.txt

# Application code + precomputed policy index + policy docs.
COPY src/            ${LAMBDA_TASK_ROOT}/src/
COPY .cache/         ${LAMBDA_TASK_ROOT}/.cache/
COPY data/policies/  ${LAMBDA_TASK_ROOT}/data/policies/

# Default handler (overridden per-function at deploy time).
CMD ["src.rag_agent.handler.handler"]
