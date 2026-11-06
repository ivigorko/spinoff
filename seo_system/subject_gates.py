"""Focused subject contracts; these checks do not replace expert SEO review."""
from urllib.parse import urlsplit
from .core import WorkflowError, canonical, check_url

REVIEWED_ROLES = {
 'keywords.keyword-discovery','keywords.intent-classifier','keywords.cluster-builder',
 'content.brief-writer','content.seo-blog-writer','content.meta-tag-writer','content.content-optimizer',
 'technical.site-crawler','technical.core-web-vitals-analyst','links.backlink-auditor',
 'local.citation-builder','ecommerce.product-schema-generator','strategy.priority-matrix-builder',
 'strategy.roadmap-planner','audit.data-compiler','audit.recommendation-engine','audit.fix-generator',
 'audit.report-builder','analytics.traffic-analyst','analytics.roi-calculator','analytics.monthly-report-writer',
 'operations.release-record','operations.production-verify','operations.measurement','operations.onboard'}


def subject_roles():return REVIEWED_ROLES


def records(sources, kind):
    out=[]
    for manifest,document in sources.values():
        if manifest['kind']==kind:
            value=document.get('records',[]) if isinstance(document,dict) else document
            if isinstance(value,list):out.extend(value)
    return out


def nonempty_list(value, fields, name):
    if not isinstance(value,list) or not value:
        raise WorkflowError('Subject contract requires a nonempty list: '+name)
    for record in value:
        if not isinstance(record,dict) or not set(fields)<=record.keys():
            raise WorkflowError('Subject record fields missing: '+name)
    return value


def source_match(sources,kind,record,fields):
    return any(all(canonical(row.get(k))==canonical(record.get(k)) for k in fields) for row in records(sources,kind) if isinstance(row,dict))


def validate_subject(result,sources,inputs,profile,spec,pointer,comparison_validator):
    if not result['coverage']['complete']:return
    role=result['role'];data=result['data']
    if result.get('work_mode')=='planning':
        nonempty_list(data['target_pages'],['url','status'],'target_pages')
        nonempty_list(data['planned_changes'],['action','rationale'],'planned_changes')
        nonempty_list(data['acceptance_plan'],['check','expected'],'acceptance_plan')
        for page in data['target_pages']:
            check_url(page['url'],profile['allowed_hosts'])
            if page['status']!='proposed':raise WorkflowError('Planning pages must be marked proposed, not observed')
        return
    if spec.get('report_kind')=='campaign_plan':
        nonempty_list(data['prospect_register'],['prospect_id','url','status'],'prospect_register')
        nonempty_list(data['draft_messages'],['prospect_id','subject','body','status'],'draft_messages')
        tracking=data['tracking_plan']
        if not isinstance(tracking,dict) or not {'owner','metrics','next_check','executor_status'}<=tracking.keys():raise WorkflowError('Campaign tracking plan is missing')
        if tracking['executor_status']!='not_scheduled':raise WorkflowError('Coordinator cannot attest that a campaign monitor is scheduled')
        ids={row['prospect_id'] for row in data['prospect_register']}
        if any(row['prospect_id'] not in ids or row['status']!='draft' for row in data['draft_messages']):raise WorkflowError('Campaign messages must be linked drafts, not sent claims')
    keyword_rows=records(sources,'keywords')
    queries={r.get('query') for r in keyword_rows if isinstance(r,dict)}
    for product in inputs:
        for row in product['data'].get('candidates',[]) if isinstance(product['data'].get('candidates'),list) else []:
            if isinstance(row,dict):queries.add(row.get('query'))
    page_rows=records(sources,'pages')
    page_urls={r.get('url') for r in page_rows if isinstance(r,dict)}
    findings=[]
    for product in inputs:
        if isinstance(product['data'].get('findings'),list):findings.extend(product['data']['findings'])
    inherited_finding_ids={r.get('finding_id') for r in findings if isinstance(r,dict)}
    for _,document in sources.values():
        if isinstance(document,dict) and isinstance(document.get('findings'),list):findings.extend(document['findings'])
    finding_ids={r.get('finding_id') for r in findings if isinstance(r,dict)}
    task_fields=['task_id','finding_ids','url','action','owner','effort_hours','dependencies','risk','acceptance_test','metric','measurement_window','required_permission']
    def tasks(value,name):
        if value==[] and isinstance(data.get('no_action_reason'),str) and data['no_action_reason'].strip():return []
        rows=nonempty_list(value,task_fields,name)
        ids=[r['task_id'] for r in rows]
        if len(set(ids))!=len(ids):raise WorkflowError('Duplicate task IDs')
        for task in rows:
            check_url(task['url'],profile['allowed_hosts'])
            if not isinstance(task['finding_ids'],list) or set(task['finding_ids'])-finding_ids:
                raise WorkflowError('Task references unknown findings')
            if not isinstance(task['dependencies'],list) or set(task['dependencies'])-set(ids):
                raise WorkflowError('Task dependency does not resolve')
            if task['effort_hours'] is not None and (isinstance(task['effort_hours'],bool) or not isinstance(task['effort_hours'],(int,float)) or task['effort_hours']<0):
                raise WorkflowError('Invalid effort estimate')
        graph={r['task_id']:r['dependencies'] for r in rows}
        def visit(key,trail):
            if key in trail:raise WorkflowError('Task dependency cycle')
            for dep in graph[key]:visit(dep,trail|{key})
        for key in graph:visit(key,set())
        return rows
    if role=='keywords.keyword-discovery':
        for row in nonempty_list(data['candidates'],['query','frequency','method'],'candidates'):
            if row['frequency'] is not None and not source_match(sources,'keywords',row,['query','frequency','method']):
                raise WorkflowError('Keyword frequency is not supported by measured keyword evidence')
    elif role=='keywords.intent-classifier':
        for row in nonempty_list(data['intent_map'],['query','intent','confidence'],'intent_map'):
            if row['query'] not in queries or row['intent'] not in {'informational','navigational','commercial','transactional','mixed'}:
                raise WorkflowError('Intent query or classification does not resolve')
    elif role=='keywords.cluster-builder':
        clusters=nonempty_list(data['clusters'],['cluster_id','intent','members','target_url'],'clusters')
        mapping=nonempty_list(data['url_mapping'],['query','existing_url','action'],'url_mapping')
        ids=[c['cluster_id'] for c in clusters]
        if len(ids)!=len(set(ids)):raise WorkflowError('Duplicate cluster IDs')
        mapped={r['query']:r for r in mapping}
        for cluster in clusters:
            if not isinstance(cluster['members'],list) or not cluster['members'] or set(cluster['members'])-queries:
                raise WorkflowError('Cluster members are not in the declared keyword universe')
            if set(cluster['members'])-mapped.keys():raise WorkflowError('Cluster mapping is incomplete')
            if cluster['target_url'] is not None:check_url(cluster['target_url'],profile['allowed_hosts'])
        for row in mapping:
            if row['query'] not in queries or row['action'] not in {'retain','update','create'}:raise WorkflowError('Invalid keyword mapping')
            if row['existing_url'] is not None:
                check_url(row['existing_url'],profile['allowed_hosts'])
                if row['action']!='create' and row['existing_url'] not in page_urls:
                    raise WorkflowError('Existing landing page has no page evidence')
    elif role=='content.brief-writer':
        if not isinstance(data['outline'],list) or not data['outline'] or not all(isinstance(x,str) and x.strip() for x in data['outline']):raise WorkflowError('Brief needs a concrete outline')
        if not isinstance(data['intent'],dict) or not {'query','intent','target_url'}<=data['intent'].keys():raise WorkflowError('Brief intent/target is missing')
        check_url(data['intent']['target_url'],profile['allowed_hosts'])
    elif role=='content.seo-blog-writer':
        if not isinstance(data['draft'],str) or not data['draft'].strip():raise WorkflowError('Draft must contain actual text')
    elif role=='content.meta-tag-writer':
        meta=data['selected_metadata']
        if not isinstance(meta,dict) or not all(isinstance(meta.get(k),str) and meta[k].strip() for k in ['url','title','description']):raise WorkflowError('Selected metadata must contain actual URL/title/description')
        check_url(meta['url'],profile['allowed_hosts'])
        draft_inputs=[p for p in inputs if p['role'] in {'content.seo-blog-writer','content.landing-page-copywriter','content.content-optimizer'}]
        if meta['url'] not in page_urls and not draft_inputs:raise WorkflowError('Metadata has neither page evidence nor an accepted draft')
    elif role=='content.content-optimizer':
        if not isinstance(data['revised_content'],str) or not data['revised_content'].strip():raise WorkflowError('Optimizer needs a concrete revised draft')
        if spec.get('work_mode')=='draft':
            draft_ids={p['_artifact_id'] for p in inputs if p['role']=='content.seo-blog-writer'}
            if not isinstance(data['baseline'],dict) or data['baseline'].get('artifact_id') not in draft_ids:raise WorkflowError('Draft optimization must reference the accepted draft')
    elif role=='technical.site-crawler':
        for row in nonempty_list(data['inventory'],['url','status_code'],'inventory'):
            if not source_match(sources,'pages',row,['url','status_code']):raise WorkflowError('Crawl inventory contradicts pages evidence')
    elif role=='technical.core-web-vitals-analyst':
        for row in nonempty_list(data['field_data'],['url','kind','lcp_ms','inp_ms','cls'],'field_data'):
            if not source_match(sources,'performance',row,['url','kind','lcp_ms','inp_ms','cls']):raise WorkflowError('CWV metrics have no performance evidence')
    elif role=='links.backlink-auditor':
        if not isinstance(data['coverage'],dict) or data['coverage'].get('kind')!='inbound':raise WorkflowError('Backlink analysis must distinguish inbound coverage')
        inbound=[r for r in records(sources,'backlinks') if isinstance(r,dict) and r.get('kind')=='inbound']
        if not inbound:raise WorkflowError('Outbound links cannot establish an inbound backlink profile')
        domains={urlsplit(r['source_url']).hostname for r in inbound}
        if not isinstance(data['domains'],list) or not set(data['domains'])<=domains:raise WorkflowError('Referring domains are unsupported')
    elif role=='local.citation-builder':
        nap=data['canonical_nap']
        if not isinstance(nap,dict) or not {'name','address','contact_ref'}<=nap.keys() or not source_match(sources,'local',nap,['name','address','contact_ref']):raise WorkflowError('Canonical NAP has no local business evidence')
    elif role=='ecommerce.product-schema-generator':
        for row in nonempty_list(data['product_data'],['sku','name','price','currency','availability'],'product_data'):
            if not source_match(sources,'products',row,['sku','name','price','currency','availability']):raise WorkflowError('Product facts contradict catalog evidence')
        ld=data['json_ld']
        if not isinstance(ld,dict) or ld.get('@type')!='Product' or not isinstance(data['validation'],dict) or data['validation'].get('status') not in {'syntax_only','manual_feature_review'}:raise WorkflowError('Product JSON-LD/validation status is missing')
        offers=ld.get('offers')
        if not isinstance(offers,dict) or not any(ld.get('name')==row['name'] and offers.get('price')==row['price'] and offers.get('priceCurrency')==row['currency'] and offers.get('availability') in {row['availability'],'https://schema.org/'+row['availability']} for row in data['product_data']):raise WorkflowError('Generated Product JSON-LD contradicts catalog facts')
        if 'aggregateRating' in ld or 'review' in ld:raise WorkflowError('Reviews require a dedicated reviewed contract, not inferred ratings')
    elif role=='audit.data-compiler':
        rows=[] if data['findings']==[] and data.get('no_action_reason') else nonempty_list(data['findings'],['finding_id','url','action','evidence'],'findings')
        if inherited_finding_ids-{f['finding_id'] for f in rows}:raise WorkflowError('Output drops accepted upstream findings')
        for finding in rows:
            ref=finding['evidence']
            if ref.get('source_id') not in sources or canonical(pointer(sources[ref['source_id']][1],ref['pointer']))!=canonical(ref['value']):raise WorkflowError('Compiled finding has no matching evidence')
    elif role=='audit.recommendation-engine':tasks(data['recommendations'],'recommendations')
    elif role=='strategy.priority-matrix-builder':tasks(data['scored_tasks'],'scored_tasks')
    elif role=='strategy.roadmap-planner':
        rows=tasks(data['tasks'],'tasks')
        input_tasks=[t for p in inputs for key in ['scored_tasks','tasks','recommendations'] for t in (p['data'].get(key,[]) if isinstance(p['data'].get(key),list) else [])]
        if input_tasks and {t['task_id'] for t in input_tasks}-{t['task_id'] for t in rows}:raise WorkflowError('Roadmap loses accepted priority tasks')
    elif role=='audit.fix-generator':
        baseline=data['baseline']
        if not isinstance(baseline,dict) or not baseline.get('revision'):raise WorkflowError('Prepared changes need a baseline revision')
        for patch in nonempty_list(data['patches'],['task_id','finding_ids','url','field','before','after'],'patches'):
            check_url(patch['url'],profile['allowed_hosts'])
            baseline_sources={sid:(m,d) for sid,(m,d) in sources.items() if m['site_revision']==baseline['revision']}
            if not source_match(baseline_sources,'pages',{'url':patch['url'],patch['field']:patch['before']},['url',patch['field']]):raise WorkflowError('Prepared patch baseline contradicts page evidence')
            if not any(m['kind']=='pages' and m['site_revision']==baseline['revision'] for m,d in sources.values()):raise WorkflowError('Prepared baseline revision has no page evidence')
        nonempty_list(data['tests'],['test','result'],'tests')
        if not isinstance(data['rollback'],dict):raise WorkflowError('Prepared change needs a concrete rollback')
    elif role=='analytics.traffic-analyst':
        comparison_validator(data['changes'],sources=sources)
        if spec.get('minimum_window_days'):
            from datetime import date
            for period in ['baseline','current']:
                window=data['changes'][period]
                if (date.fromisoformat(window['end'])-date.fromisoformat(window['start'])).days+1<spec['minimum_window_days']:raise WorkflowError('Review window is shorter than the declared quarterly scope')
    elif role=='analytics.roi-calculator':
        c=data['calculations']
        if not isinstance(c,dict) or c.get('status')!='computed':raise WorkflowError('Non-computable ROI must be partial, not completed')
        for key in ['cost','attributed_value']:
            ref=c.get(key+'_evidence',{})
            if ref.get('source_id') not in sources or canonical(pointer(sources[ref['source_id']][1],ref.get('pointer','')))!=canonical(c.get(key)):raise WorkflowError('ROI input has no financial evidence')
        financials=[d.get('financials') for m,d in sources.values() if m['kind']=='analytics' and isinstance(d,dict)]
        if not any(isinstance(f,dict) and all(c.get(k)==f.get(k) and c.get(k) is not None for k in ['currency','model','period']) for f in financials):raise WorkflowError('ROI currency, attribution model and period must match financial evidence')
        if c['cost']<=0 or abs(c['roi_percent']-100*(c['attributed_value']-c['cost'])/c['cost'])>1e-8:raise WorkflowError('ROI arithmetic is invalid')
    elif role=='audit.report-builder':
        rows=[] if data['findings']==[] and data.get('no_action_reason') else nonempty_list(data['findings'],['finding_id','url','action','evidence'],'findings')
        if inherited_finding_ids-{f['finding_id'] for f in rows}:raise WorkflowError('Output drops accepted upstream findings')
        for finding in rows:
            ref=finding['evidence']
            if not isinstance(ref,dict) or ref.get('source_id') not in sources or canonical(pointer(sources[ref['source_id']][1],ref['pointer']))!=canonical(ref['value']):raise WorkflowError('Reported finding has no matching source evidence')
        if not isinstance(data['roadmap'],dict):raise WorkflowError('Report roadmap is missing')
        tasks(data['roadmap'].get('tasks'),'report.roadmap.tasks')
    elif role=='analytics.monthly-report-writer':
        if not (data['work_log']==[] and data.get('no_action_reason')):nonempty_list(data['work_log'],['task_id','status'],'work_log')
        for item in data['work_log']:
            if item['status'] not in {'prepared','applied','verified','measured'}:raise WorkflowError('Unknown work-log status')
            if item['status'] in {'verified','measured'}:
                # A release alone cannot prove QA or a measurement. Require the actual accepted predecessor.
                wanted='operations.production-verify' if item['status']=='verified' else 'operations.measurement'
                if not any(p['role']==wanted and p['coverage']['complete'] for p in inputs):raise WorkflowError('Work log status needs an accepted verification or measurement predecessor')
            if item['status']!='prepared' and not any(m['kind']=='release' and item['task_id'] in d.get('release',{}).get('task_ids',[]) for m,d in sources.values() if isinstance(d,dict)):
                raise WorkflowError('Work log invents a release status')
