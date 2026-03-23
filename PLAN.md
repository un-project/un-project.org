# Agent Mission

Goal

    Build a web application that allows users to explore United Nations meetings by browsing or searching transcripts and voting records.

The website must allow users to:
- Browse UN meetings
- Read meeting transcripts
- Search speeches and statements
- View country profiles
- View speaker profiles
- View voting records

The application must initially support the following UN bodies:
- United Nations General Assembly (GA)
- United Nations Security Council (SC)

Only GA transcripts are currently available, but the architecture must support both.

# Technology Stack

The agent must build the application using:

Backend:
- Django
- PostgreSQL
- Django ORM

Infrastructure:
- Docker
- Docker Compose

Frontend:
- Django templates (initially)
- Minimal JavaScript
- No CSS framework

The application must be fully runnable using Docker Compose.

# Existing Database

The data already exists in a PostgreSQL database.

Database connection:

    postgresql://myuser:mypassword@localhost:5432/unproject

The Django project should connect to this database and use the existing schema.

The agent should generate Django models that map to the existing tables.

Database Schema Overview

    Table	Description
    countries	UN member states (name, ISO-2, ISO-3)
    speakers	People who spoke; linked to a country
    documents	One row per meeting PDF (symbol, date, session, location)
    document_items	Agenda items and named sections within a meeting
    stage_directions	Italic procedural text (adoptions, suspensions, …)
    speeches	One speech segment per speaker turn
    resolutions	Draft/adopted resolutions
    votes	One voting event per resolution per meeting
    country_votes	Per-country vote position for recorded votes
    amendments	Reserved for future use

Key relationships:

    speeches → speakers → countries
    votes → resolutions
    country_votes → votes + countries

All content rows are linked to:
- documents
- document_items

# Core Website Features (MVP)

## Global Search

A search bar must be present at the top of every page.

Search behavior:

Default search:

    full-text search on speech text

Optional filters:

    body (GA / SC)

    country

    speaker

    meeting

    resolution

Search results should display:

    speech excerpt

    speaker name

    country

    meeting

    date

Clicking a result opens the full meeting transcript, with the searched text highlighted.

# Pages to Implement

## Homepage

Displays:
- recent meetings
- recent speeches
- recent votes (future)

This acts as an activity feed.

## Meeting Page

URL example: /meeting/A-78-PV-12

Displays:
- meeting metadata
- agenda items
- full transcript

## Speaker Page

URL example: /speaker/123

Displays:
- speaker name
- country
- photo (if available)
- list of speeches
- statistics:
    - number of speeches
    - meetings attended

## Country Page

URL example: /country/FRA

Displays:
- country name
- country flag
- representatives who spoke
- voting history
- speeches by that country

## Meetings List

Accessible from the menu.

Displays:
- list of meetings
- filter by session
- filter by year
- filter by body

# Navigation Structure

The website must contain a top navigation bar.

Structure:

    Search Bar
    
    General Assembly ▼
        Homepage
        News
        Meetings
    
    Security Council ▼
        Homepage
        News
        Meetings
    
    More ▼
        Blog
        Terms

# Transcript Display

Meeting transcripts must:
- display speeches sequentially
- clearly show speaker changes
- allow linking to specific speeches

Example anchor: /meeting/A-78-PV-12#speech-145

# Search Engine

The search system should use:

PostgreSQL full-text search (not django LIKE) on: speeches.text

Indexes must be created to ensure fast search.

Create a Materialized View for Search.

# Static Assets

The site should support:

Country flags (ISO code based)

Example: /static/flags/FRA.svg

Speaker photos (optional): /static/speakers/{id}.jpg

# Docker Setup

The repository must include:
- docker-compose.yml
- Dockerfile
- .env

Services:
- web (django)
- db (postgres)

Running the site should only require:

    docker compose up

# Recommended Django App Structure

    un_site/
    
    core
    meetings
    speeches
    countries
    speakers
    votes
    search

# Performance Requirements

The agent must implement:
- pagination on long lists
- indexed search
- lazy loading of transcripts if needed

# Implemented Features (Originally Future)

These were listed as future features and have since been implemented:
- voting visualizations — interactive dc.js charts (position, year, category) on country pages and at `/votes/`
- country voting alignment graphs — similarity charts comparing a country's votes to others
- JSON API access — read-only REST API at `/api/` (meetings, speakers, resolutions) and `/votes/api/<iso3>/` (country votes and similarity scores)
- GA/SC body filter — country profiles and vote API accept `?body=GA|SC` to restrict to one body
- compare countries — `/votes/compare/` page with agreement rate, cross-matrix, year-by-year breakdown, and divergent vote lists
- voting similarity map — `/votes/map/` interactive D3 choropleth with zoom, country picker, disambiguation popup for overlapping territories, and similarity bar charts

# Future Features (Not Yet Implemented)

The architecture must allow future support for:
- Security Council transcripts
- amendment tracking
- timeline of debates
- LLM-based summarization of debates

# Deliverables

The agent must produce:
- a working Django project
- Docker environment
- database models mapped to the schema
- basic UI templates
- full-text search functionality
- meeting transcript viewer
- country and speaker pages
