--
-- PostgreSQL database dump
--

\restrict 4LTt7IBXaCzEwhnIcdApTtgejZdEPAfaf2CfEF5VLMndS2WAYSD4T7yjGimJ6BR

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

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
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: backup_summary_20250825; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_summary_20250825 (
    id integer NOT NULL,
    backup_name character varying(255),
    original_object character varying(255),
    object_type character varying(50),
    record_count integer,
    backup_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.backup_summary_20250825 OWNER TO postgres;

--
-- Name: backup_summary_20250825_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_summary_20250825_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_summary_20250825_id_seq OWNER TO postgres;

--
-- Name: backup_summary_20250825_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_summary_20250825_id_seq OWNED BY public.backup_summary_20250825.id;


--
-- Name: backup_summary_20250826; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_summary_20250826 (
    id integer NOT NULL,
    backup_name character varying(255),
    original_object character varying(255),
    object_type character varying(50),
    record_count integer,
    backup_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.backup_summary_20250826 OWNER TO postgres;

--
-- Name: backup_summary_20250826_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_summary_20250826_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_summary_20250826_id_seq OWNER TO postgres;

--
-- Name: backup_summary_20250826_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_summary_20250826_id_seq OWNED BY public.backup_summary_20250826.id;


--
-- Name: backup_summary_20250829; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_summary_20250829 (
    id integer NOT NULL,
    backup_name character varying(255),
    original_object character varying(255),
    object_type character varying(50),
    record_count integer,
    backup_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.backup_summary_20250829 OWNER TO postgres;

--
-- Name: backup_summary_20250829_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_summary_20250829_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_summary_20250829_id_seq OWNER TO postgres;

--
-- Name: backup_summary_20250829_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_summary_20250829_id_seq OWNED BY public.backup_summary_20250829.id;


--
-- Name: backup_views_metadata; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_views_metadata (
    id integer NOT NULL,
    backup_date date DEFAULT CURRENT_DATE,
    view_name character varying(255),
    backup_view_name character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.backup_views_metadata OWNER TO postgres;

--
-- Name: backup_views_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_views_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_views_metadata_id_seq OWNER TO postgres;

--
-- Name: backup_views_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_views_metadata_id_seq OWNED BY public.backup_views_metadata.id;


--
-- Name: categorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias (
    id character varying(36) NOT NULL,
    nome character varying(200) NOT NULL,
    empresa_id character varying(36) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.categorias OWNER TO postgres;

--
-- Name: categorias_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias_backup_20250826_175628 (
    id character varying(36),
    nome character varying(200),
    empresa_id character varying(36),
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.categorias_backup_20250826_175628 OWNER TO postgres;

--
-- Name: de_para; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.de_para (
    empresa_id character varying(36) NOT NULL,
    origem_sistema character varying(100),
    descricao_origem character varying(300),
    descricao_destino character varying(300),
    observacoes text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    id character varying(36) NOT NULL
);


ALTER TABLE public.de_para OWNER TO postgres;

--
-- Name: de_para_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.de_para_backup_20250826_175628 (
    empresa_id character varying(36),
    origem_sistema character varying(100),
    descricao_origem character varying(300),
    descricao_destino character varying(300),
    observacoes text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    plano_contas_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.de_para_backup_20250826_175628 OWNER TO postgres;

--
-- Name: dfc_structure_n1; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dfc_structure_n1 (
    name character varying(200) NOT NULL,
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36) NOT NULL
);


ALTER TABLE public.dfc_structure_n1 OWNER TO postgres;

--
-- Name: dfc_structure_n1_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dfc_structure_n1_backup_20250826_175628 (
    name character varying(200),
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.dfc_structure_n1_backup_20250826_175628 OWNER TO postgres;

--
-- Name: dfc_structure_n2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dfc_structure_n2 (
    dfc_n1_ordem integer NOT NULL,
    name character varying(200) NOT NULL,
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36) NOT NULL
);


ALTER TABLE public.dfc_structure_n2 OWNER TO postgres;

--
-- Name: dfc_structure_n2_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dfc_structure_n2_backup_20250826_175628 (
    dfc_n1_ordem integer,
    name character varying(200),
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.dfc_structure_n2_backup_20250826_175628 OWNER TO postgres;

--
-- Name: dre_structure_n0; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dre_structure_n0 (
    name character varying(200) NOT NULL,
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    dre_niveis character varying(20),
    empresa_id character varying(36),
    id character varying(36) NOT NULL
);


ALTER TABLE public.dre_structure_n0 OWNER TO postgres;

--
-- Name: dre_structure_n0_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dre_structure_n0_backup_20250826_175628 (
    name character varying(200),
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    dre_niveis character varying(20),
    empresa_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.dre_structure_n0_backup_20250826_175628 OWNER TO postgres;

--
-- Name: dre_structure_n1; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dre_structure_n1 (
    name character varying(200) NOT NULL,
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36) NOT NULL
);


ALTER TABLE public.dre_structure_n1 OWNER TO postgres;

--
-- Name: dre_structure_n1_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dre_structure_n1_backup_20250826_175628 (
    name character varying(200),
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.dre_structure_n1_backup_20250826_175628 OWNER TO postgres;

--
-- Name: dre_structure_n2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dre_structure_n2 (
    dre_n1_ordem integer NOT NULL,
    name character varying(200) NOT NULL,
    operation_type character varying(10),
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36) NOT NULL,
    description character varying(500)
);


ALTER TABLE public.dre_structure_n2 OWNER TO postgres;

--
-- Name: dre_structure_n2_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dre_structure_n2_backup_20250826_175628 (
    dre_n1_ordem integer,
    name character varying(200),
    operation_type character varying(10),
    description text,
    order_index integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.dre_structure_n2_backup_20250826_175628 OWNER TO postgres;

--
-- Name: empresas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.empresas (
    id character varying(36) NOT NULL,
    nome character varying(200) NOT NULL,
    grupo_empresa_id character varying(36) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.empresas OWNER TO postgres;

--
-- Name: empresas_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.empresas_backup_20250826_175628 (
    id character varying(36),
    nome character varying(200),
    grupo_empresa_id character varying(36),
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.empresas_backup_20250826_175628 OWNER TO postgres;

--
-- Name: financial_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_data (
    id character varying(36),
    origem character varying(50),
    empresa character varying(255),
    nome character varying(500),
    classificacao character varying(255),
    emissao date,
    competencia date,
    vencimento date,
    valor_original numeric(15,2),
    data date,
    valor numeric(15,2),
    banco character varying(255),
    conta_corrente character varying(100),
    documento character varying(100),
    observacao text,
    local character varying(100),
    segmento character varying(100),
    projeto character varying(100),
    centro_de_resultado character varying(100),
    diretoria character varying(100),
    created_at timestamp without time zone,
    empresa_id character varying(36)
);


ALTER TABLE public.financial_data OWNER TO postgres;

--
-- Name: financial_data_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_data_backup_20250826_175628 (
    origem character varying(50),
    empresa character varying(255),
    nome character varying(500),
    classificacao character varying(255),
    emissao date,
    competencia date,
    vencimento date,
    valor_original numeric(15,2),
    data date,
    valor numeric(15,2),
    banco character varying(255),
    conta_corrente character varying(100),
    documento character varying(100),
    observacao text,
    local character varying(100),
    segmento character varying(100),
    projeto character varying(100),
    centro_de_resultado character varying(100),
    diretoria character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    empresa_id character varying(36),
    de_para_id character varying(36),
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.financial_data_backup_20250826_175628 OWNER TO postgres;

--
-- Name: financial_data_backup_duplicatas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_data_backup_duplicatas (
    origem character varying(50),
    empresa character varying(255),
    nome character varying(500),
    classificacao character varying(255),
    emissao date,
    competencia date,
    vencimento date,
    valor_original numeric(15,2),
    data date,
    valor numeric(15,2),
    banco character varying(255),
    conta_corrente character varying(100),
    documento character varying(100),
    observacao text,
    local character varying(100),
    segmento character varying(100),
    projeto character varying(100),
    centro_de_resultado character varying(100),
    diretoria character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    empresa_id character varying(36),
    id character varying(36) NOT NULL
);


ALTER TABLE public.financial_data_backup_duplicatas OWNER TO postgres;

--
-- Name: grupos_empresa; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.grupos_empresa (
    id character varying(36) NOT NULL,
    nome character varying(200) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.grupos_empresa OWNER TO postgres;

--
-- Name: grupos_empresa_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.grupos_empresa_backup_20250826_175628 (
    id character varying(36),
    nome character varying(200),
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.grupos_empresa_backup_20250826_175628 OWNER TO postgres;

--
-- Name: periods; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.periods (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    is_closed boolean,
    created_at timestamp without time zone,
    grupo_empresa_id character varying(36)
);


ALTER TABLE public.periods OWNER TO postgres;

--
-- Name: periods_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.periods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.periods_id_seq OWNER TO postgres;

--
-- Name: periods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.periods_id_seq OWNED BY public.periods.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(255),
    resource character varying(100) NOT NULL,
    action character varying(50) NOT NULL,
    created_at timestamp without time zone,
    grupo_empresa_id character varying(36)
);


ALTER TABLE public.permissions OWNER TO postgres;

--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.permissions_id_seq OWNER TO postgres;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: plano_de_contas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plano_de_contas (
    empresa_id character varying(36) NOT NULL,
    conta_pai character varying(200),
    nome_conta character varying(500) NOT NULL,
    tipo_conta character varying(100),
    nivel integer,
    ordem integer,
    classificacao_dre character varying(200),
    classificacao_dre_n2 character varying(200),
    classificacao_dfc character varying(200),
    classificacao_dfc_n2 character varying(200),
    centro_custo character varying(200),
    observacoes text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    id character varying(36) NOT NULL
);


ALTER TABLE public.plano_de_contas OWNER TO postgres;

--
-- Name: plano_de_contas_backup_20250826_175628; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plano_de_contas_backup_20250826_175628 (
    empresa_id character varying(36),
    conta_pai character varying(200),
    nome_conta character varying(500),
    tipo_conta character varying(100),
    nivel integer,
    ordem integer,
    classificacao_dre character varying(200),
    classificacao_dre_n2 character varying(200),
    classificacao_dfc character varying(200),
    classificacao_dfc_n2 character varying(200),
    centro_custo character varying(200),
    observacoes text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    id character varying(36),
    backup_created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    backup_note text DEFAULT 'Backup automático após limpeza de tabelas temporárias'::text
);


ALTER TABLE public.plano_de_contas_backup_20250826_175628 OWNER TO postgres;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    role_id integer NOT NULL,
    permission_id integer NOT NULL,
    created_at timestamp without time zone,
    grupo_empresa_id character varying(36)
);


ALTER TABLE public.role_permissions OWNER TO postgres;

--
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.role_permissions_id_seq OWNER TO postgres;

--
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description character varying(255),
    created_at timestamp without time zone,
    grupo_empresa_id character varying(36)
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_roles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    created_at timestamp without time zone,
    grupo_empresa_id character varying(36)
);


ALTER TABLE public.user_roles OWNER TO postgres;

--
-- Name: user_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_roles_id_seq OWNER TO postgres;

--
-- Name: user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_roles_id_seq OWNED BY public.user_roles.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    grupo_empresa_id character varying(36)
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: v_financial_data_agrupado; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_financial_data_agrupado AS
 SELECT financial_data.classificacao,
    financial_data.empresa_id,
    financial_data.empresa,
    sum(financial_data.valor_original) AS valor_total,
    count(*) AS quantidade_registros,
    max(financial_data.created_at) AS ultima_atualizacao,
    max(financial_data.competencia) AS competencia_max,
    min(financial_data.competencia) AS competencia_min,
    to_char((max(financial_data.competencia))::timestamp with time zone, 'YYYY-MM'::text) AS periodo_mensal_max,
    to_char((min(financial_data.competencia))::timestamp with time zone, 'YYYY-MM'::text) AS periodo_mensal_min,
    concat(EXTRACT(year FROM max(financial_data.competencia)), '-Q', EXTRACT(quarter FROM max(financial_data.competencia))) AS periodo_trimestral_max,
    concat(EXTRACT(year FROM min(financial_data.competencia)), '-Q', EXTRACT(quarter FROM min(financial_data.competencia))) AS periodo_trimestral_min,
    (EXTRACT(year FROM max(financial_data.competencia)))::text AS periodo_anual_max,
    (EXTRACT(year FROM min(financial_data.competencia)))::text AS periodo_anual_min
   FROM public.financial_data
  WHERE ((financial_data.valor_original IS NOT NULL) AND (financial_data.competencia IS NOT NULL))
  GROUP BY financial_data.classificacao, financial_data.empresa_id, financial_data.empresa
  ORDER BY financial_data.classificacao, financial_data.empresa_id;


ALTER TABLE public.v_financial_data_agrupado OWNER TO postgres;

--
-- Name: v_dre_n0_completo; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_dre_n0_completo AS
 WITH fluxo_completo AS (
         SELECT fda.classificacao,
            fda.empresa_id,
            fda.empresa,
            fda.valor_total,
            fda.quantidade_registros,
            fda.ultima_atualizacao,
            dp.descricao_destino,
            dp.id AS de_para_id,
            pc.conta_pai,
            pc.classificacao_dre_n2,
            pc.id AS plano_contas_id,
            ds0.id AS dre_n0_id,
            ds0.name AS nome_conta,
            ds0.operation_type AS tipo_operacao,
            ds0.order_index AS ordem,
            ds0.description AS descricao,
            ds0.empresa_id AS dre_empresa_id,
            fda.periodo_mensal_max,
            fda.periodo_trimestral_max,
            fda.periodo_anual_max
           FROM (((public.v_financial_data_agrupado fda
             LEFT JOIN public.de_para dp ON (((fda.classificacao)::text = (dp.descricao_origem)::text)))
             LEFT JOIN public.plano_de_contas pc ON (((dp.descricao_destino)::text = (pc.conta_pai)::text)))
             LEFT JOIN public.dre_structure_n0 ds0 ON (((pc.classificacao_dre_n2)::text = ds0.description)))
          WHERE (ds0.is_active = true)
        ), dados_agrupados AS (
         SELECT fluxo_completo.classificacao,
            string_agg(DISTINCT (fluxo_completo.empresa)::text, ', '::text) AS empresas_origem,
            string_agg(DISTINCT (fluxo_completo.empresa_id)::text, ', '::text) AS empresas_ids,
            max((fluxo_completo.dre_n0_id)::text) AS dre_n0_id,
            max((fluxo_completo.nome_conta)::text) AS nome_conta,
            max((fluxo_completo.tipo_operacao)::text) AS tipo_operacao,
            max(fluxo_completo.ordem) AS ordem,
            max(fluxo_completo.descricao) AS descricao,
            sum(fluxo_completo.valor_total) AS valor_total_agregado,
            sum(fluxo_completo.quantidade_registros) AS total_registros,
            fluxo_completo.periodo_mensal_max,
            fluxo_completo.periodo_trimestral_max,
            fluxo_completo.periodo_anual_max
           FROM fluxo_completo
          WHERE (fluxo_completo.dre_n0_id IS NOT NULL)
          GROUP BY fluxo_completo.classificacao, fluxo_completo.periodo_mensal_max, fluxo_completo.periodo_trimestral_max, fluxo_completo.periodo_anual_max, fluxo_completo.dre_n0_id, fluxo_completo.nome_conta, fluxo_completo.tipo_operacao, fluxo_completo.ordem, fluxo_completo.descricao
        ), valores_mensais AS (
         SELECT dados_agrupados.dre_n0_id,
            dados_agrupados.nome_conta,
            dados_agrupados.tipo_operacao,
            dados_agrupados.ordem,
            dados_agrupados.descricao,
            dados_agrupados.classificacao,
            dados_agrupados.empresas_origem,
            dados_agrupados.empresas_ids,
            dados_agrupados.valor_total_agregado AS valor_2025_01,
            dados_agrupados.valor_total_agregado AS valor_2025_02,
            dados_agrupados.valor_total_agregado AS valor_2025_03,
            dados_agrupados.valor_total_agregado AS valor_2025_04,
            dados_agrupados.valor_total_agregado AS valor_2025_05,
            dados_agrupados.valor_total_agregado AS valor_2025_06,
            dados_agrupados.valor_total_agregado AS valor_2025_07,
            dados_agrupados.valor_total_agregado AS valor_2025_08,
            dados_agrupados.valor_total_agregado AS valor_2025_09,
            dados_agrupados.valor_total_agregado AS valor_2025_10,
            dados_agrupados.valor_total_agregado AS valor_2025_11,
            dados_agrupados.valor_total_agregado AS valor_2025_12,
            dados_agrupados.valor_total_agregado AS valor_2025_q1,
            dados_agrupados.valor_total_agregado AS valor_2025_q2,
            dados_agrupados.valor_total_agregado AS valor_2025_q3,
            dados_agrupados.valor_total_agregado AS valor_2025_q4,
            dados_agrupados.valor_total_agregado AS valor_2025,
            dados_agrupados.valor_total_agregado AS valor_2024,
            dados_agrupados.valor_total_agregado AS valor_total_geral,
            dados_agrupados.total_registros
           FROM dados_agrupados
          GROUP BY dados_agrupados.dre_n0_id, dados_agrupados.nome_conta, dados_agrupados.tipo_operacao, dados_agrupados.ordem, dados_agrupados.descricao, dados_agrupados.classificacao, dados_agrupados.empresas_origem, dados_agrupados.empresas_ids, dados_agrupados.valor_total_agregado, dados_agrupados.total_registros
        )
 SELECT valores_mensais.dre_n0_id,
    valores_mensais.nome_conta,
    valores_mensais.tipo_operacao,
    valores_mensais.ordem,
    valores_mensais.descricao,
    'CAR'::text AS origem,
    valores_mensais.empresas_origem AS empresa,
    valores_mensais.empresas_ids AS empresa_id,
    json_build_object('2025-01', valores_mensais.valor_2025_01, '2025-02', valores_mensais.valor_2025_02, '2025-03', valores_mensais.valor_2025_03, '2025-04', valores_mensais.valor_2025_04, '2025-05', valores_mensais.valor_2025_05, '2025-06', valores_mensais.valor_2025_06, '2025-07', valores_mensais.valor_2025_07, '2025-08', valores_mensais.valor_2025_08, '2025-09', valores_mensais.valor_2025_09, '2025-10', valores_mensais.valor_2025_10, '2025-11', valores_mensais.valor_2025_11, '2025-12', valores_mensais.valor_2025_12) AS valores_mensais,
    json_build_object('2025-Q1', valores_mensais.valor_2025_q1, '2025-Q2', valores_mensais.valor_2025_q2, '2025-Q3', valores_mensais.valor_2025_q3, '2025-Q4', valores_mensais.valor_2025_q4) AS valores_trimestrais,
    json_build_object('2025', valores_mensais.valor_2025, '2024', valores_mensais.valor_2024) AS valores_anuais,
    json_build_object() AS orcamentos_mensais,
    json_build_object() AS orcamentos_trimestrais,
    json_build_object() AS orcamentos_anuais,
    0 AS orcamento_total,
    valores_mensais.valor_total_geral AS valor_total,
    valores_mensais.empresas_origem AS source
   FROM valores_mensais
  ORDER BY valores_mensais.ordem;


ALTER TABLE public.v_dre_n0_completo OWNER TO postgres;

--
-- Name: v_dre_n0_completo_backup_20250905; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_dre_n0_completo_backup_20250905 AS
 SELECT v_dre_n0_completo.dre_n0_id,
    v_dre_n0_completo.nome_conta,
    v_dre_n0_completo.tipo_operacao,
    v_dre_n0_completo.ordem,
    v_dre_n0_completo.descricao,
    v_dre_n0_completo.origem,
    v_dre_n0_completo.empresa,
    v_dre_n0_completo.empresa_id,
    v_dre_n0_completo.valores_mensais,
    v_dre_n0_completo.valores_trimestrais,
    v_dre_n0_completo.valores_anuais,
    v_dre_n0_completo.orcamentos_mensais,
    v_dre_n0_completo.orcamentos_trimestrais,
    v_dre_n0_completo.orcamentos_anuais,
    v_dre_n0_completo.orcamento_total,
    v_dre_n0_completo.valor_total,
    v_dre_n0_completo.source
   FROM public.v_dre_n0_completo;


ALTER TABLE public.v_dre_n0_completo_backup_20250905 OWNER TO postgres;

--
-- Name: v_dre_n0_completo_data_backup_20250103_125314; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.v_dre_n0_completo_data_backup_20250103_125314 (
    dre_n0_id character varying(36),
    nome_conta character varying(200),
    tipo_operacao character varying(10),
    ordem integer,
    descricao text,
    origem text,
    empresa character varying(200),
    empresa_id character varying(36),
    valores_mensais jsonb,
    valores_trimestrais jsonb,
    valores_anuais jsonb,
    orcamentos_mensais jsonb,
    orcamentos_trimestrais jsonb,
    orcamentos_anuais jsonb,
    orcamento_total integer,
    valor_total integer,
    source text
);


ALTER TABLE public.v_dre_n0_completo_data_backup_20250103_125314 OWNER TO postgres;

--
-- Name: v_dre_n0_completo_data_backup_20250905_125925; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.v_dre_n0_completo_data_backup_20250905_125925 (
    dre_n0_id character varying(36),
    nome_conta character varying(200),
    tipo_operacao character varying(10),
    ordem integer,
    descricao text,
    origem text,
    empresa character varying(200),
    empresa_id character varying(36),
    valores_mensais jsonb,
    valores_trimestrais jsonb,
    valores_anuais jsonb,
    orcamentos_mensais jsonb,
    orcamentos_trimestrais jsonb,
    orcamentos_anuais jsonb,
    orcamento_total integer,
    valor_total integer,
    source text
);


ALTER TABLE public.v_dre_n0_completo_data_backup_20250905_125925 OWNER TO postgres;

--
-- Name: v_financial_data_agrupado_backup_20250905; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_financial_data_agrupado_backup_20250905 AS
 SELECT v_financial_data_agrupado.classificacao,
    v_financial_data_agrupado.empresa_id,
    v_financial_data_agrupado.empresa,
    v_financial_data_agrupado.valor_total,
    v_financial_data_agrupado.quantidade_registros,
    v_financial_data_agrupado.ultima_atualizacao,
    v_financial_data_agrupado.competencia_max,
    v_financial_data_agrupado.competencia_min,
    v_financial_data_agrupado.periodo_mensal_max,
    v_financial_data_agrupado.periodo_mensal_min,
    v_financial_data_agrupado.periodo_trimestral_max,
    v_financial_data_agrupado.periodo_trimestral_min,
    v_financial_data_agrupado.periodo_anual_max,
    v_financial_data_agrupado.periodo_anual_min
   FROM public.v_financial_data_agrupado;


ALTER TABLE public.v_financial_data_agrupado_backup_20250905 OWNER TO postgres;

--
-- Name: backup_summary_20250825 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_summary_20250825 ALTER COLUMN id SET DEFAULT nextval('public.backup_summary_20250825_id_seq'::regclass);


--
-- Name: backup_summary_20250826 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_summary_20250826 ALTER COLUMN id SET DEFAULT nextval('public.backup_summary_20250826_id_seq'::regclass);


--
-- Name: backup_summary_20250829 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_summary_20250829 ALTER COLUMN id SET DEFAULT nextval('public.backup_summary_20250829_id_seq'::regclass);


--
-- Name: backup_views_metadata id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_views_metadata ALTER COLUMN id SET DEFAULT nextval('public.backup_views_metadata_id_seq'::regclass);


--
-- Name: periods id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.periods ALTER COLUMN id SET DEFAULT nextval('public.periods_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: user_roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles ALTER COLUMN id SET DEFAULT nextval('public.user_roles_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: backup_summary_20250825 backup_summary_20250825_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_summary_20250825
    ADD CONSTRAINT backup_summary_20250825_pkey PRIMARY KEY (id);


--
-- Name: backup_summary_20250826 backup_summary_20250826_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_summary_20250826
    ADD CONSTRAINT backup_summary_20250826_pkey PRIMARY KEY (id);


--
-- Name: backup_summary_20250829 backup_summary_20250829_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_summary_20250829
    ADD CONSTRAINT backup_summary_20250829_pkey PRIMARY KEY (id);


--
-- Name: backup_views_metadata backup_views_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_views_metadata
    ADD CONSTRAINT backup_views_metadata_pkey PRIMARY KEY (id);


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: dfc_structure_n1 dfc_structure_n1_order_index_empresa_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dfc_structure_n1
    ADD CONSTRAINT dfc_structure_n1_order_index_empresa_unique UNIQUE (order_index, empresa_id);


--
-- Name: dfc_structure_n2 dfc_structure_n2_order_index_empresa_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dfc_structure_n2
    ADD CONSTRAINT dfc_structure_n2_order_index_empresa_unique UNIQUE (order_index, empresa_id);


--
-- Name: dre_structure_n0 dre_structure_n0_order_index_empresa_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n0
    ADD CONSTRAINT dre_structure_n0_order_index_empresa_unique UNIQUE (order_index, empresa_id);


--
-- Name: dre_structure_n1 dre_structure_n1_order_index_empresa_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n1
    ADD CONSTRAINT dre_structure_n1_order_index_empresa_unique UNIQUE (order_index, empresa_id);


--
-- Name: dre_structure_n2 dre_structure_n2_order_index_empresa_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n2
    ADD CONSTRAINT dre_structure_n2_order_index_empresa_unique UNIQUE (order_index, empresa_id);


--
-- Name: grupos_empresa empresas_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.grupos_empresa
    ADD CONSTRAINT empresas_nome_key UNIQUE (nome);


--
-- Name: grupos_empresa empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.grupos_empresa
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: empresas grupos_empresa_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT grupos_empresa_nome_key UNIQUE (nome);


--
-- Name: empresas grupos_empresa_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT grupos_empresa_pkey PRIMARY KEY (id);


--
-- Name: periods periods_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.periods
    ADD CONSTRAINT periods_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_name_key UNIQUE (name);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: de_para pk_de_para_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.de_para
    ADD CONSTRAINT pk_de_para_id PRIMARY KEY (id);


--
-- Name: financial_data_backup_duplicatas pk_financial_data_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_data_backup_duplicatas
    ADD CONSTRAINT pk_financial_data_id PRIMARY KEY (id);


--
-- Name: plano_de_contas pk_plano_de_contas_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plano_de_contas
    ADD CONSTRAINT pk_plano_de_contas_id PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: de_para uk_de_para_descricao_empresa; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.de_para
    ADD CONSTRAINT uk_de_para_descricao_empresa UNIQUE (descricao_origem, empresa_id);


--
-- Name: dfc_structure_n1 uk_dfc_structure_n1_dfc_n1_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dfc_structure_n1
    ADD CONSTRAINT uk_dfc_structure_n1_dfc_n1_id UNIQUE (id);


--
-- Name: dfc_structure_n2 uk_dfc_structure_n2_dfc_n2_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dfc_structure_n2
    ADD CONSTRAINT uk_dfc_structure_n2_dfc_n2_id UNIQUE (id);


--
-- Name: dre_structure_n0 uk_dre_structure_n0_description_empresa_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n0
    ADD CONSTRAINT uk_dre_structure_n0_description_empresa_id UNIQUE (description, empresa_id);


--
-- Name: dre_structure_n0 uk_dre_structure_n0_dre_n0_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n0
    ADD CONSTRAINT uk_dre_structure_n0_dre_n0_id UNIQUE (id);


--
-- Name: dre_structure_n1 uk_dre_structure_n1_dre_n1_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n1
    ADD CONSTRAINT uk_dre_structure_n1_dre_n1_id UNIQUE (id);


--
-- Name: dre_structure_n2 uk_dre_structure_n2_dre_n2_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n2
    ADD CONSTRAINT uk_dre_structure_n2_dre_n2_id UNIQUE (id);


--
-- Name: plano_de_contas uk_plano_de_contas_conta_pai_empresa; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plano_de_contas
    ADD CONSTRAINT uk_plano_de_contas_conta_pai_empresa UNIQUE (conta_pai, empresa_id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_categoria_grupo_empresa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_categoria_grupo_empresa ON public.categorias USING btree (empresa_id);


--
-- Name: idx_de_para_descricao_empresa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_de_para_descricao_empresa ON public.de_para USING btree (descricao_origem, empresa_id);


--
-- Name: idx_de_para_destino; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_de_para_destino ON public.de_para USING btree (descricao_destino);


--
-- Name: idx_de_para_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_de_para_empresa_id ON public.de_para USING btree (empresa_id);


--
-- Name: idx_de_para_grupo_empresa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_de_para_grupo_empresa ON public.de_para USING btree (empresa_id);


--
-- Name: idx_de_para_origem; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_de_para_origem ON public.de_para USING btree (descricao_origem);


--
-- Name: idx_dfc_n1_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dfc_n1_order ON public.dfc_structure_n1 USING btree (order_index);


--
-- Name: idx_dfc_n2_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dfc_n2_order ON public.dfc_structure_n2 USING btree (order_index);


--
-- Name: idx_dfc_n2_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dfc_n2_parent ON public.dfc_structure_n2 USING btree (dfc_n1_ordem);


--
-- Name: idx_dfc_structure_n1_grupo_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dfc_structure_n1_grupo_empresa_id ON public.dfc_structure_n1 USING btree (empresa_id);


--
-- Name: idx_dfc_structure_n2_grupo_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dfc_structure_n2_grupo_empresa_id ON public.dfc_structure_n2 USING btree (empresa_id);


--
-- Name: idx_dre_n0_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_n0_active ON public.dre_structure_n0 USING btree (is_active);


--
-- Name: idx_dre_n0_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_n0_order ON public.dre_structure_n0 USING btree (order_index);


--
-- Name: idx_dre_n1_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_n1_order ON public.dre_structure_n1 USING btree (order_index);


--
-- Name: idx_dre_n2_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_n2_order ON public.dre_structure_n2 USING btree (order_index);


--
-- Name: idx_dre_n2_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_n2_parent ON public.dre_structure_n2 USING btree (dre_n1_ordem);


--
-- Name: idx_dre_structure_n0_active_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_structure_n0_active_order ON public.dre_structure_n0 USING btree (is_active, order_index);


--
-- Name: idx_dre_structure_n0_grupo_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_structure_n0_grupo_empresa_id ON public.dre_structure_n0 USING btree (empresa_id);


--
-- Name: idx_dre_structure_n1_grupo_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_structure_n1_grupo_empresa_id ON public.dre_structure_n1 USING btree (empresa_id);


--
-- Name: idx_dre_structure_n2_grupo_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dre_structure_n2_grupo_empresa_id ON public.dre_structure_n2 USING btree (empresa_id);


--
-- Name: idx_financial_data_competencia; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_financial_data_competencia ON public.financial_data_backup_duplicatas USING btree (competencia);


--
-- Name: idx_financial_data_grupo_empresa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_financial_data_grupo_empresa_id ON public.financial_data_backup_duplicatas USING btree (empresa_id);


--
-- Name: idx_financial_data_valor_not_null; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_financial_data_valor_not_null ON public.financial_data_backup_duplicatas USING btree (valor_original) WHERE (valor_original IS NOT NULL);


--
-- Name: idx_grupo_empresa_empresa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_grupo_empresa_empresa ON public.empresas USING btree (grupo_empresa_id);


--
-- Name: idx_plano_contas_grupo_empresa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plano_contas_grupo_empresa ON public.plano_de_contas USING btree (empresa_id);


--
-- Name: periods_date_range_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX periods_date_range_idx ON public.periods USING btree (start_date, end_date);


--
-- Name: periods_type_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX periods_type_idx ON public.periods USING btree (type);


--
-- Name: users_email_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX users_email_idx ON public.users USING btree (email);


--
-- Name: categorias fk_categorias_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT fk_categorias_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: de_para fk_de_para_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.de_para
    ADD CONSTRAINT fk_de_para_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: de_para fk_de_para_grupo_empresa_id_empresas__id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.de_para
    ADD CONSTRAINT fk_de_para_grupo_empresa_id_empresas__id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: dfc_structure_n1 fk_dfc_structure_n1_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dfc_structure_n1
    ADD CONSTRAINT fk_dfc_structure_n1_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: dfc_structure_n2 fk_dfc_structure_n2_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dfc_structure_n2
    ADD CONSTRAINT fk_dfc_structure_n2_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: dre_structure_n0 fk_dre_structure_n0_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n0
    ADD CONSTRAINT fk_dre_structure_n0_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: dre_structure_n1 fk_dre_structure_n1_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n1
    ADD CONSTRAINT fk_dre_structure_n1_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: dre_structure_n2 fk_dre_structure_n2_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dre_structure_n2
    ADD CONSTRAINT fk_dre_structure_n2_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: empresas fk_empresas_grupo_empresa_id_grupos_empresa; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT fk_empresas_grupo_empresa_id_grupos_empresa FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: financial_data_backup_duplicatas fk_financial_data_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_data_backup_duplicatas
    ADD CONSTRAINT fk_financial_data_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: periods fk_periods_grupo_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.periods
    ADD CONSTRAINT fk_periods_grupo_empresa_id FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: permissions fk_permissions_grupo_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT fk_permissions_grupo_empresa_id FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: plano_de_contas fk_plano_de_contas_empresa_id_empresas; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plano_de_contas
    ADD CONSTRAINT fk_plano_de_contas_empresa_id_empresas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: plano_de_contas fk_plano_de_contas_grupo_empresa_id_empresas__id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plano_de_contas
    ADD CONSTRAINT fk_plano_de_contas_grupo_empresa_id_empresas__id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: role_permissions fk_role_permissions_grupo_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT fk_role_permissions_grupo_empresa_id FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: roles fk_roles_grupo_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_grupo_empresa_id FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: user_roles fk_user_roles_grupo_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_user_roles_grupo_empresa_id FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: users fk_users_grupo_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_grupo_empresa_id FOREIGN KEY (grupo_empresa_id) REFERENCES public.grupos_empresa(id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id);


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 4LTt7IBXaCzEwhnIcdApTtgejZdEPAfaf2CfEF5VLMndS2WAYSD4T7yjGimJ6BR

