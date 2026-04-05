--
-- PostgreSQL database dump
--

\restrict oBanwPXhvwclaI0tHzv0y4kWv0mXSguPzsRdKrVhiBLOp7TBi45wbBoMPeG19hc

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

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
    'absent',
    'non_voting'
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
    m49 character varying(5),
    un_member_since date,
    un_member_end date
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
-- Name: country_ideal_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country_ideal_points (
    id integer NOT NULL,
    country_id integer,
    iso3 character varying(3) NOT NULL,
    year integer NOT NULL,
    ideal_point double precision NOT NULL,
    se double precision
);


--
-- Name: country_ideal_points_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.country_ideal_points_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: country_ideal_points_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.country_ideal_points_id_seq OWNED BY public.country_ideal_points.id;


--
-- Name: country_votes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country_votes (
    id integer NOT NULL,
    vote_id integer NOT NULL,
    country_id integer NOT NULL,
    vote_position public.vote_position_enum NOT NULL,
    permanent_member boolean
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
    session integer,
    date date,
    location character varying(50),
    pdf_path character varying(500),
    is_general_debate boolean DEFAULT false NOT NULL
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
-- Name: general_debate_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.general_debate_entries (
    id integer NOT NULL,
    document_id integer,
    country_id integer,
    speaker_id integer,
    speaker_name text NOT NULL,
    salutation character varying(20),
    ga_session integer NOT NULL,
    meeting_date date,
    undl_id character varying(30),
    undl_link text,
    text text
);


--
-- Name: general_debate_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.general_debate_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: general_debate_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.general_debate_entries_id_seq OWNED BY public.general_debate_entries.id;


--
-- Name: permanent_representatives; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permanent_representatives (
    id integer NOT NULL,
    country_id integer,
    speaker_id integer,
    name text NOT NULL,
    salutation character varying(20),
    notes text,
    undl_id character varying(30),
    undl_link text
);


--
-- Name: permanent_representatives_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.permanent_representatives_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: permanent_representatives_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permanent_representatives_id_seq OWNED BY public.permanent_representatives.id;


--
-- Name: resolution_citations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resolution_citations (
    id integer NOT NULL,
    citing_id integer NOT NULL,
    cited_symbol text NOT NULL,
    cited_id integer,
    weight integer NOT NULL
);


--
-- Name: resolution_citations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resolution_citations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: resolution_citations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resolution_citations_id_seq OWNED BY public.resolution_citations.id;


--
-- Name: resolutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resolutions (
    id integer NOT NULL,
    draft_symbol text NOT NULL,
    adopted_symbol text,
    title text,
    body character varying(2) NOT NULL,
    session integer,
    category text,
    agenda_title text,
    committee_report text,
    full_text text,
    crunsc_id character varying(30),
    undl_id character varying(30),
    undl_link character varying(500)
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
-- Name: sc_representatives; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sc_representatives (
    id integer NOT NULL,
    country_id integer,
    speaker_id integer,
    name text NOT NULL,
    salutation character varying(20),
    sc_president boolean,
    notes text,
    undl_id character varying(30),
    undl_link text
);


--
-- Name: sc_representatives_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sc_representatives_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sc_representatives_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sc_representatives_id_seq OWNED BY public.sc_representatives.id;


--
-- Name: speakers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.speakers (
    id integer NOT NULL,
    name character varying(300) NOT NULL,
    country_id integer,
    organization character varying(400),
    role character varying(500),
    title character varying(20)
);


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
-- Name: search_index; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.search_index AS
 SELECT row_number() OVER () AS id,
    item_type,
    item_id,
    document_id,
    document_symbol,
    date,
    body,
    session,
    speaker_id,
    speaker_name,
    country_id,
    country_name,
    country_iso3,
    content,
    search_vector
   FROM ( SELECT 'speech'::text AS item_type,
            s.id AS item_id,
            s.document_id,
            d.symbol AS document_symbol,
            d.date,
            d.body,
            d.session,
            s.speaker_id,
            sp.name AS speaker_name,
            sp.country_id,
            c.name AS country_name,
            c.iso3 AS country_iso3,
            s.text AS content,
            ((setweight(to_tsvector('english'::regconfig, (COALESCE(sp.name, ''::character varying))::text), 'A'::"char") || setweight(to_tsvector('english'::regconfig, (COALESCE(c.name, ''::character varying))::text), 'B'::"char")) || setweight(to_tsvector('english'::regconfig, COALESCE(s.text, ''::text)), 'C'::"char")) AS search_vector
           FROM (((public.speeches s
             JOIN public.documents d ON ((d.id = s.document_id)))
             JOIN public.speakers sp ON ((sp.id = s.speaker_id)))
             LEFT JOIN public.countries c ON ((c.id = sp.country_id)))
        UNION ALL
         SELECT 'resolution'::text AS item_type,
            r.id AS item_id,
            NULL::integer AS document_id,
            COALESCE(r.adopted_symbol, r.draft_symbol) AS document_symbol,
            NULL::date AS date,
            r.body,
            r.session,
            NULL::integer AS speaker_id,
            NULL::text AS speaker_name,
            NULL::integer AS country_id,
            NULL::text AS country_name,
            NULL::text AS country_iso3,
            ((COALESCE(r.title, ''::text) || ' '::text) || COALESCE(r.full_text, ''::text)) AS content,
            (((setweight(to_tsvector('english'::regconfig, COALESCE(r.adopted_symbol, r.draft_symbol, ''::text)), 'A'::"char") || setweight(to_tsvector('english'::regconfig, COALESCE(r.title, ''::text)), 'B'::"char")) || setweight(to_tsvector('english'::regconfig, COALESCE(r.category, ''::text)), 'C'::"char")) || setweight(to_tsvector('english'::regconfig, COALESCE(r.full_text, ''::text)), 'D'::"char")) AS search_vector
           FROM public.resolutions r
          WHERE ((COALESCE(r.title, ''::text) <> ''::text) OR (r.full_text IS NOT NULL))) base
  WITH NO DATA;


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
    total_non_voting integer,
    total_ms integer,
    vote_note text,
    undl_id character varying(20),
    undl_link character varying(500),
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
-- Name: country_ideal_points id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_ideal_points ALTER COLUMN id SET DEFAULT nextval('public.country_ideal_points_id_seq'::regclass);


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
-- Name: general_debate_entries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.general_debate_entries ALTER COLUMN id SET DEFAULT nextval('public.general_debate_entries_id_seq'::regclass);


--
-- Name: permanent_representatives id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permanent_representatives ALTER COLUMN id SET DEFAULT nextval('public.permanent_representatives_id_seq'::regclass);


--
-- Name: resolution_citations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolution_citations ALTER COLUMN id SET DEFAULT nextval('public.resolution_citations_id_seq'::regclass);


--
-- Name: resolutions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolutions ALTER COLUMN id SET DEFAULT nextval('public.resolutions_id_seq'::regclass);


--
-- Name: sc_representatives id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sc_representatives ALTER COLUMN id SET DEFAULT nextval('public.sc_representatives_id_seq'::regclass);


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
-- Name: country_ideal_points country_ideal_points_iso3_year_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_ideal_points
    ADD CONSTRAINT country_ideal_points_iso3_year_key UNIQUE (iso3, year);


--
-- Name: country_ideal_points country_ideal_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_ideal_points
    ADD CONSTRAINT country_ideal_points_pkey PRIMARY KEY (id);


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
-- Name: general_debate_entries general_debate_entries_ga_session_speaker_name_country_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.general_debate_entries
    ADD CONSTRAINT general_debate_entries_ga_session_speaker_name_country_id_key UNIQUE (ga_session, speaker_name, country_id);


--
-- Name: general_debate_entries general_debate_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.general_debate_entries
    ADD CONSTRAINT general_debate_entries_pkey PRIMARY KEY (id);


--
-- Name: permanent_representatives permanent_representatives_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permanent_representatives
    ADD CONSTRAINT permanent_representatives_pkey PRIMARY KEY (id);


--
-- Name: permanent_representatives permanent_representatives_undl_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permanent_representatives
    ADD CONSTRAINT permanent_representatives_undl_id_key UNIQUE (undl_id);


--
-- Name: resolution_citations resolution_citations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolution_citations
    ADD CONSTRAINT resolution_citations_pkey PRIMARY KEY (id);


--
-- Name: resolutions resolutions_crunsc_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolutions
    ADD CONSTRAINT resolutions_crunsc_id_key UNIQUE (crunsc_id);


--
-- Name: resolutions resolutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolutions
    ADD CONSTRAINT resolutions_pkey PRIMARY KEY (id);


--
-- Name: sc_representatives sc_representatives_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sc_representatives
    ADD CONSTRAINT sc_representatives_pkey PRIMARY KEY (id);


--
-- Name: sc_representatives sc_representatives_undl_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sc_representatives
    ADD CONSTRAINT sc_representatives_undl_id_key UNIQUE (undl_id);


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
-- Name: resolution_citations uq_citation; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolution_citations
    ADD CONSTRAINT uq_citation UNIQUE (citing_id, cited_symbol);


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
    ADD CONSTRAINT uq_speaker UNIQUE (name, country_id, organization);


--
-- Name: votes votes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (id);


--
-- Name: idx_search_index_body; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_search_index_body ON public.search_index USING btree (body) WHERE (body IS NOT NULL);


--
-- Name: idx_search_index_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_search_index_country ON public.search_index USING btree (country_id) WHERE (country_id IS NOT NULL);


--
-- Name: idx_search_index_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_search_index_id ON public.search_index USING btree (id);


--
-- Name: idx_search_index_speaker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_search_index_speaker ON public.search_index USING btree (speaker_id) WHERE (speaker_id IS NOT NULL);


--
-- Name: idx_search_index_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_search_index_type ON public.search_index USING btree (item_type, item_id);


--
-- Name: idx_search_index_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_search_index_vector ON public.search_index USING gin (search_vector);


--
-- Name: ix_cip_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cip_country ON public.country_ideal_points USING btree (country_id);


--
-- Name: ix_cip_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cip_year ON public.country_ideal_points USING btree (year);


--
-- Name: ix_gde_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_gde_country ON public.general_debate_entries USING btree (country_id);


--
-- Name: ix_gde_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_gde_document ON public.general_debate_entries USING btree (document_id);


--
-- Name: ix_rc_cited; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rc_cited ON public.resolution_citations USING btree (cited_id);


--
-- Name: ix_rc_citing; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rc_citing ON public.resolution_citations USING btree (citing_id);


--
-- Name: ix_res_crunsc_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_res_crunsc_id ON public.resolutions USING btree (crunsc_id) WHERE (crunsc_id IS NOT NULL);


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
-- Name: country_ideal_points country_ideal_points_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_ideal_points
    ADD CONSTRAINT country_ideal_points_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id) ON DELETE CASCADE;


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
-- Name: general_debate_entries general_debate_entries_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.general_debate_entries
    ADD CONSTRAINT general_debate_entries_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id) ON DELETE SET NULL;


--
-- Name: general_debate_entries general_debate_entries_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.general_debate_entries
    ADD CONSTRAINT general_debate_entries_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: general_debate_entries general_debate_entries_speaker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.general_debate_entries
    ADD CONSTRAINT general_debate_entries_speaker_id_fkey FOREIGN KEY (speaker_id) REFERENCES public.speakers(id) ON DELETE SET NULL;


--
-- Name: permanent_representatives permanent_representatives_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permanent_representatives
    ADD CONSTRAINT permanent_representatives_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id) ON DELETE SET NULL;


--
-- Name: permanent_representatives permanent_representatives_speaker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permanent_representatives
    ADD CONSTRAINT permanent_representatives_speaker_id_fkey FOREIGN KEY (speaker_id) REFERENCES public.speakers(id) ON DELETE SET NULL;


--
-- Name: resolution_citations resolution_citations_cited_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolution_citations
    ADD CONSTRAINT resolution_citations_cited_id_fkey FOREIGN KEY (cited_id) REFERENCES public.resolutions(id) ON DELETE SET NULL;


--
-- Name: resolution_citations resolution_citations_citing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resolution_citations
    ADD CONSTRAINT resolution_citations_citing_id_fkey FOREIGN KEY (citing_id) REFERENCES public.resolutions(id) ON DELETE CASCADE;


--
-- Name: sc_representatives sc_representatives_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sc_representatives
    ADD CONSTRAINT sc_representatives_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id) ON DELETE SET NULL;


--
-- Name: sc_representatives sc_representatives_speaker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sc_representatives
    ADD CONSTRAINT sc_representatives_speaker_id_fkey FOREIGN KEY (speaker_id) REFERENCES public.speakers(id) ON DELETE SET NULL;


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

\unrestrict oBanwPXhvwclaI0tHzv0y4kWv0mXSguPzsRdKrVhiBLOp7TBi45wbBoMPeG19hc

