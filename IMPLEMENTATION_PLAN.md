# Implementation Plan — ralph-wiggum-tutorial

## Status

> **Implementation Status: Base App 100% ✅ | Comic Generator 100% ✅**
>
> _All Comic Generator tasks complete._

| Component | Status | Notes |
|-----------|--------|-------|
| Base App (Hello World) | ✅ Complete | Flask + React Islands, 13 backend + 11 E2E tests passing |
| Comic Generator Feature | ✅ Complete | 17/17 tasks complete, all files implemented |

---

## 🎯 Comic Generator — Prioritized Task List

> **Spec:** `specs/issue-comic-generator-sdlc_planner-add-comic-system.md`
> **Goal:** Generate 3-panel comics using Hugging Face APIs
> **LLM:** `HuggingFaceH4/zephyr-7b-beta` for script generation
> **Images:** `stabilityai/stable-diffusion-xl-base-1.0` for panel images
> **Pattern:** Follow Hello feature (`src/app/views/hello.py`, `frontend/src/islands/hello/`)

### P0 — Must Have (Core Functionality)

#### Phase 1: Dependencies & Configuration

| Task | File | Status |
|------|------|--------|
| 1.1 | `requirements.txt` | ✅ |
| 1.2 | `src/app/config.py` | ✅ |
| 1.3 | `.env.example` | ✅ |

- ✅ **1.1** Add `huggingface_hub>=0.20.0` to `requirements.txt`
  - Append after `python-dotenv>=1.0.0`
- ✅ **1.2** Add `HF_API_TOKEN` to `src/app/config.py` base Config class:
  ```python
  HF_API_TOKEN = os.environ.get('HF_API_TOKEN')
  ```
- ✅ **1.3** Add `HF_API_TOKEN=` placeholder to `.env.example`:
  ```bash
  # Hugging Face API token for comic generation
  HF_API_TOKEN=
  ```

#### Phase 2: Backend Schemas

| Task | File | Status |
|------|------|--------|
| 2.1 | `src/app/schemas/comic.py` | ✅ |

- ✅ **2.1** Create `src/app/schemas/comic.py` following `hello.py` pattern:
  - `ComicGenerateRequest`: `prompt: str = Field(..., min_length=1, max_length=500)`
  - `ComicPanel`: `panel_number: int`, `description: str`, `dialogue: str`, `image_base64: Optional[str]`
  - `ComicResponse`: `prompt: str`, `panels: list[ComicPanel]`, `created_at: datetime`
  - Add `model_config = ConfigDict(from_attributes=True)` for ORM compatibility

#### Phase 3: Backend Service

| Task | File | Status |
|------|------|--------|
| 2.2 | `src/app/services/comic_service.py` | ✅ |

- ✅ **2.2** Create `src/app/services/comic_service.py` using `huggingface_hub.InferenceClient`:
  - `generate_script(prompt: str) -> list[dict]` — Call `HuggingFaceH4/zephyr-7b-beta` to generate 3 panel descriptions + captions
  - `generate_image(description: str) -> str` — Call `stabilityai/stable-diffusion-xl-base-1.0`, return base64
  - `generate_comic(prompt: str) -> ComicResponse` — Orchestrate script + images
  - Handle API errors (rate limits → 429, failures → 503) with custom exceptions
  - Use structured prompt format for consistent 3-panel JSON output

#### Phase 4: Backend MVC

| Task | File | Status |
|------|------|--------|
| 3.1 | `src/app/controllers/comic.py` | ✅ |
| 3.2 | `src/app/views/comic.py` | ✅ |
| 3.3 | `src/app/templates/comic/index.html` | ✅ |
| 3.4 | `src/app/views/__init__.py` | ✅ |

- ✅ **3.1** Create `src/app/controllers/comic.py` following `hello.py` pattern:
  - `ComicController` class with static methods
  - `generate(data: ComicGenerateRequest) -> ComicResponse` — Call `ComicService.generate_comic()`

- ✅ **3.2** Create `src/app/views/comic.py` Blueprint following `hello.py` pattern:
  - `comic_bp = Blueprint('comic', __name__)`
  - `GET /comic` — Render `comic/index.html` template
  - `POST /api/comic/generate` — Validate with `ComicGenerateRequest`, call controller, return `ComicResponse` JSON
  - Return 400 on validation errors, 429/503 on HF API failures

- ✅ **3.3** Create `src/app/templates/comic/index.html` extending `base.html`:
  - Add `<div data-island="comic-generator" data-props='{}' class="...">` mount point
  - Include loading skeleton placeholder (3 gray boxes for panels)

- ✅ **3.4** Register blueprint in `src/app/views/__init__.py`:
  ```python
  from .comic import comic_bp
  app.register_blueprint(comic_bp)
  ```

#### Phase 5: Frontend

| Task | File | Status |
|------|------|--------|
| 4.1 | `frontend/src/types/index.ts` | ✅ |
| 4.2 | `frontend/src/islands/comic/ComicGenerator.tsx` | ✅ |
| 4.3 | `frontend/src/islands/comic/index.tsx` | ✅ |
| 4.4 | `frontend/src/main.ts` | ✅ |

- ✅ **4.1** Add TypeScript interfaces to `frontend/src/types/index.ts`:
  ```typescript
  export interface ComicPanel {
    panel_number: number
    description: string
    dialogue: string
    image_base64?: string
  }

  export interface ComicGenerateRequest {
    prompt: string
  }

  export interface ComicResponse {
    prompt: string
    panels: ComicPanel[]
    created_at: string
  }
  ```

- ✅ **4.2** Create `frontend/src/islands/comic/ComicGenerator.tsx` following `HelloIsland.tsx` pattern:
  - `useState` for: prompt, panels, loading, error
  - Textarea for prompt input (max 500 chars)
  - "Generate Comic" button with loading spinner and disabled state
  - 3-panel CSS grid layout displaying base64 images + dialogue captions
  - Error message display (red banner)
  - Call `POST /api/comic/generate` via fetch

- ✅ **4.3** Create `frontend/src/islands/comic/index.tsx` mount function:
  ```typescript
  import { createRoot } from 'react-dom/client'
  import { ComicGenerator } from './ComicGenerator'

  export function mount(element: HTMLElement, props: unknown): void {
    const root = createRoot(element)
    root.render(<ComicGenerator {...(props as object)} />)
  }
  ```

- ✅ **4.4** Register island in `frontend/src/main.ts` islandRegistry:
  ```typescript
  const islandRegistry: Record<string, () => Promise<IslandModule>> = {
    hello: () => import('./islands/hello'),
    'comic-generator': () => import('./islands/comic'),
  }
  ```

### P1 — Should Have (Polish, Testing & Quality)

#### Phase 6: Navigation

| Task | File | Status |
|------|------|--------|
| 5.1 | `src/app/templates/base.html` | ✅ |

- ✅ **5.1** Update `src/app/templates/base.html`:
  - Add navigation header with links to `/` (Hello) and `/comic` (Comic Generator)
  ```html
  <nav class="bg-white shadow">
    <div class="max-w-4xl mx-auto px-4 py-3 flex gap-4">
      <a href="/" class="text-gray-700 hover:text-blue-600">Hello</a>
      <a href="/comic" class="text-gray-700 hover:text-blue-600">Comic Generator</a>
    </div>
  </nav>
  ```

#### Phase 7: Testing

| Task | File | Status |
|------|------|--------|
| 6.1 | `tests/test_comic_service.py` | ✅ |
| 6.2 | `e2e/comic-generator.spec.ts` | ✅ |

- ✅ **6.1** Create `tests/test_comic_service.py` with mocked `InferenceClient`:
  - Test `generate_script()` returns list of 3 valid panel dicts
  - Test `generate_image()` returns non-empty base64 string
  - Test `generate_comic()` end-to-end orchestration
  - Test error handling: API timeout → raises exception, rate limit → 429, invalid response → validation error
  - Use `unittest.mock.patch` to mock `huggingface_hub.InferenceClient`

- ✅ **6.2** Create `e2e/comic-generator.spec.ts` with mocked API:
  - Use `page.route('/api/comic/generate', ...)` to mock API response
  - Test navigation to `/comic` shows form
  - Test form submission: enter prompt, click Generate, see loading state
  - Test success: 3 panels render with images (data-testid="panel-1", etc.) and captions
  - Test error state: mock 503, verify error banner displays

### P2 — Nice to Have (Future Enhancements)

_Not in scope for initial implementation._

- ❌ Panel count slider (1-6 panels instead of fixed 3)
- ❌ Download comic as PNG image
- ❌ Share comic via unique URL
- ❌ History of generated comics (requires database model)

---

## ✅ Base App (Complete)

> _Reference implementation pattern for Comic Generator_

| Area | Status |
|------|--------|
| `src/app/` | ✅ Flask app factory, models, views, controllers, schemas, templates, errors, logging |
| `frontend/` | ✅ React Islands, Vite, TypeScript, Tailwind, ESLint, Vitest |
| `scripts/` | ✅ bootstrap, setup, server, test, lint, typecheck, console, db-seed |
| `tests/` | ✅ 13 backend tests (pytest), 11 E2E tests (Playwright) |
| `.devcontainer/` | ✅ Python 3.12, PostgreSQL, Node.js |
| `.github/workflows/` | ✅ CI pipeline for lint, typecheck, test |

**Key Reference Files:**
- Schema: `src/app/schemas/hello.py`
- Controller: `src/app/controllers/hello.py`
- Views: `src/app/views/hello.py`
- Template: `src/app/templates/hello/index.html`
- Island Component: `frontend/src/islands/hello/HelloIsland.tsx`
- Island Mount: `frontend/src/islands/hello/index.tsx`
- Types: `frontend/src/types/index.ts`
- Registry: `frontend/src/main.ts`

---

## Validation Commands

```bash
# After implementation, run all validation steps:

# 1. Install new dependency
pip install -r requirements.txt

# 2. Run linters
script/lint                        # flake8 + eslint

# 3. Run type checkers
script/typecheck                   # mypy + tsc

# 4. Run unit tests
script/test                        # pytest + vitest

# 5. Run E2E tests
script/test-e2e                    # Playwright

# 6. Manual verification (requires HF_API_TOKEN in .env):
export HF_API_TOKEN=your_token_here
script/server                      # Start Flask + Vite
# Visit http://localhost:5000/comic
# Enter a prompt and verify 3-panel comic generates
```

## Implementation Order

Execute tasks in this order:

1. **Configuration** (1.1-1.3) — Install dependency, add config
2. **Schemas** (2.1) — Define request/response models
3. **Service** (2.2) — Implement Hugging Face API integration
4. **Controller** (3.1) — Wire service to controller
5. **Views** (3.2) — Create routes and blueprint
6. **Template** (3.3) — Create HTML with island mount point
7. **Registration** (3.4) — Register blueprint
8. **Frontend Types** (4.1) — Add TypeScript interfaces
9. **Island Component** (4.2) — Build React UI
10. **Island Mount** (4.3) — Create mount function
11. **Island Registry** (4.4) — Register in main.ts
12. **Navigation** (5.1) — Add nav link
13. **Unit Tests** (6.1) — Test service with mocks
14. **E2E Tests** (6.2) — Test full flow with mocked API
