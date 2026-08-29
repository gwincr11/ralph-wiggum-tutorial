# Feature: Home Page Weather Forecast Widget

## Feature Description
Add a weather forecast widget to the home page that uses the browser's Geolocation API to detect the user's location, fetches current weather and a 5-day forecast from the National Weather Service (weather.gov) API via a backend proxy, and displays it with weather icons, current temperature, high/low temperatures, and a 5-day forecast strip. If the user denies location access, the widget is hidden entirely.

## User Story
As a visitor to the site
I want to see my local weather forecast on the home page
So that I can quickly check current conditions and the upcoming 5-day forecast without leaving the site

## Problem Statement
The home page currently only shows the Hello greeting island. There is no contextual, location-aware content that gives users a reason to return or that personalizes their experience. Adding a weather widget provides useful, dynamic content that leverages the browser's geolocation capabilities and a free, reliable government API.

## Solution Statement
Implement a weather widget as a new React Island on the home page with a backend proxy to handle API requests.

The widget will:
1.  Use the browser `navigator.geolocation.getCurrentPosition()` API to get the user's lat/lng
2.  Call the backend API `/api/weather?lat={lat}&lng={lng}`
3.  The backend will call the weather.gov API (`/points` → `forecast`) with the required `User-Agent` header
4.  Display: weather icon, current temperature, today's high/low, and a 5-day forecast strip
5.  If the user blocks location or the API fails, the widget renders nothing (invisible)

**Architecture decision:** Weather data fetching happens via a **backend proxy** because the NWS API requires a custom `User-Agent` header identifying the application, which browsers block for security reasons. A proxy also allows for caching and error handling closer to the source.

## Relevant Files

**Existing files to modify:**
- `src/app/templates/hello/index.html` — Add a new `data-island="weather"` mount point
- `frontend/src/main.ts` — Register the new `weather` island
- `requirements.txt` — Add `requests` library
- `src/app/__init__.py` — Register the new weather blueprint

**New Files:**
- `src/app/views/weather.py` — Flask blueprint for weather proxy
- `src/app/services/weather_service.py` — Service to handle NWS API calls and caching
- `tests/test_weather.py` — Backend tests for the weather proxy
- `frontend/src/islands/weather/WeatherIsland.tsx` — Main React component
- `frontend/src/islands/weather/index.tsx` — Island mount function
- `frontend/src/islands/weather/WeatherIcon.tsx` — Icon mapping component
- `frontend/tests/islands/weather/WeatherIsland.test.tsx` — Frontend unit tests
- `e2e/weather.spec.ts` — E2E tests

## Implementation Plan

### Phase 1: Backend Implementation
1.  Add `requests` to `requirements.txt`.
2.  Create `WeatherService` class in `src/app/services/weather_service.py`:
    -   Method `get_forecast(lat, lng)`
    -   Calls NWS `/points/{lat},{lng}` to get forecast URL.
    -   Calls forecast URL to get data.
    -   Returns simplified weather data structure.
    -   Implements simple in-memory caching (e.g., `lru_cache` or a dictionary with timestamps) to respect NWS politeness.
    -   Handles errors (timeouts, 500s) gracefully.
3.  Create `weather_bp` in `src/app/views/weather.py`:
    -   Route `GET /api/weather` accepting `lat` and `lng` query params.
    -   Calls `WeatherService`.
    -   Returns JSON response.
4.  Register blueprint in `create_app`.

### Phase 2: Frontend Implementation
1.  Create `WeatherIcon` component.
2.  Create `WeatherIsland` component:
    -   Request geolocation.
    -   Fetch from `/api/weather`.
    -   Render loading/data/error states.
3.  Register island in `main.ts`.
4.  Add mount point to `index.html`.

### Phase 3: Testing
1.  Backend tests: Mock external API calls, test success/failure/caching.
2.  Frontend tests: Mock fetch to backend, test rendering.
3.  E2E tests: Verify full flow with mocked geolocation.

## Step by Step Tasks

### Step 1: Backend Setup
- Add `requests>=2.31.0` to `requirements.txt`.
- Run `pip install -r requirements.txt`.

### Step 2: Weather Service
- Create `src/app/services/weather_service.py`.
- Implement `get_forecast(lat, lng)`:
  -   Headers: `{'User-Agent': '(RalphWiggumTutorial, tutorial@example.com)'}`
  -   Logic:
      1.  Check cache (optional but recommended).
      2.  GET `https://api.weather.gov/points/{lat},{lng}`.
      3.  Extract `properties.forecast` URL.
      4.  GET forecast URL.
      5.  Return data.

### Step 3: Weather Blueprint
- Create `src/app/views/weather.py`.
- Define `weather_bp`.
- Route `/api/weather`:
  -   Validate `lat` and `lng`.
  -   Call service.
  -   Return JSON.
- Register in `src/app/__init__.py`.

### Step 4: Backend Tests
- Create `tests/test_weather.py`.
- Test `/api/weather` endpoint.
- Mock `requests.get` to simulate NWS responses.

### Step 5: Frontend Components
- Create `frontend/src/islands/weather/WeatherIcon.tsx` (same as original plan).
- Create `frontend/src/islands/weather/WeatherIsland.tsx`:
  -   Fetch `/api/weather?lat=${lat}&lng=${lng}`.
  -   Render data.
- Create `frontend/src/islands/weather/index.tsx`.

### Step 6: Integration
- Add to `frontend/src/main.ts`.
- Add to `src/app/templates/hello/index.html`.

### Step 7: Verification
- Run backend tests: `pytest tests/test_weather.py`.
- Run frontend tests: `npm test`.
- Run E2E tests: `npx playwright test`.

## Acceptance Criteria
1.  ✅ Widget appears when location is granted.
2.  ✅ Widget uses backend proxy to fetch data.
3.  ✅ Backend handles NWS User-Agent requirement.
4.  ✅ Tests pass (backend, frontend, E2E).
