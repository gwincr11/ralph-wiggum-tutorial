# Feature: Comic Strip Generator

## Feature Description
A "Comic Strip Generator" that allows users to input a story idea or prompt. The system uses Hugging Face's Inference API to:
1.  Generate a 3-panel comic script/description using a Large Language Model (Zephyr 7B).
2.  Generate images for each panel using a Text-to-Image model (Stable Diffusion XL).
3.  Display the result as a 3-panel comic strip with captions.

## User Story
As a user
I want to enter a funny situation or story idea
So that I can see a custom-generated 3-panel comic strip about it.

## Problem Statement
Users want a fun, interactive way to generate content using AI models within the Ralph Wiggum application, leveraging the "islands" architecture. Currently, there is no such feature.

## Solution Statement
We will implement a new "Comic" feature module:
-   **Backend**: A Flask blueprint (`comic_bp`) that serves the page and an API endpoint (`/api/comic/generate`).
-   **Service**: A `ComicService` that interfaces with Hugging Face Inference API.
-   **Frontend**: A React Island (`ComicGenerator`) that handles user input, displays loading state, and renders the generated comic.
-   **Models**:
    -   LLM: `HuggingFaceH4/zephyr-7b-beta` for script generation.
    -   Image: `stabilityai/stable-diffusion-xl-base-1.0` for panel generation.

## Relevant Files
-   `requirements.txt`: Need to add `huggingface_hub`.
-   `src/app/config.py`: Add `HF_API_TOKEN` configuration.
-   `src/app/views/__init__.py`: Register the new `comic_bp`.
-   `frontend/src/main.ts`: Register the `comic-generator` island.
-   `src/app/templates/base.html`: Add navigation link to the header/nav.

### New Files
-   `src/app/schemas/comic.py`: Pydantic models for request/response.
-   `src/app/services/comic_service.py`: Handles HF API interaction.
-   `src/app/controllers/comic.py`: Business logic for the comic feature.
-   `src/app/views/comic.py`: Flask routes.
-   `src/app/templates/comic/index.html`: Jinja2 template for the comic page.
-   `frontend/src/islands/comic/ComicGenerator.tsx`: React component.
-   `e2e/comic-generator.spec.ts`: Playwright test.

## Implementation Plan

### Phase 1: Foundation & Backend Service
Set up dependencies, configuration, schemas, and the core service to talk to Hugging Face.

### Phase 2: Backend API & Views
Create the controller, blueprint, and templates to serve the feature.

### Phase 3: Frontend Implementation
Build the React Island to interact with the API and display results.

### Phase 4: Integration & Testing
Register the module, add navigation, and verify with E2E tests.

## Step by Step Tasks

### 1. Setup Dependencies and Config
-   Add `huggingface_hub>=0.20.0` to `requirements.txt`.
-   Update `src/app/config.py` to include `HF_API_TOKEN = os.environ.get('HF_API_TOKEN')`.
-   Run `pip install -r requirements.txt`.

### 2. Create Comic Service & Schemas
-   Create `src/app/schemas/comic.py`:
    -   `ComicGenerateRequest` (prompt: str)
    -   `ComicPanel` (image: base64, caption: str)
    -   `ComicResponse` (panels: List[ComicPanel])
-   Create `src/app/services/comic_service.py`.
-   Implement `generate_comic_script(prompt)`: Calls Zephyr-7b to generate 3 panel descriptions + captions.
-   Implement `generate_panel_image(description)`: Calls SDXL to generate an image (returns base64).
-   Implement `generate_comic(prompt)`: Orchestrates the above and returns list of panels.
-   Handle `huggingface_hub` exceptions and raise custom service errors.

### 3. Create Comic Controller
-   Create `src/app/controllers/comic.py`.
-   Implement `generate(data: ComicGenerateRequest)` method that calls `ComicService`.
-   Return data matching `ComicResponse` schema.

### 4. Create Comic Views (Blueprint)
-   Create `src/app/views/comic.py`.
-   Define `comic_bp`.
-   Route `GET /comic`: Renders `comic/index.html`.
-   Route `POST /api/comic/generate`:
    -   Validate input with `ComicGenerateRequest`.
    -   Call `ComicController.generate`.
    -   Return `ComicResponse` as JSON.
    -   Handle service errors and return appropriate HTTP status codes.

### 5. Register Blueprint
-   Update `src/app/views/__init__.py` to import and register `comic_bp`.

### 6. Create Template
-   Create directory `src/app/templates/comic/`.
-   Create `src/app/templates/comic/index.html`.
-   Extend `base.html`.
-   Add a container with `data-island="comic-generator"`.
-   Update `src/app/templates/base.html` to include a navigation link to `/comic` in the main header.

### 7. Create Frontend Island
-   Create directory `frontend/src/islands/comic/`.
-   Create `frontend/src/islands/comic/ComicGenerator.tsx`.
-   Implement UI:
    -   Textarea for prompt.
    -   "Generate Comic" button.
    -   Loading spinner/progress.
    -   Error message display.
    -   Display area for 3 panels (flex/grid layout).
-   Use `fetch` to call `/api/comic/generate`.
-   Handle loading, error, and success states.

### 8. Register Island
-   Update `frontend/src/main.ts` to add `comic-generator` to `islandRegistry`.

### 9. E2E Testing
-   Create `e2e/comic-generator.spec.ts`.
-   Test navigation to `/comic`.
-   Test entering a prompt and clicking generate.
-   **Mock the API response**: Use `page.route('/api/comic/generate', ...)` to return a canned response with placeholder base64 images to avoid hitting HF API.
-   Verify panels appear.

### 10. Validation
-   Run `script/lint`.
-   Run `script/typecheck`.
-   Run `script/test`.
-   Run `script/test-e2e`.

## Testing Strategy

### Unit Tests
-   Mock `InferenceClient` in `tests/test_comic_service.py` to test service logic without network calls.
-   Test `ComicController` logic independently if needed.

### Edge Cases
-   HF API rate limits/failures: Service should catch these and raise specific errors that the View maps to 503 or 429 status codes.
-   Empty prompts: View/Schema validation should catch this (400 Bad Request).
-   Slow generation times: Frontend should have a loading spinner and disable the button.

## Acceptance Criteria
-   User can access `/comic`.
-   User can enter a prompt.
-   System generates 3 panels with images and captions.
-   Images are displayed correctly.
-   UI handles loading state cleanly.
-   Error messages are displayed if generation fails.

## Validation Commands
```bash
# Install new deps
pip install -r requirements.txt

# Lint code
script/lint

# Typecheck
script/typecheck

# Run Backend Tests
script/test

# Run E2E tests (Mocked API)
script/test-e2e --project=chromium --grep "comic"

# Manual verification (if HF_API_TOKEN set in .env)
# script/server
# Visit http://localhost:5000/comic
```
