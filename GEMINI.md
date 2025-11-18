# Project Overview

This project is a modular dubbing pipeline designed to automate the process of dubbing videos. It's built with a Python backend using FastAPI and a Streamlit frontend for user interaction. The pipeline is orchestrated through a series of configurable steps, allowing for flexibility and easy maintenance.

**Key Technologies:**

*   **Backend:** Python, FastAPI
*   **Frontend:** Streamlit, HTML/CSS/JavaScript
*   **Orchestration:** Python, YAML
*   **Modules:** The pipeline is composed of several modules, each responsible for a specific task in the dubbing process:
    *   Audio Extractor
    *   Whisper STT (Speech-to-Text)
    *   Text Processor/Translator
    *   VALL-E X TTS (Text-to-Speech)
    *   XTTS (backup TTS)
    *   RVC (Voice Conversion)
    *   Wav2Lip (Lip-sync)

**Architecture:**

The project follows a modular architecture with a clear separation of concerns:

*   **`backend`:** Contains the FastAPI application that exposes the pipeline modules as API endpoints.
*   **`frontend`:** Includes a Streamlit application and a static web console for interacting with the backend.
*   **`modules`:** Each module is a self-contained script that can be executed independently.
*   **`orchestrator`:** Manages the execution of the pipeline by running the modules in a predefined order.
*   **`data`:** Stores input, intermediate, and output files for the pipeline.
*   **`scripts`:** Contains helper scripts for setting up the environment, running the pipeline, and running tests.

# Building and Running

## Environment Setup

1.  **Create virtual environments:**
    ```powershell
    python -m venv .venv_backend
    python -m venv .venv_frontend
    ```

2.  **Install dependencies:**
    ```powershell
    # Activate backend environment and install dependencies
    .\.venv_backend\Scripts\activate
    pip install -r backend\requirements.txt

    # Activate frontend environment and install dependencies
    .\.venv_frontend\Scripts\activate
    pip install -r frontend\requirements.txt
    ```

    Alternatively, you can run the provided script to automate this process:
    ```powershell
    .\scripts\setup_env.ps1
    ```

## Running the Application

1.  **Start the backend server:**
    ```powershell
    uvicorn backend.main:app --reload --port 8000
    ```

2.  **Run the Streamlit UI:**
    ```powershell
    streamlit run frontend/app.py
    ```

3.  **Run the static web console:**
    Open the `frontend/web/index.html` file in your browser, or run a simple web server:
    ```powershell
    cd frontend/web
    python -m http.server 8501
    ```

## Running the Pipeline

The pipeline can be run using the `pipeline_runner.py` script or the `run_pipeline.ps1` wrapper.

**Using the PowerShell script:**
```powershell
.\scripts\run_pipeline.ps1 -InputMedia data/inputs/sample.mp4
```

**Using the Python script directly:**
```powershell
python orchestrator/pipeline_runner.py --input-media data/inputs/sample.mp4
```

# Development Conventions

*   **Modularity:** Each step in the pipeline is a separate module, making it easy to add, remove, or modify individual components.
*   **Configuration:** The pipeline is configured using YAML files, allowing for easy customization of the steps and their parameters.
*   **Data Flow:** The pipeline uses a standardized data flow, with input, intermediate, and output files stored in the `data` directory.
*   **API-driven:** The backend exposes the pipeline modules as a RESTful API, enabling integration with different frontends and applications.
*   **Asynchronous Support:** The backend supports asynchronous execution of long-running tasks, with a job management system to track their status.

# Testing

The project includes a set of tests to ensure the quality and correctness of the pipeline.

**Running tests:**
```powershell
.\scripts\run_tests.ps1 -m smoke
```

To run all tests, use the `-m all` option:
```powershell
.\scripts\run_tests.ps1 -m all
```

You can also run the tests directly using `pytest`:
```powershell
python -m pytest tests
```
