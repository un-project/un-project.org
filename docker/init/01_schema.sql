--
-- PostgreSQL database dump
--

\restrict O4oEzmgIc1ByDldb6sRDKtdUd1ek5EOBjQplwYwyOpOhpqytERdPHfigGk9PmBU

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: direction_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.direction_type_enum AS ENUM (
    'adoption',
    'decision',
    'suspension',
    'resumption',
    'adjournment',
    'silence',
    'language_note',
    'other'
);


--
-- Name: item_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.item_type_enum AS ENUM (
    'agenda_item',
    'other_item'
);


--
-- Name: vote_position_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.vote_position_enum AS ENUM (
    'yes',
    'no',
    'abstain',
    'absent'
);


--
-- Name: vote_scope_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.vote_scope_enum AS ENUM (
    'whole_resolution',
    'paragraph',
    'amendment'
);


--
-- Name: vote_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.vote_type_enum AS ENUM (
    'consensus',
    'recorded'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: amendments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.amendments (
    id integer NOT NULL,
    resolution_id integer NOT NULL,
    description text,
    proposed_by_country_id integer,
    oral_correction boolean NOT NULL
);


--
-- Name: amendments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.amendments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: amendments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.amendments_id_seq OWNED BY public.amendments.id;


--
-- Name: countries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.countries (
    id integer NOT NULL,
    name character varying(300) NOT NULL,
    short_name character varying(100),
    iso2 character varying(2),
    iso3 character varying(3),
    un_member_since date
);


--
-- Name: countries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.countries_id_seq OWNED BY public.countries.id;


--
-- Name: country_votes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country_votes (
    id integer NOT NULL,
    vote_id integer NOT NULL,
    country_id integer NOT NULL,
    vote_position public.vote_position_enum NOT NULL
);


--
-- Name: country_votes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.country_votes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: country_votes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.country_votes_id_seq OWNED BY public.country_votes.id;


--
-- Name: document_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_items (
    id integer NOT NULL,
    document_id integer NOT NULL,
    "position" integer NOT NULL,
    item_type public.item_type_enum NOT NULL,
    title text NOT NULL,
    agenda_number integer,
    sub_item character varying(10),
    continued boolean NOT NULL
);


--
-- Name: document_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.document_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: document_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.document_items_id_seq OWNED BY public.document_items.id;


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    symbol character varying(30) NOT NULL,
    body character varying(2) NOT NULL,
    meeting_number integer NOT NULL,
    session integer NOT NULL,
    date date,
    location character varying(50),
    pdf_path character varying(500)
);


--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: resolutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resolutions (
    id integer NOT NULL,
    draft_symbol character varying(50) NOT NULL,
    adopted_symbol character varying(50),
    title text,
    body character varying(2) NOT NULL,
    session integer,
    category character varying(200)
);


--
-- Name: resolutions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resolutions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resolutions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resolutions_id_seq OWNED BY public.resolutions.id;


--
-- Name: speakers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.speakers (
    id integer NOT NULL,
    name character varying(300) NOT NULL,
    country_id integer,
    role character varying(100),
    title character varying(20)
);


--
-- Name: speakers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.speakers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: speakers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.speakers_id_seq OWNED BY public.speakers.id;


--
-- Name: speeches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.speeches (
    id integer NOT NULL,
    document_id integer NOT NULL,
    item_id integer,
    speaker_id integer NOT NULL,
    language character varying(50),
    on_behalf_of character varying(300),
    text text NOT NULL,
    position_in_document integer NOT NULL,
    position_in_item integer NOT NULL
);


--
-- Name: speeches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.speeches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: speeches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.speeches_id_seq OWNED BY public.speeches.id;


--
-- Name: stage_directions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stage_directions (
    id integer NOT NULL,
    document_id integer NOT NULL,
    item_id integer,
    text text NOT NULL,
    direction_type public.direction_type_enum NOT NULL,
    position_in_document integer NOT NULL,
    position_in_item integer NOT NULL
);


--
-- Name: stage_directions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stage_directions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: stage_directions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_directions_id_seq OWNED BY public.stage_directions.id;


--
-- Name: votes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.votes (
    id integer NOT NULL,
    document_id integer NOT NULL,
    item_id integer,
    resolution_id integer NOT NULL,
    vote_type public.vote_type_enum NOT NULL,
    vote_scope public.vote_scope_enum NOT NULL,
    paragraph_number integer,
    yes_count integer,
    no_count integer,
    abstain_count integer,
    position_in_item integer NOT NULL
);


--
-- Name: votes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.votes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: votes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.votes_id_seq OWNED BY public.votes.id;


--
-- Name: amendments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.amendments ALTER COLUMN id SET DEFAULT nextval('public.amendments_id_seq'::regclass);


--
-- Name: countries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries ALTER COLUMN id SET DEFAULT nextval('public.countries_id_seq'::regclass);


--
-- Name: country_votes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_votes ALTER COLUMN id SET DEFAULT nextval('public.country_votes_id_seq'::regclass);


--
-- Name: document_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_items ALTER COLUMN id SET DEFAULT nextval('public.document_items_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: resolutions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolutions ALTER COLUMN id SET DEFAULT nextval('public.resolutions_id_seq'::regclass);


--
-- Name: speakers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speakers ALTER COLUMN id SET DEFAULT nextval('public.speakers_id_seq'::regclass);


--
-- Name: speeches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speeches ALTER COLUMN id SET DEFAULT nextval('public.speeches_id_seq'::regclass);


--
-- Name: stage_directions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_directions ALTER COLUMN id SET DEFAULT nextval('public.stage_directions_id_seq'::regclass);


--
-- Name: votes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.votes ALTER COLUMN id SET DEFAULT nextval('public.votes_id_seq'::regclass);


--
-- Name: amendments amendments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT amendments_pkey PRIMARY KEY (id);


--
-- Name: countries countries_iso2_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_iso2_key UNIQUE (iso2);


--
-- Name: countries countries_iso3_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_iso3_key UNIQUE (iso3);


--
-- Name: countries countries_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_name_key UNIQUE (name);


--
-- Name: countries countries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_pkey PRIMARY KEY (id);


--
-- Name: country_votes country_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_votes
    ADD CONSTRAINT country_votes_pkey PRIMARY KEY (id);


--
-- Name: document_items document_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_items
    ADD CONSTRAINT document_items_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: documents documents_symbol_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_symbol_key UNIQUE (symbol);


--
-- Name: resolutions resolutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolutions
    ADD CONSTRAINT resolutions_pkey PRIMARY KEY (id);


--
-- Name: speakers speakers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speakers
    ADD CONSTRAINT speakers_pkey PRIMARY KEY (id);


--
-- Name: speeches speeches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speeches
    ADD CONSTRAINT speeches_pkey PRIMARY KEY (id);


--
-- Name: stage_directions stage_directions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_directions
    ADD CONSTRAINT stage_directions_pkey PRIMARY KEY (id);


--
-- Name: country_votes uq_country_vote; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_votes
    ADD CONSTRAINT uq_country_vote UNIQUE (vote_id, country_id);


--
-- Name: document_items uq_item_position; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_items
    ADD CONSTRAINT uq_item_position UNIQUE (document_id, "position");


--
-- Name: speakers uq_speaker; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speakers
    ADD CONSTRAINT uq_speaker UNIQUE (name, country_id);


--
-- Name: votes votes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (id);


--
-- Name: amendments amendments_proposed_by_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT amendments_proposed_by_country_id_fkey FOREIGN KEY (proposed_by_country_id) REFERENCES public.countries(id);


--
-- Name: amendments amendments_resolution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT amendments_resolution_id_fkey FOREIGN KEY (resolution_id) REFERENCES public.resolutions(id);


--
-- Name: country_votes country_votes_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_votes
    ADD CONSTRAINT country_votes_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: country_votes country_votes_vote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_votes
    ADD CONSTRAINT country_votes_vote_id_fkey FOREIGN KEY (vote_id) REFERENCES public.votes(id);


--
-- Name: document_items document_items_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_items
    ADD CONSTRAINT document_items_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: speakers speakers_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speakers
    ADD CONSTRAINT speakers_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: speeches speeches_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speeches
    ADD CONSTRAINT speeches_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: speeches speeches_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speeches
    ADD CONSTRAINT speeches_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.document_items(id);


--
-- Name: speeches speeches_speaker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speeches
    ADD CONSTRAINT speeches_speaker_id_fkey FOREIGN KEY (speaker_id) REFERENCES public.speakers(id);


--
-- Name: stage_directions stage_directions_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_directions
    ADD CONSTRAINT stage_directions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: stage_directions stage_directions_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_directions
    ADD CONSTRAINT stage_directions_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.document_items(id);


--
-- Name: votes votes_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: votes votes_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.document_items(id);


--
-- Name: votes votes_resolution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_resolution_id_fkey FOREIGN KEY (resolution_id) REFERENCES public.resolutions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict O4oEzmgIc1ByDldb6sRDKtdUd1ek5EOBjQplwYwyOpOhpqytERdPHfigGk9PmBU

