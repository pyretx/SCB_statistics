-- ─────────────────────────────────────────────────────────────────────────────
-- Compliance register — Phase 1 backfill (docs/compliance-framework.md §12).
-- Adds the remaining 18 countries (everything except the Phase 0 pilots:
-- the 20 Eurostat-SES countries + Norway + Mexico, already seeded).
--
-- Run ONCE in the Supabase SQL editor, AFTER 2026-07-14_compliance_register.sql.
-- Idempotency: uses ON CONFLICT DO NOTHING so a re-run is safe.
--
-- Clearance is seeded conservatively — every dimension 'likely_verify' except
-- 'attribution' = 'confirmed' (attribution is always required) — with the licence
-- URL on the dataset as evidence and NO reviewed_by. The owner reviews and flips
-- dimensions to 'confirmed' (framework §1.2). All rows grandfathered=true so they
-- stay public per §1.4. Nothing here asserts approval on assumption.
--
-- Licence fields are BEST-EFFORT starting points for the owner's review, not
-- final determinations — hence 'likely_verify'.
-- ─────────────────────────────────────────────────────────────────────────────

-- ══ Providers (one per country; 1:1 here — Eurostat's many-countries case is the
--    Phase 0 exception) ═══════════════════════════════════════════════════════
insert into public.compliance_provider (provider_id, name, country_or_org, homepage_url, reuse_policy_url) values
  ('scb',      'Statistics Sweden (SCB)',            'Sweden',      'https://www.scb.se/en/',            'https://www.scb.se/en/About-us/'),
  ('insee',    'INSEE',                              'France',      'https://www.insee.fr/en/',          'https://www.etalab.gouv.fr/licence-ouverte-open-licence/'),
  ('bls',      'U.S. Bureau of Labor Statistics',    'United States','https://www.bls.gov/',             'https://www.bls.gov/opub/copyright-information.htm'),
  ('dst',      'Statistics Denmark (DST)',           'Denmark',     'https://www.dst.dk/en',             'https://www.dst.dk/en/OmDST/omdst'),
  ('hagstofa', 'Statistics Iceland (Hagstofa)',      'Iceland',     'https://statice.is/',               'https://statice.is/about-statistics-iceland/'),
  ('statfin',  'Statistics Finland',                 'Finland',     'https://stat.fi/index_en.html',     'https://stat.fi/org/lainsaadanto/copyright_en.html'),
  ('statee',   'Statistics Estonia',                 'Estonia',     'https://www.stat.ee/en',            'https://www.stat.ee/en/avaandmed'),
  ('cbs',      'Statistics Netherlands (CBS)',       'Netherlands', 'https://www.cbs.nl/en-gb',          'https://www.cbs.nl/en-gb/about-us/website/copyright'),
  ('ons',      'Office for National Statistics (ONS)','United Kingdom','https://www.ons.gov.uk/',        'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'),
  ('destatis', 'Federal Statistical Office (Destatis)','Germany',   'https://www.destatis.de/EN/',       'https://www.govdata.de/dl-de/by-2-0'),
  ('statcan',  'Statistics Canada',                  'Canada',      'https://www.statcan.gc.ca/en/start','https://www.statcan.gc.ca/en/reference/licence'),
  ('statsnz',  'Stats NZ',                           'New Zealand', 'https://www.stats.govt.nz/',        'https://www.stats.govt.nz/help-with-using-this-site/'),
  ('abs',      'Australian Bureau of Statistics',    'Australia',   'https://www.abs.gov.au/',           'https://www.abs.gov.au/website-privacy-copyright-and-disclaimer'),
  ('surs',     'Statistical Office of Slovenia (SURS)','Slovenia',  'https://www.stat.si/StatWeb/en',    'https://www.stat.si/StatWeb/en/about-us'),
  ('ibge',     'IBGE',                               'Brazil',      'https://www.ibge.gov.br/en/',       'https://www.ibge.gov.br/en/institutional/copyright.html'),
  ('fso',      'Federal Statistical Office (FSO/BFS)','Switzerland', 'https://www.bfs.admin.ch/',         'https://www.bfs.admin.ch/bfs/en/home/fso/terms-of-use.html'),
  ('ine',      'INE (Instituto Nacional de Estadística)','Spain',   'https://www.ine.es/en/',            'https://www.ine.es/en/aviso_legal_en.htm'),
  ('estat',    'e-Stat (Statistics Bureau of Japan)','Japan',       'https://www.e-stat.go.jp/en',       'https://www.e-stat.go.jp/en/terms-of-use')
on conflict (provider_id) do nothing;

-- ══ Datasets (terms live here; licence best-effort → likely_verify) ═══════════
insert into public.compliance_dataset
  (dataset_id, provider_id, title, official_table_id, dataset_url, data_type,
   licence_name, licence_url, licence_summary_plain, required_attribution_text,
   personal_data, reference_period_note) values
  ('scb_am0110','scb','Salary structure, whole economy (AM0110)','AM0110',
     'https://www.statistikdatabasen.scb.se/','official_table',
     'Statistics Sweden reuse terms','https://www.scb.se/en/About-us/',
     'Official statistics freely available for reuse with attribution to Statistics Sweden.',
     'Source: Statistics Sweden (SCB)','none','Annual; mean + P10–P90 monthly earnings, SEK.'),
  ('insee_fd_salaan','insee','Base Tous Salariés — microdata (FD_SALAAN) + Melodi means','FD_SALAAN',
     'https://www.insee.fr/en/statistiques','microdata',
     'Licence Ouverte / Open Licence 2.0 (Etalab)','https://www.etalab.gouv.fr/licence-ouverte-open-licence/',
     'Free reuse, including commercial, with attribution to INSEE under the French Open Licence.',
     'Source: INSEE','none','Annual microdata vintage; net salary percentiles, EUR.'),
  ('bls_oews','bls','Occupational Employment and Wage Statistics (OEWS)','OEWS',
     'https://www.bls.gov/oes/','derived_bundle',
     'U.S. Government work — public domain','https://www.bls.gov/opub/copyright-information.htm',
     'U.S. Government works are in the public domain; citation of BLS is requested.',
     'Source: U.S. Bureau of Labor Statistics, OEWS','none','May reference year; mean + P10–P90 annual wage, USD (national + state).'),
  ('dst_lons20','dst','Earnings by occupation (LONS20)','LONS20',
     'https://www.statbank.dk/LONS20','official_table',
     'Statistics Denmark reuse terms','https://www.dst.dk/en/OmDST/omdst',
     'Statistics Denmark data may be reused freely with attribution.',
     'Source: Statistics Denmark','none','Annual; standardised hourly earnings, DKK.'),
  ('hagstofa_vin02001','hagstofa','Wages by occupation (VIN02001)','VIN02001',
     'https://px.hagstofa.is/','official_table',
     'Statistics Iceland reuse terms','https://statice.is/about-statistics-iceland/',
     'Reuse permitted with attribution to Statistics Iceland.',
     'Source: Statistics Iceland','none','Annual; monthly earnings, thousand ISK (shown in ISK).'),
  ('statfin_15au','statfin','Structure of Earnings (15au)','15au',
     'https://stat.fi/','official_table',
     'CC BY 4.0','https://creativecommons.org/licenses/by/4.0/',
     'Free reuse, including commercial, with attribution to Statistics Finland.',
     'Source: Statistics Finland','none','Annual SES; P10/median/P90 monthly earnings, EUR.'),
  ('statee_pa633','statee','Average gross wages by occupation (PA633)','PA633',
     'https://andmed.stat.ee/en/stat/','official_table',
     'CC BY 4.0','https://creativecommons.org/licenses/by/4.0/',
     'Free reuse, including commercial, with attribution to Statistics Estonia.',
     'Source: Statistics Estonia','none','4-yearly SES; average monthly earnings, EUR.'),
  ('cbs_85517ned','cbs','Wages by occupation (85517NED)','85517NED',
     'https://opendata.cbs.nl/','official_table',
     'CC BY 4.0','https://www.cbs.nl/en-gb/about-us/website/copyright',
     'CBS open data may be reused, including commercially, with attribution to CBS.',
     'Source: Statistics Netherlands (CBS)','none','Annual (2013→); gross hourly wages P25/median/P75, EUR.'),
  ('ons_ashe_t14','ons','Annual Survey of Hours and Earnings — Table 14','ASHE-T14',
     'https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours','report_pdf',
     'Open Government Licence v3.0','https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
     'Free reuse, including commercial, with attribution under the UK Open Government Licence.',
     'Source: Office for National Statistics','none','2021–2024; mean + P10–P90 by 4-digit SOC, GBP.'),
  ('destatis_62361','destatis','Earnings by occupation (GENESIS 62361-0030)','62361-0030',
     'https://www-genesis.destatis.de/','official_table',
     'Data licence Germany – attribution – 2.0 (DL-DE-BY-2.0)','https://www.govdata.de/dl-de/by-2-0',
     'Free reuse, including commercial, with attribution under DL-DE-BY-2.0.',
     'Source: Statistisches Bundesamt (Destatis)','none','Gross monthly mean + median by KldB-2010, EUR.'),
  ('statcan_14100417','statcan','Employee wages by occupation (14-10-0417)','14-10-0417',
     'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410041701','official_table',
     'Statistics Canada Open Licence','https://www.statcan.gc.ca/en/reference/licence',
     'Free reuse, including commercial, with attribution under the Statistics Canada Open Licence.',
     'Source: Statistics Canada','none','Average + median wages by NOC × province, CAD.'),
  ('statsnz_inc004','statsnz','Income by occupation (INC_INC_004)','INC_INC_004',
     'https://explore.data.stats.govt.nz/','official_table',
     'CC BY 4.0','https://www.stats.govt.nz/help-with-using-this-site/',
     'Free reuse, including commercial, with attribution to Stats NZ.',
     'Source: Stats NZ','none','2009→; median + average earnings by ANZSCO major group, NZD.'),
  ('abs_eeh','abs','Employee Earnings and Hours (EEH), data cube 11','EEH-DC11',
     'https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions','official_table',
     'CC BY 4.0','https://www.abs.gov.au/website-privacy-copyright-and-disclaimer',
     'Free reuse, including commercial, with attribution to the ABS.',
     'Source: Australian Bureau of Statistics','none','Average earnings by detailed ANZSCO, AUD.'),
  ('surs_0711335s','surs','Earnings by occupation (SURS 0711335S)','0711335S',
     'https://pxweb.stat.si/','official_table',
     'CC BY 4.0','https://www.stat.si/StatWeb/en/about-us',
     'Free reuse, including commercial, with attribution to SURS.',
     'Source: Statistical Office of Slovenia (SURS)','none','2011–2022; P10–P90 + mean + median gross monthly, EUR.'),
  ('ibge_pnadc_9457','ibge','PNAD Contínua — earnings (SIDRA table 9457)','9457',
     'https://sidra.ibge.gov.br/tabela/9457','official_table',
     'IBGE reuse terms','https://www.ibge.gov.br/en/institutional/copyright.html',
     'IBGE data may be reused with attribution to IBGE.',
     'Source: IBGE','none','2012→; average earnings by ISCO major group, BRL (estimated monthly).'),
  ('fso_lse_205','fso','Swiss Earnings Structure Survey (px-x-0304010000_205)','px-x-0304010000_205',
     'https://www.pxweb.bfs.admin.ch/','official_table',
     'FSO/BFS terms of use','https://www.bfs.admin.ch/bfs/en/home/fso/terms-of-use.html',
     'FSO data may be reused with attribution to the Federal Statistical Office.',
     'Source: Federal Statistical Office (FSO)','none','2012–2024 biennial; median + P10–P90 standardised monthly wage, CHF.'),
  ('ine_70672','ine','Encuesta de Estructura Salarial (INE table 70672)','70672',
     'https://www.ine.es/jaxiT3/Tabla.htm?t=70672','official_table',
     'INE reuse terms','https://www.ine.es/en/aviso_legal_en.htm',
     'INE data may be reused, including commercial, with attribution to INE.',
     'Source: INE (Spain)','none','2018 SES; mean + P10–P90 gross monthly (annual ÷ 12), EUR.'),
  ('estat_0003426315','estat','Basic Survey on Wage Structure (e-Stat 0003426315)','0003426315',
     'https://www.e-stat.go.jp/dbview?sid=0003426315','official_table',
     'e-Stat terms of use','https://www.e-stat.go.jp/en/terms-of-use',
     'e-Stat statistics may be reused with attribution under the e-Stat terms of use.',
     'Source: e-Stat (Japan)','none','2020–2023; mean scheduled monthly cash earnings by JSCO-2020, JPY.')
on conflict (dataset_id) do nothing;

-- ══ Access methods (channel constraints) ═════════════════════════════════════
insert into public.compliance_access_method
  (access_id, dataset_id, method, endpoint_or_file, requires_api_key, caching_allowed_note,
   microdata_confidentiality_terms) values
  ('scb_am0110_api','scb_am0110','api','https://api.scb.se/OV0104/v1/doris/en/ssd/AM/AM0110/', false, 'Live fetch, disk-cached.', null),
  ('insee_fd_salaan_micro','insee_fd_salaan','microdata_download','INSEE FD_SALAAN microdata + Melodi means API', false,
     'Bundled microdata percentiles; Melodi means fetched live.',
     'Publish aggregated percentiles only; no re-identification. Confirm INSEE microdata reuse conditions.'),
  ('bls_oews_file','bls_oews','excel','BLS OEWS special-requests files (national + state + industry)', false, 'Bundled snapshot; re-downloadable from BLS.', null),
  ('dst_lons20_api','dst_lons20','api','https://api.statbank.dk/v1/data/LONS20/', false, 'Live fetch, disk-cached.', null),
  ('hagstofa_vin02001_api','hagstofa_vin02001','api','https://px.hagstofa.is/pxen/api/v1/', false, 'Live fetch, disk-cached.', null),
  ('statfin_15au_api','statfin_15au','api','https://statfin.stat.fi/PXWeb/api/v1/en/StatFin/', false, 'Live fetch, disk-cached.', null),
  ('statee_pa633_api','statee_pa633','api','https://andmed.stat.ee/api/v1/en/stat/', false, 'Live fetch, disk-cached.', null),
  ('cbs_85517ned_api','cbs_85517ned','api','https://opendata.cbs.nl/ODataApi/odata/85517NED', false, 'Live fetch (OData), disk-cached.', null),
  ('ons_ashe_t14_file','ons_ashe_t14','excel','ONS ASHE Table 14 workbooks', false, 'Bundled snapshot; re-downloadable from ONS.', null),
  ('destatis_62361_api','destatis_62361','api','https://www-genesis.destatis.de/genesisWS/rest/2020/', true, 'Bundled snapshot; rebuild via GENESIS API.', null),
  ('statcan_14100417_file','statcan_14100417','csv','StatCan WDS full-table CSV (14-10-0417)', false, 'Bundled snapshot; re-downloadable from StatCan.', null),
  ('statsnz_inc004_api','statsnz_inc004','api','https://explore.data.stats.govt.nz/ (SDMX)', true, 'Bundled snapshot; rebuild via Stats NZ API key.', null),
  ('abs_eeh_file','abs_eeh','excel','ABS EEH data cube 11 (XLSX)', false, 'Bundled snapshot; re-downloadable from ABS.', null),
  ('surs_0711335s_api','surs_0711335s','api','https://pxweb.stat.si/SiStatData/api/v1/en/Data/', false, 'Bundled snapshot; rebuild via PxWeb.', null),
  ('ibge_pnadc_9457_api','ibge_pnadc_9457','api','https://apisidra.ibge.gov.br/', false, 'Bundled snapshot; rebuild via SIDRA.', null),
  ('fso_lse_205_api','fso_lse_205','api','https://www.pxweb.bfs.admin.ch/api/v1/en/', false, 'Bundled snapshot; rebuild via PxWeb.', null),
  ('ine_70672_api','ine_70672','api','https://servicios.ine.es/wstempus/js/en/', false, 'Bundled snapshot; rebuild via Tempus3.', null),
  ('estat_0003426315_api','estat_0003426315','api','https://api.e-stat.go.jp/rest/3.0/app/', true, 'Bundled snapshot; rebuild via e-Stat API key.', null)
on conflict (access_id) do nothing;

-- ══ Country implementations (grandfathered=true, public_publishable=true) ═════
insert into public.compliance_country_impl
  (impl_id, country_slug, dataset_id, access_id, displayed_original_values,
   grandfathered, public_publishable, release_status, clearance_overall) values
  ('scb_am0110__se2','se2','scb_am0110','scb_am0110_api','Mean + P10–P90 monthly earnings (SEK) by SSYK occupation', true, true, 'public_ok', 'likely_verify'),
  ('insee_fd_salaan__fr2','fr2','insee_fd_salaan','insee_fd_salaan_micro','Net salary percentiles (EUR) by PCS occupation', true, true, 'public_ok', 'likely_verify'),
  ('bls_oews__us','us','bls_oews','bls_oews_file','Mean + P10–P90 annual wage (USD) by SOC occupation, national + state', true, true, 'beta_ok', 'likely_verify'),
  ('dst_lons20__denmark','denmark','dst_lons20','dst_lons20_api','Standardised monthly earnings (DKK) by DISCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('hagstofa_vin02001__iceland','iceland','hagstofa_vin02001','hagstofa_vin02001_api','Monthly earnings (ISK) by ISCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('statfin_15au__finland','finland','statfin_15au','statfin_15au_api','Monthly earnings (EUR; P10/median/P90) by ISCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('statee_pa633__estonia','estonia','statee_pa633','statee_pa633_api','Average monthly earnings (EUR) by ISCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('cbs_85517ned__netherlands','netherlands','cbs_85517ned','cbs_85517ned_api','Gross hourly wages (EUR; P25/median/P75) by BRC occupation', true, true, 'beta_ok', 'likely_verify'),
  ('ons_ashe_t14__uk','uk','ons_ashe_t14','ons_ashe_t14_file','Mean + P10–P90 (GBP) by SOC-2020 occupation', true, true, 'beta_ok', 'likely_verify'),
  ('destatis_62361__germany','germany','destatis_62361','destatis_62361_api','Gross monthly mean + median (EUR) by KldB-2010 occupation', true, true, 'beta_ok', 'likely_verify'),
  ('statcan_14100417__canada','canada','statcan_14100417','statcan_14100417_file','Average + median wages (CAD) by NOC occupation × province', true, true, 'beta_ok', 'likely_verify'),
  ('statsnz_inc004__newzealand','newzealand','statsnz_inc004','statsnz_inc004_api','Median + average earnings (NZD) by ANZSCO major group', true, true, 'beta_ok', 'likely_verify'),
  ('abs_eeh__australia','australia','abs_eeh','abs_eeh_file','Average earnings (AUD) by detailed ANZSCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('surs_0711335s__slovenia','slovenia','surs_0711335s','surs_0711335s_api','P10–P90 + mean + median gross monthly (EUR) by ISCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('ibge_pnadc_9457__brazil','brazil','ibge_pnadc_9457','ibge_pnadc_9457_api','Average earnings (BRL) by ISCO major group', true, true, 'beta_ok', 'likely_verify'),
  ('fso_lse_205__switzerland','switzerland','fso_lse_205','fso_lse_205_api','Median + P10–P90 standardised monthly wage (CHF) by ISCO occupation', true, true, 'beta_ok', 'likely_verify'),
  ('ine_70672__spain','spain','ine_70672','ine_70672_api','Mean + P10–P90 gross monthly (EUR) by CNO-11 occupation', true, true, 'beta_ok', 'likely_verify'),
  ('estat_0003426315__japan','japan','estat_0003426315','estat_0003426315_api','Mean scheduled monthly cash earnings (JPY) by JSCO-2020 occupation', true, true, 'beta_ok', 'likely_verify')
on conflict (impl_id) do nothing;

-- ══ Transformations (drive the Official / SE-calculation badges) ══════════════
-- Only the DATA-PIPELINE transformations are recorded here (currency/period
-- conversions, microdata-derived percentiles, real-terms series). Runtime user
-- actions common to all countries (multi-occupation aggregate toggle, leaderboard
-- ranking, projection tab) are labelled generically in-app, not per-country.
insert into public.compliance_transformation (impl_id, transform_type, origin, method_note, inputs) values
  ('insee_fd_salaan__fr2','aggregation','salary_explorer',
     'Per-occupation percentiles computed by Salary Explorer from the FD_SALAAN microdata.','INSEE Base Tous Salariés microdata'),
  ('dst_lons20__denmark','period_conversion','salary_explorer',
     'Published hourly earnings scaled by Salary Explorer to a standard month.','DST LONS20 hourly × standard monthly hours'),
  ('ons_ashe_t14__uk','inflation_adjustment','salary_explorer',
     'Real-terms (constant-price) series computed by Salary Explorer using CPIH.','ONS CPIH index'),
  ('statcan_14100417__canada','period_conversion','salary_explorer',
     'Published wages scaled by Salary Explorer to a standard month.','StatCan 14-10-0417 → standard month'),
  ('abs_eeh__australia','period_conversion','salary_explorer',
     'Published weekly earnings scaled by Salary Explorer to a standard month.','ABS EEH weekly × standard weeks'),
  ('ibge_pnadc_9457__brazil','period_conversion','salary_explorer',
     'Monthly earnings estimated by Salary Explorer from the published hourly figures.','IBGE SIDRA 9457 hourly → monthly'),
  ('ine_70672__spain','period_conversion','salary_explorer',
     'Official annual earnings divided by 12 by Salary Explorer to a monthly figure.','INE 70672 annual ÷ 12')
on conflict do nothing;

-- ══ Dataset-level assessments — every dimension for every backfilled dataset ══
-- likely_verify for all dimensions except attribution (confirmed). +12-month
-- review. reviewed_by intentionally NULL until the owner reviews.
insert into public.compliance_assessment
  (subject_type, subject_id, dimension, status, next_review_date)
select 'dataset', d.dataset_id, dim.dimension,
       case when dim.dimension = 'attribution' then 'confirmed' else 'likely_verify' end,
       (now() + interval '12 months')::date
from (values
  ('scb_am0110'),('insee_fd_salaan'),('bls_oews'),('dst_lons20'),('hagstofa_vin02001'),
  ('statfin_15au'),('statee_pa633'),('cbs_85517ned'),('ons_ashe_t14'),('destatis_62361'),
  ('statcan_14100417'),('statsnz_inc004'),('abs_eeh'),('surs_0711335s'),('ibge_pnadc_9457'),
  ('fso_lse_205'),('ine_70672'),('estat_0003426315')
) as d(dataset_id)
cross join (values
  ('access'),('commercial'),('redistribute'),('derive'),('store_cache'),('attribution')
) as dim(dimension)
on conflict (subject_type, subject_id, dimension) do nothing;

-- Access-level: INSEE microdata confidentiality (framework §11).
insert into public.compliance_assessment
  (subject_type, subject_id, dimension, status, evidence_note, next_review_date) values
  ('access','insee_fd_salaan_micro','microdata_confidentiality','provider_confirm',
     'Publish aggregated percentiles only; confirm INSEE microdata reuse conditions.',
     (now() + interval '12 months')::date)
on conflict (subject_type, subject_id, dimension) do nothing;

-- Audit-log entry.
insert into public.compliance_review_log (subject_type, subject_id, action, actor, before_after) values
  ('impl','(phase1-backfill)','backfill_created','system',
   jsonb_build_object('note','Phase 1 backfill: 18 remaining countries inserted'));
