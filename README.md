# TicketPilot

TicketPilot is an AI-powered customer support system that automatically triages incoming support tickets, drafts responses, escalates risky cases for human review, and answers policy questions using retrieval-augmented generation.

Live demo: https://d2m9tsplwhuev5.cloudfront.net

## Overview

TicketPilot contains two AI workflows:

### Ticket Triage Agent

The triage system processes incoming customer support tickets and:

* Classifies category, urgency, and sentiment
* Generates a draft response
* Detects sensitive or low-confidence cases
* Routes higher-risk tickets to a human approval queue
* Stores ticket status and approval decisions in DynamoDB

Tickets are processed asynchronously using Amazon SQS so incoming traffic can be buffered and handled independently of the web request.

The agent workflow is implemented using LangGraph and uses Pydantic schemas to validate structured LLM outputs.

### Policy Q&A Agent

The policy Q&A system uses retrieval-augmented generation to answer questions using company policy documents.

The pipeline:

1. Splits policy documents into searchable chunks
2. Generates embeddings using OpenAI embeddings
3. Stores and searches vectors using FAISS
4. Retrieves the most relevant policy text
5. Generates an answer grounded only in the retrieved context
6. Returns the answer with its source citation

If the retrieved documentation does not support an answer, the system returns that it does not know rather than generating an unsupported response.

## Architecture

The application is deployed as a serverless AWS system.

Customer requests are sent through API Gateway to AWS Lambda functions.

Ticket processing follows:

Dashboard -> API Gateway -> Intake Lambda -> SQS -> Triage Lambda -> DynamoDB

Human approval follows:

Dashboard -> API Gateway -> Approvals Lambda -> DynamoDB

Policy questions follow:

Dashboard -> API Gateway -> RAG Lambda -> FAISS retrieval -> OpenAI model

The frontend is hosted using Amazon S3 and CloudFront.

## Tech Stack

Python

LangGraph

OpenAI API

* gpt-4o-mini
* text-embedding-3-small

AI / Retrieval

* FAISS
* Pydantic
* Retrieval-Augmented Generation

AWS

* Lambda
* API Gateway
* SQS
* DynamoDB
* S3
* CloudFront
* SSM Parameter Store
* CloudWatch
* ECR

Infrastructure / Development

* AWS SAM
* Docker
* pytest
* GitHub Actions

## Project Structure

src/

* triage_agent/ - ticket classification, response drafting, escalation logic, Lambda handler
* rag_agent/ - document ingestion, retrieval, grounded answer generation, Lambda handler
* shared/ - configuration, LLM utilities, schemas, storage, caching, and logging
* api.py - ticket intake and approval API handlers

infra/

* AWS SAM infrastructure
* Docker image configuration
* deployment scripts

evals/

* evaluation datasets
* classification metrics
* LLM response evaluation

dashboard/

* web interface for ticket submission, policy questions, and human approvals

tests/

* automated unit tests

docs/

* project documentation and operations notes

## Running Locally

Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add an OpenAI API key to `.env`.

Build the policy search index:

```bash
python -m src.rag_agent.ingest
```

Run the RAG demo:

```bash
python scripts/cache_demo.py
```

Run tests:

```bash
python -m pytest
```

Run evaluations:

```bash
python evals/run_eval.py --label demo
```

## Deployment

The application can be deployed to AWS using the included SAM infrastructure and Docker configuration.

Store the OpenAI API key in AWS Systems Manager Parameter Store:

```bash
aws ssm put-parameter \
  --name /ticketpilot/openai-api-key \
  --type String \
  --value "YOUR_KEY" \
  --overwrite
```

Deploy:

```bash
bash infra/deploy.sh
```

## License

MIT License.
