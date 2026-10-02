# Take-home A: Agent Run Explorer

## What this is

Every agent our platform runs leaves a trace: which steps it took, which tools it
called, how long each took, how many tokens it burned, and whether it finished.
Support and delivery engineers currently read those traces by grepping JSON files,
which is exactly as pleasant as it sounds.

Build them a small web tool to browse and understand agent runs.

You have a dataset of 201 runs in [data/runs.jsonl](data/runs.jsonl). Each line is one
run. Read a few lines before you start designing anything.

## Timebox and expectations

Budget around 8 hours of focused work, spread over up to 4 days. We would much rather
see the "must build" section done well than all three sections done badly. If you run
out of time, stop, and write down in `DECISIONS.md` what you would have done next.

Nothing here is a trick. The dataset is deliberately a bit messy, the way production
data is. Part of what we are assessing is whether you notice.

## Stack

- Backend in Python. FastAPI preferred; Flask or Django REST are acceptable.
- Frontend in Next.js with the App Router, TypeScript, and React.
- Two processes talking over HTTP. Do not put the data loading inside Next.js API
  routes and skip the Python service.
- Styling is your call. Tailwind, CSS modules, plain CSS, a component library, all fine.
  We are not scoring visual polish, but we are scoring whether the thing is usable.
- No database required. Loading the JSONL into memory at startup is a reasonable
  choice for 201 records. Say in `DECISIONS.md` what you would change if the file
  had 20 million.

## Must build

### Backend

`GET /api/runs` returns a page of runs, with:

- pagination, and a total count so the UI can render "showing 1-25 of 201"
- filter by `status` and by `agent`, both accepting more than one value
- filter by a `started_at` date range
- a text search across the run's prompt
- sort by `started_at`, `duration_ms`, or `cost_usd`, ascending or descending

Filters must compose. Two agents plus one status plus a date range plus a sort is a
single valid request, not four separate endpoints.

Do not return each run's full `steps` array from the list endpoint.

`GET /api/runs/{id}` returns one run including its steps, and 404s properly for an
id that does not exist.

`GET /api/stats` returns aggregates the dashboard can render without further
computation on the client:

- run count and success rate, overall and per agent
- median and p95 duration for completed runs
- total cost per agent
- run counts per day over the dataset's date range

`POST /api/runs/{id}/explain` returns a short natural-language explanation of what
the run did and, if it failed, where it went wrong. Stream the response to the client
as it is produced.

The explain endpoint must work with no API key configured. Ship a mock provider,
selected by an environment variable, that returns deterministic canned text with a
small artificial delay so the streaming path is exercised. Use a real model provider
behind the same interface if you want to; use a free tier and never commit a key.
We will grade with the mock.

### Frontend

`/runs` is a server-rendered list. Filter, search, sort, and page state all live in
the URL search params, so that a filtered view can be copied into Slack and reopened
by someone else. Handle the loading, empty, and error cases visibly.

`/runs/[id]` shows one run: its metadata, its error if it has one, and its steps in
order with duration and tokens per step. Step inputs and outputs should be readable
without leaving the page. An "Explain this run" control calls the explain endpoint
and renders the text as it streams in, not after it completes.

`/dashboard` renders the `/api/stats` data. Two or three charts is enough. Pick a
chart library, or draw SVG yourself.

### Tests

At least three backend tests with real assertions:

- one that proves two filters compose correctly
- one that checks a statistic against a value you computed by hand

At least one frontend test, or a paragraph in `DECISIONS.md` explaining what you would
test and why you skipped it. "No time" is an acceptable reason if the rest is solid.

## Should build, if time allows

- A `tool` filter that matches runs containing a step using that tool.
- Deep-link to a specific step, so `/runs/run_0042#step-3` opens with that step expanded.
- Keyboard navigation in the list: arrow keys move the selection, Enter opens.
- A visible request-duration or request-count indicator so a reviewer can see the
  frontend is not refetching everything on every keystroke.

## Stretch, purely optional

- Cursor pagination alongside offset pagination, with a note on the tradeoff.
- Handle a run with 500 steps without the detail page stuttering.
- Docker Compose that brings both services up with one command.

## Things you have to decide yourself

We left these underspecified on purpose. Any defensible answer scores; an
undocumented answer does not. Put a sentence on each in `DECISIONS.md`.

1. Some runs have `cost_usd: null`. Decide what "total cost per agent" means when
   some rows are unpriced, and make the UI honest about it.
2. Runs with status `running` have no `ended_at` and no `duration_ms`. Decide how they
   sort and whether they count toward success rate.
3. At least one record in the dataset will break a naive loader. Find it. Decide what
   to do about it, and make sure the API does not silently return something wrong.
4. `p95 duration` over a filtered set: does your `/api/stats` respect the filters the
   user has applied on the list page, or is it always global? Either is fine. Pick one
   and be consistent.

## Using AI tools

Use them. Claude, Copilot, Cursor, whatever you normally use. We use them too.

The condition: you own every line you submit. In the follow-up interview we will open
your repo, point at code, and ask why it is written that way, what a given type is at
that point, and what breaks if we delete a line. Candidates who cannot answer those
questions about their own submission do not advance, regardless of how good the code
looks. Do not submit code you have not read.

## Submitting

Push to a public GitHub repo and send us the link.

Your repo must have:

- `README.md` with setup steps that work on a clean machine. Assume the reviewer has
  Python and Node and nothing else. If a step is missing, we will not guess it.
- `DECISIONS.md` covering the four decisions above, anything you noticed about the
  data, what you would do with another day, and which parts you are least happy with.
  Half a page is plenty. Honest beats impressive here.
- `.env.example` listing every variable you read. No real keys, ever.
- Commit history that shows the work: a series of small commits with messages a
  reviewer can follow. One commit called "initial commit" containing the whole project
  is an automatic fail, even if the code is excellent.

We will clone it, follow your README, and expect to be looking at a working app inside
ten minutes. Test that path on a fresh clone before you send it.

Questions about the brief are welcome and never count against you. Email us.
