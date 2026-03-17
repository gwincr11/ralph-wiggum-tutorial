# Hello Feature Pattern - Complete Documentation

This document provides complete architecture documentation for the Hello feature, serving as a replication template for new features like Comic.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Structure](#backend-structure)
3. [Frontend Structure](#frontend-structure)
4. [Data Flow](#data-flow)
5. [Implementation Checklist](#implementation-checklist)
6. [Code Templates](#code-templates)
7. [Common Mistakes](#common-mistakes)

---

## Architecture Overview

The Hello feature demonstrates a **React Islands Architecture** with:
- **Backend:** Flask + SQLAlchemy + Pydantic
- **Frontend:** React + TypeScript
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Pattern:** Layered architecture with clear separation of concerns

### Layer Diagram

```
┌─ Backend (Flask) ─────────────────┬─ Frontend (React) ──────────────┐
│                                   │                                 │
│  Routes (views/hello.py)          │  Islands (React Components)     │
│  ├─ GET /                         │  ├─ HelloIsland.tsx            │
│  ├─ GET /api/hello               │  │   (interactive component)     │
│  ├─ POST /api/hello              │  └─ index.tsx (mount)           │
│  ├─ GET /api/hello/<id>          │                                 │
│  └─ DELETE /api/hello/<id>       │  main.ts (Island Registry)      │
│                                   │  ├─ Auto-discovers islands      │
│  Controllers                      │  ├─ Dynamic imports             │
│  ├─ get_all()                    │  └─ Mounts with props           │
│  ├─ get_by_id()                  │                                 │
│  ├─ create()                     │  Types (interface)              │
│  └─ delete()                     │  ├─ Hello                      │
│                                   │  └─ HelloCreate                │
│  Models (SQLAlchemy)              │                                 │
│  ├─ id                            │  Styling (Tailwind)            │
│  ├─ message                       │                                 │
│  └─ created_at                    │                                 │
│                                   │                                 │
│  Schemas (Pydantic)               │                                 │
│  ├─ HelloCreate (input)           │                                 │
│  └─ HelloResponse (output)        │                                 │
│                                   │                                 │
│  Templates (Jinja2)               │                                 │
│  └─ index.html                    │                                 │
│     (with data-island mount)      │                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## Backend Structure

### 1. Models (src/app/models/hello.py)

```python
from datetime import datetime
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import db

class Hello(db.Model):
    """Hello model representing a greeting message."""
    __tablename__ = 'hello'

    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

**Key Points:**
- Uses modern SQLAlchemy with `Mapped` type hints
- Simple schema: id, message, timestamp
- Database will auto-order by created_at

### 2. Schemas (src/app/schemas/hello.py)

```python
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class HelloCreate(BaseModel):
    """Input validation for creating a Hello."""
    message: str = Field(..., min_length=1, max_length=255)

class HelloResponse(BaseModel):
    """Output serialization for API responses."""
    id: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Key Points:**
- `HelloCreate` validates incoming requests (POST)
- `HelloResponse` serializes database objects for API
- `from_attributes=True` allows Pydantic to convert ORM objects
- Field validation rules prevent invalid data

### 3. Controllers (src/app/controllers/hello.py)

```python
from ..models import Hello, db
from ..schemas import HelloCreate

class HelloController:
    """Controller with CRUD operations."""

    @staticmethod
    def get_all() -> list[Hello]:
        """Retrieve all Hello records, newest first."""
        return Hello.query.order_by(Hello.created_at.desc()).all()

    @staticmethod
    def get_by_id(hello_id: int) -> Hello | None:
        """Retrieve a specific Hello by ID."""
        return db.session.get(Hello, hello_id)

    @staticmethod
    def create(data: HelloCreate) -> Hello:
        """Create and persist a new Hello."""
        hello = Hello(message=data.message)
        db.session.add(hello)
        db.session.commit()
        return hello

    @staticmethod
    def delete(hello_id: int) -> bool:
        """Delete a Hello. Returns True if successful."""
        hello = db.session.get(Hello, hello_id)
        if hello:
            db.session.delete(hello)
            db.session.commit()
            return True
        return False
```

**Key Points:**
- All methods are static (functional approach)
- Encapsulates database logic
- Views call controller, not model directly
- Returns model objects, not JSON

### 4. Views/Routes (src/app/views/hello.py)

```python
from flask import Blueprint, render_template, jsonify, request, abort
from pydantic import ValidationError
from ..controllers import HelloController
from ..schemas import HelloCreate, HelloResponse

hello_bp = Blueprint('hello', __name__)

@hello_bp.route('/')
def index():
    """Render main page with React island."""
    hellos = HelloController.get_all()
    hellos_data = [HelloResponse.model_validate(h).model_dump() for h in hellos]
    return render_template('hello/index.html', hellos=hellos_data)

@hello_bp.route('/api/hello', methods=['GET'])
def api_list():
    """List all hellos as JSON."""
    hellos = HelloController.get_all()
    return jsonify([HelloResponse.model_validate(h).model_dump() for h in hellos])

@hello_bp.route('/api/hello', methods=['POST'])
def api_create():
    """Create a new hello."""
    try:
        data = HelloCreate.model_validate(request.json)
    except ValidationError as e:
        return jsonify(error="Validation Error", details=e.errors()), 400

    hello = HelloController.create(data)
    return jsonify(HelloResponse.model_validate(hello).model_dump()), 201

@hello_bp.route('/api/hello/<int:hello_id>', methods=['GET'])
def api_get(hello_id: int):
    """Get a single hello by ID."""
    hello = HelloController.get_by_id(hello_id)
    if not hello:
        abort(404)
    return jsonify(HelloResponse.model_validate(hello).model_dump())

@hello_bp.route('/api/hello/<int:hello_id>', methods=['DELETE'])
def api_delete(hello_id: int):
    """Delete a hello by ID."""
    if HelloController.delete(hello_id):
        return '', 204
    abort(404)
```

**Key Points:**
- Blueprint for modular routing
- Separates HTML and JSON endpoints
- Validates all input with Pydantic schemas
- Proper HTTP status codes: 201 (create), 204 (delete), 400 (validation), 404 (not found)

### 5. Templates (src/app/templates/hello/index.html)

```html
{% extends "base.html" %}

{% block title %}Hello - Ralph Wiggum Tutorial{% endblock %}

{% block content %}
<main class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8 text-gray-800">Hello World</h1>

    {# React Island Mount Point #}
    <div
        data-island="hello"
        data-props='{{ hellos | tojson | safe }}'
        class="bg-white rounded-lg shadow p-6"
    >
        {# Fallback for no JavaScript #}
        <noscript>
            <p class="text-gray-600">JavaScript is required for interactive features.</p>
        </noscript>

        {# Loading state #}
        <div class="animate-pulse">
            <div class="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        </div>
    </div>

    {# Server-rendered fallback #}
    <section class="mt-8">
        <h2 class="text-xl font-semibold mb-4">Messages (Server Rendered)</h2>
        {% if hellos %}
            <ul class="space-y-2">
                {% for hello in hellos %}
                    <li class="p-3 bg-white rounded shadow-sm">
                        {{ hello.message }}
                        <span class="text-gray-400 text-sm">
                            {{ hello.created_at.strftime('%Y-%m-%d %H:%M') }}
                        </span>
                    </li>
                {% endfor %}
            </ul>
        {% else %}
            <p class="text-gray-500">No messages yet.</p>
        {% endif %}
    </section>
</main>
{% endblock %}
```

**Key Points:**
- `data-island="hello"` identifies the React mount point
- `data-props='{{ hellos | tojson | safe }}'` passes server data to React
- Includes fallback content for no-JavaScript scenarios
- Shows loading state while JavaScript loads

### 6. Blueprint Registration (src/app/views/__init__.py)

```python
from flask import Flask

def register_blueprints(app: Flask) -> None:
    """Register all blueprints with Flask."""
    from .hello import hello_bp

    app.register_blueprint(hello_bp)
```

---

## Frontend Structure

### 1. TypeScript Types (frontend/src/types/index.ts)

```typescript
/**
 * API response type - matches backend schema
 */
export interface Hello {
  id: number
  message: string
  created_at: string  // ISO 8601 format
}

/**
 * Request payload type
 */
export interface HelloCreate {
  message: string
}
```

**Key Points:**
- Must match backend Pydantic schemas exactly
- `created_at` is a string from JSON API
- No ORM details in frontend types

### 2. React Component (frontend/src/islands/hello/HelloIsland.tsx)

```typescript
import React, { useState, useEffect } from 'react'
import type { Hello, HelloCreate } from '@/types'

interface HelloIslandProps {
  initialData?: Hello[]
}

export function HelloIsland({ initialData = [] }: HelloIslandProps) {
  // State
  const [hellos, setHellos] = useState<Hello[]>(initialData)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch fresh data on mount
  useEffect(() => {
    fetchHellos()
  }, [])

  async function fetchHellos() {
    try {
      const response = await fetch('/api/hello')
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setHellos(data)
    } catch (e) {
      console.error('Failed to fetch:', e)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim()) return

    setLoading(true)
    setError(null)

    try {
      const payload: HelloCreate = { message: message.trim() }
      const response = await fetch('/api/hello', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to create')
      }

      const newHello = await response.json()
      setHellos([newHello, ...hellos])  // Add to top
      setMessage('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number) {
    try {
      const response = await fetch(`/api/hello/${id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Failed to delete')
      setHellos(hellos.filter(h => h.id !== id))
    } catch (e) {
      console.error('Failed to delete:', e)
    }
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter a greeting..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
          disabled={loading}
          maxLength={255}
        />
        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Adding...' : 'Add'}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* List */}
      <div className="space-y-2">
        {hellos.length === 0 ? (
          <p className="text-gray-500 italic">No greetings yet.</p>
        ) : (
          hellos.map((hello) => (
            <div key={hello.id} className="flex justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <span>{hello.message}</span>
                <span className="text-gray-400 text-sm ml-2">
                  {new Date(hello.created_at).toLocaleDateString()}
                </span>
              </div>
              <button
                onClick={() => handleDelete(hello.id)}
                className="text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
```

**Key Points:**
- Receives `initialData` from server (no loading state)
- `useEffect` on mount fetches fresh data from `/api/hello`
- Form handles validation and submission
- Delete functionality filters list
- Error handling with user messages

### 3. Mount Function (frontend/src/islands/hello/index.tsx)

```typescript
import { createRoot } from 'react-dom/client'
import { HelloIsland } from './HelloIsland'
import type { Hello } from '@/types'

export function mount(element: HTMLElement, props: unknown): void {
  element.innerHTML = ''
  const initialData = Array.isArray(props) ? (props as Hello[]) : []
  const root = createRoot(element)
  root.render(<HelloIsland initialData={initialData} />)
}
```

**Key Points:**
- Required `mount(element, props)` signature
- Called by `main.ts` when island is discovered
- Clears fallback content
- Parses props safely

### 4. Island Registry (frontend/src/main.ts)

```typescript
const islandRegistry: Record<string, () => Promise<IslandModule>> = {
  hello: () => import('./islands/hello'),
  // Add more islands here
}

async function mountIslands(): Promise<void> {
  const islands = document.querySelectorAll<HTMLElement>('[data-island]')

  for (const element of islands) {
    const islandName = element.getAttribute('data-island')
    if (!islandName) continue

    const importFn = islandRegistry[islandName]
    if (!importFn) continue

    try {
      const module = await importFn()
      const props = parseProps(element)
      module.mount(element, props)
    } catch (e) {
      console.error(`Failed to mount "${islandName}":`, e)
    }
  }
}
```

**Key Points:**
- Automatically scans DOM for `[data-island]` attributes
- Dynamically imports island modules
- Parses `data-props` and passes to mount function
- Error handling for missing or failed islands

---

## Data Flow

### Request/Response Examples

#### 1. GET / (HTML Page)

**Request:**
```
GET /
```

**Backend Processing:**
```python
hellos = HelloController.get_all()  # [Hello(...), Hello(...)]
hellos_data = [HelloResponse.model_validate(h).model_dump() for h in hellos]
return render_template('hello/index.html', hellos=hellos_data)
```

**Response:**
```html
<html>
  <body>
    <div data-island="hello" data-props='[{"id": 1, "message": "Hi", "created_at": "2024-01-01T12:00:00"}]'>
      <div class="animate-pulse"><!-- loading skeleton --></div>
    </div>
    <section><!-- server-rendered list --></section>
  </body>
</html>
```

**Frontend:**
- Browser renders HTML with skeleton
- `main.ts` finds `[data-island]` element
- Imports `islands/hello`, calls `mount(element, props)`
- React component renders with `initialData`

#### 2. POST /api/hello (Create)

**Request:**
```json
POST /api/hello
Content-Type: application/json

{
  "message": "Hello, World!"
}
```

**Backend Processing:**
```python
data = HelloCreate.model_validate(request.json)  # Validates
hello = HelloController.create(data)              # Creates + commits
return jsonify(HelloResponse.model_validate(hello).model_dump()), 201
```

**Response:**
```json
201 Created
{
  "id": 2,
  "message": "Hello, World!",
  "created_at": "2024-01-01T12:05:00"
}
```

**Frontend:**
```javascript
const newHello = await response.json()
setHellos([newHello, ...hellos])  // Add to top
```

#### 3. DELETE /api/hello/1

**Request:**
```
DELETE /api/hello/1
```

**Backend Processing:**
```python
if HelloController.delete(1):
    return '', 204
abort(404)
```

**Response:**
```
204 No Content
(empty body)
```

**Frontend:**
```javascript
setHellos(hellos.filter(h => h.id !== 1))  // Remove from list
```

---

## Implementation Checklist

### Backend Setup (6 files)

- [ ] **Model** (`src/app/models/comic.py`)
  - [ ] Create `Comic` class with SQLAlchemy
  - [ ] Add fields: `id`, resource fields, `created_at`
  - [ ] Use `Mapped` type hints

- [ ] **Schema** (`src/app/schemas/comic.py`)
  - [ ] Create `ComicCreate` with input validation
  - [ ] Create `ComicResponse` with output fields
  - [ ] Add `model_config = ConfigDict(from_attributes=True)`

- [ ] **Controller** (`src/app/controllers/comic.py`)
  - [ ] Implement `get_all()` with ordering
  - [ ] Implement `get_by_id(id)`
  - [ ] Implement `create(data)`
  - [ ] Implement `delete(id)`

- [ ] **Views** (`src/app/views/comic.py`)
  - [ ] Create `comic_bp` blueprint
  - [ ] Implement `GET /` (HTML)
  - [ ] Implement `GET /api/comics` (JSON list)
  - [ ] Implement `POST /api/comics` (create, 201)
  - [ ] Implement `GET /api/comics/<id>` (get one, 404)
  - [ ] Implement `DELETE /api/comics/<id>` (delete, 204)

- [ ] **Template** (`src/app/templates/comic/index.html`)
  - [ ] Extend `base.html`
  - [ ] Add `<div data-island="comic" data-props='{{ comics | tojson | safe }}'>`
  - [ ] Include fallback content

- [ ] **Blueprint Registration** (`src/app/views/__init__.py`)
  - [ ] Import `comic_bp`
  - [ ] Register blueprint

### Database Setup

- [ ] Run migration
  ```bash
  flask db migrate -m "Add Comic model"
  flask db upgrade
  ```

### Frontend Setup (4 files)

- [ ] **Types** (`frontend/src/types/index.ts`)
  - [ ] Add `interface Comic { ... }`
  - [ ] Add `interface ComicCreate { ... }`

- [ ] **Component** (`frontend/src/islands/comic/ComicIsland.tsx`)
  - [ ] Create component with props
  - [ ] Add useState hooks
  - [ ] Implement `fetchComics()`
  - [ ] Implement `handleSubmit()`
  - [ ] Implement `handleDelete()`
  - [ ] Render form, error, list

- [ ] **Mount** (`frontend/src/islands/comic/index.tsx`)
  - [ ] Export `mount(element, props)` function
  - [ ] Create React root and render component

- [ ] **Registry** (`frontend/src/main.ts`)
  - [ ] Add to `islandRegistry`:
    ```typescript
    comic: () => import('./islands/comic'),
    ```

---

## Code Templates

### Creating a New Feature (Comic)

#### Backend Model

```python
from datetime import datetime
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import db

class Comic(db.Model):
    __tablename__ = 'comic'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

#### Backend Schema

```python
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ComicCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    image_url: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=1000)

class ComicResponse(BaseModel):
    id: int
    title: str
    image_url: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

#### Frontend Types

```typescript
export interface Comic {
  id: number
  title: string
  image_url: string
  description: string
  created_at: string
}

export interface ComicCreate {
  title: string
  image_url: string
  description: string
}
```

---

## Common Mistakes

### Backend

1. **Forgetting `model_config`**
   ```python
   # ❌ Wrong - Won't convert ORM objects
   class ComicResponse(BaseModel):
       id: int
       title: str

   # ✓ Correct
   class ComicResponse(BaseModel):
       id: int
       title: str
       model_config = ConfigDict(from_attributes=True)
   ```

2. **Not validating input**
   ```python
   # ❌ Wrong - Accepts any data
   hello = HelloController.create(request.json)

   # ✓ Correct - Validates first
   data = HelloCreate.model_validate(request.json)
   hello = HelloController.create(data)
   ```

3. **Wrong HTTP status codes**
   ```python
   # ❌ Wrong
   return jsonify(hello), 200  # POST should be 201
   return '', 200              # DELETE should be 204

   # ✓ Correct
   return jsonify(hello), 201
   return '', 204
   ```

4. **Not ordering results**
   ```python
   # ❌ Wrong - Random order
   return Hello.query.all()

   # ✓ Correct - Newest first
   return Hello.query.order_by(Hello.created_at.desc()).all()
   ```

### Frontend

5. **Hardcoded URLs**
   ```typescript
   // ❌ Wrong - breaks in different environments
   fetch('http://localhost:5000/api/hello')

   // ✓ Correct - relative paths
   fetch('/api/hello')
   ```

6. **Missing island registry**
   ```typescript
   // ❌ Wrong - island won't mount
   // (forgot to add to islandRegistry)

   // ✓ Correct
   const islandRegistry = {
     comic: () => import('./islands/comic'),
   }
   ```

7. **Forgetting `data-props`**
   ```html
   <!-- ❌ Wrong - no initial data -->
   <div data-island="comic"></div>

   <!-- ✓ Correct - passes server data -->
   <div data-island="comic" data-props='{{ comics | tojson | safe }}'></div>
   ```

8. **Race conditions**
   ```typescript
   // ❌ Wrong - state updates may race
   handleDelete(id) {
     fetch(...).then(() => {
       setHellos(filter...)  // Might use stale data
     })
   }

   // ✓ Correct - use callback form
   handleDelete(id) {
     fetch(...).then(() => {
       setHellos(hellos => hellos.filter(h => h.id !== id))
     })
   }
   ```

---

## Testing

### Local Development

```bash
# Terminal 1: Backend
python -m flask run

# Terminal 2: Frontend
cd frontend && npm run dev

# Browser
http://localhost:5000
```

### Testing Checklist

- [ ] Page loads with data
- [ ] Create a new item (POST /api/hello)
- [ ] Item appears at top of list
- [ ] Delete an item (DELETE /api/hello/:id)
- [ ] Item removed from list
- [ ] Refresh page - data persists
- [ ] Disable JavaScript - fallback content visible
- [ ] Form validation works
- [ ] Error messages display

---

## Key Principles

### Progressive Enhancement
- ✅ HTML works without JavaScript
- ✅ JavaScript enhances with React interactivity
- ✅ No loading spinner needed (instant content)

### Islands Architecture
- 🏝️ Partial hydration (only interactive parts)
- 🏝️ Self-contained (each island is independent)
- ��️ Colocated (UI, logic, state together)

### Type Safety
- ✅ Pydantic validates on backend
- ✅ TypeScript interfaces on frontend
- ✅ Runtime validation prevents bugs

### Layered Design
- ✅ Models (database schema)
- ✅ Schemas (validation)
- ✅ Controllers (business logic)
- ✅ Views (HTTP endpoints)
- ✅ Templates (HTML)
- ✅ Components (React UI)

---

## Summary

The Hello pattern provides a complete, production-ready architecture for building CRUD features:

1. **Backend:** Flask blueprints with SQLAlchemy models and Pydantic validation
2. **Frontend:** React islands with TypeScript for type safety
3. **Database:** SQLAlchemy ORM with proper migrations
4. **API:** RESTful endpoints with proper status codes
5. **Enhancement:** Progressive enhancement with React islands

Follow this pattern for consistent, maintainable code across features.
