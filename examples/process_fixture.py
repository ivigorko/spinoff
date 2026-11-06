"""Synthetic procedure-contract fixtures. No live data, analysis or publication is performed."""
from __future__ import annotations
import argparse
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from examples.create_demo import create
from seo_system.core import canonical, config, digest
from seo_system import processes as p


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    return Path(path)


def fixture(directory, clock=None, window_days=28):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    clock = clock or datetime.now(timezone.utc)
    profile, _ = create(directory, clock.isoformat())
    expanded = json.loads(profile.read_text())
    expanded.update(business_type='services', business_profile={'offer':'Synthetic service','audience':'Synthetic audience','geography':'demo-only','business_model':'Synthetic service'},
                    competitors=[{'host':'competitor.example','reason':'Synthetic comparison'}],
                    brand_voice={'tone':'clear','do':['Explain facts'],'avoid':['Invented claims'],'approved_examples':[]},
                    resources={'owners':['synthetic owner'],'technical_hours':None,'content_hours':None,'constraints':['Unknown capacity; scenario plan only']},
                    conversion_definitions=[{'name':'synthetic inquiry','definition':'Synthetic test event','unit':'events','source_ref':None}],
                    source_bindings=[], constraints=['No real services or external actions'])
    write(profile, expanded)
    signature = {'property_ref':'synthetic-property','timezone':'Etc/UTC','definition_version':'organic-session-v1','filters_hash':'synthetic-filter-v1'}
    scope = {'host': 'example.com', 'region': 'demo-only', 'engine': 'google', 'device': 'desktop', **signature}
    end = clock.date()-timedelta(days=3)
    start = end-timedelta(days=window_days-1)
    b_end = start-timedelta(days=1)
    b_start = b_end-timedelta(days=window_days-1)
    metrics = [{'start': str(b_start), 'end': str(b_end), 'scope': scope.copy(), 'metric': 'organic_sessions', 'unit': 'sessions', 'value': 100},
               {'start': str(start), 'end': str(end), 'scope': scope.copy(), 'metric': 'organic_sessions', 'unit': 'sessions', 'value': 120}]
    release = {'release_id': 'synthetic-release-1', 'released_at': str(start)+'T00:00:00+00:00',
               'baseline_revision': 'synthetic-v1', 'target_revision': 'synthetic-v2', 'urls': ['https://example.com/'],
               'authorization_ref': 'synthetic fixture only; not permission for an external action', 'task_ids': ['synthetic-title-task'],
               'expected_changes':[{'task_id':'synthetic-title-task','url':'https://example.com/','field':'title','expected':'Synthetic service'}]}
    documents = {
      'business': {'offer': 'Synthetic service', 'goal': 'Useful tested site', 'audience': 'Synthetic audience', 'capacity_hours': None,
                   'findings':[{'finding_id':'synthetic-missing-title','url':'https://example.com/','action':'Prepare a useful title'}]},
      'market': {'region': 'demo-only', 'segments': ['synthetic service demand'], 'market_size': None},
      'search_updates': {'updates': [], 'note': 'Synthetic: no claim about a real search update'},
      'serp': {'records': [{'query': 'synthetic service', 'url': 'https://example.com/', 'engine': 'google', 'region': 'demo-only', 'device': 'desktop', 'position': 4}]},
      'keywords': {'records': [{'query': 'synthetic service', 'frequency': 100, 'method': 'synthetic fixture', 'intent': 'commercial', 'url': 'https://example.com/'}]},
      'competitors': {'records': [{'host': 'competitor.example', 'selection': 'Synthetic comparison'}]},
      'pages': {'records': [{'url': 'https://example.com/', 'status_code': 200, 'title': '', 'h1': 'Synthetic service'}]},
      'indexation': {'robots': 'allow', 'sitemap_urls': ['https://example.com/'], 'indexed': None, 'method': 'synthetic signal, not actual index status'},
      'performance': {'records': [{'url': 'https://example.com/', 'kind': 'synthetic field URL p75', 'lcp_ms': 2400, 'inp_ms': 190, 'cls': 0.05}]},
      'schema': {'records': [{'url': 'https://example.com/', 'type': 'Organization', 'synthetic_valid': True}]},
      'internal_links': {'records': [{'source_url': 'https://example.com/', 'target_url': 'https://example.com/'}], 'complete': True},
      'content': {'records': [{'url': 'https://example.com/', 'purpose': 'Explain synthetic service', 'body': 'A fictional service for a contract test. No real claims.'}]},
      'backlinks': {'records': [{'source_url': 'https://partner.example/resource', 'target_url': 'https://example.com/', 'kind': 'inbound','placement_type':'synthetic editorial'}]},
      'ai_visibility': {'records': [{'platform': 'synthetic platform', 'prompt': 'Explain synthetic service', 'answer': 'Synthetic service: https://example.com/', 'mention': True, 'citation_url': 'https://example.com/', 'observed_at': clock.isoformat()}]},
      'local': {'records': [{'name': 'Synthetic location', 'address': 'Fictional location only', 'profile': 'synthetic profile','contact_ref':'synthetic-public-contact'}]},
      'products': {'records': [{'name': 'Synthetic product', 'sku': 'TEST-1', 'price': 10, 'currency': 'USD', 'availability': 'InStock'}]},
      'analytics': {'records': metrics,'financials':{'cost':100,'attributed_value':150,'currency':'USD','model':'synthetic attribution only','period':{'start':str(start),'end':str(end)}}},
      'logs': {'records': [{'path': '/', 'status': 200, 'bot_identity': 'synthetic verified identity', 'requests': 3}]},
      'release': {'release': release},
      'verification': {'records': [{'url': 'https://example.com/', 'title': 'Synthetic service', 'status_code': 200}]}
    }
    manifests = {}
    for kind, document in documents.items():
        source_file = write(directory/(kind+'.json'), document)
        manifest = {'schema_version': 1, 'source_id': 'src-'+kind.replace('_','-'), 'project_id': 'synthetic-demo', 'kind': kind,
                    'source_locator': 'synthetic:'+kind, 'primary_origin': 'explicitly synthetic test fixture', 'file': source_file.name,
                    'sha256': digest(source_file.read_bytes()), 'host': 'example.com',
                    'scope': {'region': 'demo-only', 'language': 'ru', 'engine': 'google', 'device': 'desktop'},
                    'site_revision': 'synthetic-v2' if kind in {'verification','release'} else 'synthetic-v1',
                    'purpose': 'post_release' if kind in {'verification','release'} else 'current',
                    'source_generated_at': clock.isoformat(), 'collected_at': clock.isoformat(), 'period': {'start': str(b_start), 'end': str(end)} if kind=='analytics' else None,
                    'classification': 'synthetic', 'coverage': {'complete': True, 'limitations': []}}
        manifests[kind] = write(directory/(kind+'.manifest.json'), manifest)
        if kind=='analytics':
            manifest['analytics_signature']=signature
            write(manifests[kind],manifest)
    post_manifest = json.loads(manifests['pages'].read_text())
    post_pages = copy.deepcopy(documents['pages'])
    post_pages['records'][0]['title'] = 'Synthetic service'
    post_file = write(directory/'pages-post.json',post_pages)
    post_manifest.update(source_id='src-pages-post', purpose='post_release', site_revision='synthetic-v2',file=post_file.name,sha256=digest(post_file.read_bytes()))
    manifests['pages_post'] = write(directory/'pages-post.manifest.json', post_manifest)
    return {'profile': profile, 'manifests': manifests, 'documents': documents, 'release': release, 'metrics': metrics, 'clock': clock}


def result_for(root, state, node, inputs):
    draft = p.template(root, state['project_id'], state['run_id'], node['id'])
    role = p.catalog()[node['role']]
    # Structured fictional products exercise lineage and gates, not the quality of a real SEO analysis.
    selected_kinds=node.get('required_evidence_kinds',role['required_evidence_kinds'])
    base = {'scope':'reduced synthetic coordination case; not expert certification',
            'source_snapshots':{kind:inputs['documents'][kind] for kind in selected_kinds}}
    draft['data'] = {section: copy.deepcopy(base) for section in draft['data']}
    named = {
      'seeds': ['synthetic service'], 'candidates': inputs['documents']['keywords']['records'],
      'clusters': [{'cluster_id': 'cluster-service', 'intent': 'commercial', 'members': ['synthetic service'], 'target_url': 'https://example.com/'}],
      'url_mapping': [{'query': 'synthetic service', 'existing_url': 'https://example.com/', 'action': 'retain'}],
      'intent_map': [{'query': 'synthetic service', 'intent': 'commercial', 'confidence': 'synthetic'}],
      'draft': 'Synthetic service. This fictional page demonstrates useful, sourced content for a test.',
      'metadata': {'title': 'Synthetic service', 'description': 'A fictional service used only for contract tests.'},
      'selected_metadata': {'url':'https://example.com/','title':'Synthetic service','description':'A fictional service used only for contract tests.'},
      'outline':['What the synthetic service provides','Conditions and next steps'],
      'intent':{'query':'synthetic service','intent':'commercial','target_url':'https://example.com/'},
      'revised_content':'Synthetic service. A fictional, reviewed draft for contract tests.',
      'inventory': inputs['documents']['pages']['records'],
      'findings': [{'finding_id': 'synthetic-missing-title', 'url': 'https://example.com/', 'code': 'missing_title', 'action': 'Prepare a useful title', 'evidence': {'source_id': 'src-pages', 'pointer': '/records/0/title', 'value': ''}}],
      'json_ld': {'@context': 'https://schema.org', '@type': 'Product', 'name': 'Synthetic product', 'offers':{'@type':'Offer','price':10,'priceCurrency':'USD','availability':'https://schema.org/InStock'}},
      'product_data': inputs['documents']['products']['records'],
      'validation':{'status':'syntax_only','external_feature_validation':'not_run'},
      'canonical_nap':{k:inputs['documents']['local']['records'][0][k] for k in ['name','address','contact_ref']},
      'domains':['partner.example'],
      'field_data': inputs['documents']['performance']['records'],
      'next_backlog': [{'task_id': 'synthetic-follow-up', 'action': 'Review measured change and test another hypothesis'}],
      'periods': inputs['metrics'], 'release': inputs['release'],
      'checks': [{'url': 'https://example.com/', 'field': 'title', 'expected': 'Synthetic service', 'actual': 'Synthetic service', 'evidence': {'source_id': 'src-verification', 'pointer': '/records/0/title'}}]
    }
    named['profile'] = json.loads(inputs['profile'].read_text())
    task={'task_id':'synthetic-title-task','finding_ids':['synthetic-missing-title'],'url':'https://example.com/','action':'Set title to Synthetic service','owner':'synthetic developer','effort_hours':None,'dependencies':[],'risk':'Preserve page content','acceptance_test':'Fresh rendered title equals Synthetic service','metric':'organic_sessions','measurement_window':'Synthetic closed 28-day windows','required_permission':'No real permission: fixture only'}
    named.update(tasks=[task],scored_tasks=[task],recommendations=[task],priorities=[task],baseline={'revision':'synthetic-v1','url':'https://example.com/','title':''},
                 patches=[{'task_id':'synthetic-title-task','finding_ids':['synthetic-missing-title'],'url':'https://example.com/','field':'title','before':'','after':'Synthetic service'}],
                 tests=[{'test':'title change and content preserved','result':'synthetic pass'}],rollback={'revision':'synthetic-v1','title':''},authorization_boundary={'status':'synthetic only; no live action'})
    named['roadmap']={'tasks':[task],'capacity':'unknown; scenario only'}
    named['work_log']=[{'task_id':'synthetic-title-task','status':'applied'}]
    named['calculations']={'status':'computed','cost':100,'attributed_value':150,'roi_percent':50,**{k:inputs['documents']['analytics']['financials'][k] for k in ['currency','model','period']},
                          'cost_evidence':{'source_id':'src-analytics','pointer':'/financials/cost'},
                          'attributed_value_evidence':{'source_id':'src-analytics','pointer':'/financials/attributed_value'}}
    a,b=copy.deepcopy(inputs['metrics'])
    a['evidence']={'source_id':'src-analytics','pointer':'/records/0/value'}
    b['evidence']={'source_id':'src-analytics','pointer':'/records/1/value'}
    named['changes']={'baseline':a,'current':b,'absolute_change':20,'percent_change':20.0}
    for section in draft['data']:
        if section in named:draft['data'][section] = copy.deepcopy(named[section])
    if node['role']=='operations.measurement':
        a,b=copy.deepcopy(inputs['metrics'])
        a['evidence']={'source_id':'src-analytics','pointer':'/records/0/value'}
        b['evidence']={'source_id':'src-analytics','pointer':'/records/1/value'}
        draft['data']['comparison']={'baseline':a,'current':b,'absolute_change':20,'percent_change':20.0}
        draft['data']['decision']={'status':'measured','interpretation':'Synthetic association only, no causal attribution'}
    kinds=set(selected_kinds)|{'business'}
    if 'findings' in draft['data'] or 'patches' in draft['data']:kinds.add('pages')
    if node['role']=='keywords.cluster-builder' and state['workflow']!='new-site-launch':kinds.add('pages')
    if state['workflow']=='new-site-launch' and node['role']=='keywords.cluster-builder':
        draft['data']['url_mapping'][0]['action']='create'
    if node['role'].startswith('keywords.') or node['role']=='content.brief-writer':kinds.add('keywords')
    if node['role']=='analytics.monthly-report-writer':kinds.add('release')
    draft['source_ids']=['src-'+kind.replace('_','-') for kind in sorted(kinds)]
    if node['id'] == 'post-audit':
        draft['source_ids'] = ['src-pages-post' if sid == 'src-pages' else sid for sid in draft['source_ids']]
    if node['role']=='links.backlink-auditor':
        draft['data']['coverage']={'kind':'inbound','universe':'selected synthetic export only'}
    if node['role']=='content.content-optimizer' and node.get('work_mode')=='draft':
        from seo_system.processes import connection,product
        con=connection(root)
        try:
            _,aid=product(con,root,state['project_id'],state['run_id'],'draft')
            draft['data']['baseline']={'kind':'accepted_draft','artifact_id':aid}
        finally:con.close()
    if node.get('work_mode')=='planning':
        draft['data'].update(target_pages=[{'url':'https://example.com/','status':'proposed'}],
                            planned_changes=[{'action':'Prepare '+node['id']+' rules','rationale':'Launch planning only; no live audit'}],
                            acceptance_plan=[{'check':'Inspect actual published page after release','expected':'Matches approved launch plan'}],
                            limitations=['No live pages observed'])
    if node.get('report_kind')=='campaign_plan':
        draft['data'].update(campaign_summary='Fictional campaign plan, no outreach performed',
                            prospect_register=[{'prospect_id':'synthetic-partner','url':'https://partner.example/resource','status':'candidate'}],
                            draft_messages=[{'prospect_id':'synthetic-partner','subject':'Fictional resource suggestion','body':'A synthetic draft, not sent.','status':'draft'}],
                            tracking_plan={'owner':'synthetic owner','metrics':['placements observed','qualified replies'],'next_check':'After an authorized campaign starts','executor_status':'not_scheduled'},
                            limitations=['No delivery, prospect contact validation or live tracking performed'])
    draft['claims']=[{'classification':'fact','text':'The synthetic source describes a fictional offer.', 'evidence':[{'source_id':'src-business','pointer':'/offer','value':'Synthetic service'}]}]
    if 'findings' in draft['data']:
        draft['claims'].append({'classification':'fact','text':'The synthetic baseline title is empty.','evidence':[{'source_id':'src-pages','pointer':'/records/0/title','value':''}]})
    draft['coverage']={'complete':True,'limitations':[]}
    for check in draft['qa']:
        check.update(passed=True,note='Synthetic structural contract case only; not a live expert QA or external action')
    return draft


def run_fixture(directory, workflow='agency-cycle', clock=None):
    directory=Path(directory)
    inputs=fixture(directory/'inputs',clock,window_days=90 if workflow=='quarterly-review' else 28)
    root=directory/'state'
    state=p.start(inputs['profile'],workflow,root,synthetic=True,clock=inputs['clock'])
    for manifest in inputs['manifests'].values():p.add_source(root,state['project_id'],state['run_id'],manifest,inputs['clock'])
    for node in state['nodes']:
        product=result_for(root,state,node,inputs)
        output=write(directory/'result.json',product)
        p.submit(root,state['project_id'],state['run_id'],node['id'],output,inputs['clock'])
    return p.status(root,state['project_id'],state['run_id'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--workflow',default='agency-cycle');args=parser.parse_args()
    print(json.dumps(run_fixture(args.output,args.workflow),ensure_ascii=False,indent=2))
