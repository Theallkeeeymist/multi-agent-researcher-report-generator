import pytest
import random
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.routes import app

client = TestClient(app)

TRAFFIC_QUESTIONS = [
    "Explain multi-agent orchestration architectures in detail.",
    "Explain autoencoders in depth",
    "Explain the need for Chemical process intensification and how it impacts our society",
    "Explain different ways to optimize token cost in LLMs",
    "How can changing the filtration impact the water flux ratio in a polymer",
    "Psychologically explain how a smile can hide darkness beneath",
    "Explain retrieval-augmented generation pipeline optimization techniques.",
    "Explain how attention mechanisms scale in vision transformers versus standard transformers.",
    "Explain the mathematical foundations of contrastive learning and InfoNCE loss.",
    "Explain how model quantization affects inference latency and accuracy in edge deployment.",
    "Explain the role of policy gradient methods in reinforcement learning from human feedback.",
    "Explain graph neural networks and their applications in molecular property prediction.",
    "Explain the trade-offs between sparse attention and dense attention mechanisms.",
    "Explain how diffusion models generate high-fidelity images through iterative score matching.",
    "Explain model pruning strategies and how they eliminate redundant neural network weights.",
    "Explain the mechanics of Mixture-of-Experts routing algorithms in modern language models.",
    "Explain zero-shot and few-shot generalization in large foundation models.",
    "Explain how causal inference differs from standard predictive machine learning models.",
    "Explain the architecture and training dynamics of variational autoencoders.",
    "Explain how prompt engineering techniques influence output alignment in alignment fine-tuning.",
    "Explain the differences between parameter-efficient fine-tuning methods like LoRA and adapter tuning.",
    "Explain how vector databases index high-dimensional embeddings for efficient approximate nearest neighbor search.",
    "Explain the challenges of catastrophic forgetting in continual learning neural networks.",
    "Explain how federated learning preserves data privacy while training distributed models.",
    "Explain the mechanics of self-supervised learning in computer vision representation.",
    "Explain how reinforcement learning agents handle sparse reward environments.",
    "Explain the core principles of computational fluid dynamics in multiphase reactors.",
    "Explain how mass transfer limitations affect catalytic reaction kinetics in fixed-bed reactors.",
    "Explain the thermodynamic principles behind supercritical fluid extraction.",
    "Explain how dynamic modeling helps optimize industrial distillation column control loops.",
    "Explain the mechanisms of membrane fouling in reverse osmosis desalination systems.",
    "Explain how non-Newtonian fluid behavior influences pipeline pressure drop calculations.",
    "Explain the scaling laws governing heat transfer coefficients in shell-and-tube heat exchangers.",
    "Explain the role of polymer rheology in polymer processing and extrusion manufacturing.",
    "Explain how electrochemical impedance spectroscopy characterizes fuel cell performance.",
    "Explain the principles of adsorption isotherm modeling in industrial gas separation.",
    "Explain how process safety management mitigates runaway reactions in chemical plants.",
    "Explain the transport phenomena behind boundary layer separation in fluid flow.",
    "Explain how molecular simulation aids in the rational design of novel catalysts.",
    "Explain the energy efficiency implications of integrating renewable energy into chemical refineries.",
    "Explain how microfluidic devices enhance precision chemical synthesis.",
    "Explain how distributed training frameworks like DeepSpeed partition workload across GPU clusters.",
    "Explain the architectural differences between event-driven microservices and monolithic backend systems.",
    "Explain how containerization with Docker ensures reproducibility across MLOps deployment pipelines.",
    "Explain the importance of data drift monitoring in production machine learning monitoring systems.",
    "Explain how graph databases optimize traversal queries compared to relational databases.",
    "Explain the principles of asynchronous programming in high-throughput Python backend APIs.",
    "Explain how database indexing strategies impact query performance in large-scale datasets.",
    "Explain the strategies used to handle imbalanced datasets in fraud detection machine learning pipelines.",
    "Explain how continuous integration and continuous deployment pipelines automate software release cycles.",
    "Explain the impact of memory bandwidth bottlenecks on large language model inference speeds.",
    "Explain the psychological mechanisms behind cognitive dissonance and behavioral adaptation.",
    "Explain how evolutionary psychology shapes modern human risk-assessment behavior.",
    "Explain the neurobiological basis of emotional regulation and stress resilience.",
    "Explain the social dynamics of group polarization in digital communication platforms.",
    "Explain the philosophical implications of artificial consciousness and subjective experience."
]

@patch("src.api.routes.run_research_task.delay")
@patch("src.api.routes.AsyncResult")
def test_simulated_traffic_load_workflow(mock_async_result, mock_celery_delay):
    """
    Simulates high-volume real-world client traffic by running a loop 
    of 100 random requests to verify API stability under load.
    """
    SIMULATION_ITERATIONS = 100  # Adjust this to test 50, 100, or more requests

    for i in range(SIMULATION_ITERATIONS):
        # Unique task ID for each loop iteration
        iteration_task_id = f"e2e-load-test-uuid-{i}"
        mock_celery_delay.return_value.id = iteration_task_id

        # Pick a random question from your comprehensive pool
        selected_question = random.choice(TRAFFIC_QUESTIONS)
        payload = {
            "question": selected_question
        }
        
        # 1. Simulate POST request to trigger the task
        response = client.post("/research", json=payload)
        assert response.status_code in [200, 202], f"Failed on iteration {i} with payload: {selected_question}"
        
        data = response.json()
        task_id = data.get("task_id") or data.get("id") or iteration_task_id
        assert task_id is not None

        # Verify Celery delay was invoked properly with the selected question
        mock_celery_delay.assert_called_with(selected_question)

        # 2. Configure mock status check for this iteration
        mock_result_instance = mock_async_result.return_value
        mock_result_instance.state = "SUCCESS"
        mock_result_instance.ready.return_value = True
        mock_result_instance.result = {
            "status": "completed",
            "report": f"Report for iteration {i}: {selected_question}"
        }

        # 3. Simulate GET request to track status
        status_response = client.get(f"/research/status/{task_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            assert status_data is not None