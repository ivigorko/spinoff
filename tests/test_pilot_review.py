"""Adversarial acceptance tests against real persistent coordinator entry points."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from examples.process_fixture import fixture, result_for, run_fixture, write
from seo_system import processes as p
from seo_system.core import WorkflowError, canonical, config, digest, selected_input
from tests.test_processes import CLOCK


class PilotReviewTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.base=Path(temp.name);self.inputs=fixture(self.base/'input',CLOCK);self.root=self.base/'state'

    def start(self,workflow,register=True,exclude=()):
        self.state=p.start(self.inputs['profile'],workflow,self.root,True,CLOCK)
        if register:
            for kind,manifest in self.inputs['manifests'].items():
                if kind not in exclude:p.add_source(self.root,self.state['project_id'],self.state['run_id'],manifest,CLOCK)

    def result(self,node):
        return result_for(self.root,self.state,next(n for n in self.state['nodes'] if n['id']==node),self.inputs)

    def submit(self,node,result=None):
        return p.submit(self.root,self.state['project_id'],self.state['run_id'],node,write(self.base/'result.json',result or self.result(node)),CLOCK)

    def advance(self,target):
        for node in self.state['nodes']:
            if node['id']==target:return
            self.submit(node['id'])

    def rejected_role(self,role,mutate,message):
        self.start('role:'+role)
        result=self.result('work');mutate(result)
        with self.assertRaisesRegex(WorkflowError,message):self.submit('work',result)
        status=p.status(self.root,self.state['project_id'],self.state['run_id'])
        self.assertEqual(status['nodes'][0]['status'],'pending')

    def test_garbage_cluster_is_rejected_by_submit(self):
        self.rejected_role('keywords.cluster-builder',lambda r:r['data'].update(clusters={'filled':True}),'nonempty list')

    def test_measured_frequency_cannot_be_invented(self):
        self.rejected_role('keywords.keyword-discovery',lambda r:r['data']['candidates'][0].update(frequency=9999),'frequency')

    def test_unrelated_http200_cannot_verify_title(self):
        self.rejected_role('operations.production-verify',lambda r:r['data'].update(checks=[{'url':'https://example.com/','field':'status_code','expected':200,'actual':200,'evidence':{'source_id':'src-verification','pointer':'/records/0/status_code'}}]),'actual released changes')

    def test_verification_field_must_match_pointer(self):
        self.rejected_role('operations.production-verify',lambda r:r['data']['checks'][0].update(field='status_code'),'field contradicts')

    def test_source_paths_and_symlinks_stay_in_selected_directory(self):
        self.start('keyword-strategy',register=False)
        outside=write(self.base/'outside.json',self.inputs['documents']['business'])
        path=self.inputs['manifests']['business'];manifest=json.loads(path.read_text())
        for candidate in ['../outside.json',str(outside),'escape.json']:
            with self.subTest(candidate=candidate):
                if candidate=='escape.json':(path.parent/candidate).symlink_to(outside)
                manifest['file']=candidate
                with self.assertRaisesRegex(WorkflowError,'escapes'):p.add_source(self.root,self.state['project_id'],self.state['run_id'],write(path.parent/'bad.json',manifest),CLOCK)
        # Shared guard is also used by legacy technical intake.
        with self.assertRaisesRegex(WorkflowError,'escapes'):selected_input(path,'../outside.json')

    def test_original_file_is_equally_bounded(self):
        self.start('keyword-strategy',register=False)
        path=self.inputs['manifests']['business'];manifest=json.loads(path.read_text())
        write(self.base/'original.json',self.inputs['documents']['business'])
        manifest['original']={'file':'../original.json','sha256':manifest['sha256'],'format':'json','normalization':'Unchanged synthetic test bytes'}
        with self.assertRaisesRegex(WorkflowError,'escapes'):p.add_source(self.root,self.state['project_id'],self.state['run_id'],write(path.parent/'bad.json',manifest),CLOCK)

    def test_readiness_includes_missing_raw_input(self):
        self.start('role:technical.site-crawler',register=False)
        node=p.status(self.root,self.state['project_id'],self.state['run_id'])['nodes'][0]
        self.assertFalse(node['ready']);self.assertIn('pages',node['missing_evidence_kinds'])

    def test_no_live_pages_needed_for_content_sprint_or_launch_plan(self):
        for workflow in ['content-sprint','new-site-launch']:
            with self.subTest(workflow=workflow):
                self.start(workflow,exclude=('pages','pages_post'))
                for node in self.state['nodes']:
                    result=self.result(node['id'])
                    self.assertNotIn('src-pages',result['source_ids'])
                    self.submit(node['id'],result)
                self.assertEqual(p.status(self.root,self.state['project_id'],self.state['run_id'])['status'],'completed')

    def test_live_observation_cannot_be_claimed_in_launch_plan(self):
        self.start('new-site-launch',exclude=('pages','pages_post'));self.advance('schema')
        result=self.result('schema');result['data']['target_pages'][0]['status']='observed'
        with self.assertRaisesRegex(WorkflowError,'proposed'):self.submit('schema',result)

    def test_cwv_requires_matching_measured_metrics(self):
        self.rejected_role('technical.core-web-vitals-analyst',lambda r:r['data']['field_data'][0].update(inp_ms=0),'performance evidence')

    def test_outbound_links_do_not_establish_backlink_profile(self):
        path=self.inputs['manifests']['backlinks'];manifest=json.loads(path.read_text())
        document=copy.deepcopy(self.inputs['documents']['backlinks']);document['records'][0]['kind']='outbound'
        raw=write(path.parent/'backlinks.json',document);manifest['sha256']=digest(raw.read_bytes());write(path,manifest)
        self.rejected_role('links.backlink-auditor',lambda r:None,'Outbound')

    def test_catalog_facts_and_local_nap_cannot_be_invented(self):
        for role,key,field,value in [('ecommerce.product-schema-generator','product_data','price',999),('local.citation-builder','canonical_nap','address','Invented')]:
            with self.subTest(role=role):
                def mutate(r):
                    record=r['data'][key];record=record[0] if isinstance(record,list) else record;record[field]=value
                self.rejected_role(role,mutate,'catalog evidence|local business evidence')

    def test_generated_jsonld_cannot_change_verified_catalog_price(self):
        self.rejected_role('ecommerce.product-schema-generator',lambda r:r['data']['json_ld']['offers'].update(price=999),'JSON-LD contradicts')

    def test_campaign_summary_preserves_linked_drafts_and_tracking(self):
        self.start('link-building-campaign');self.advance('summary')
        result=self.result('summary');result['data']['draft_messages'][0]['status']='sent'
        with self.assertRaisesRegex(WorkflowError,'linked drafts'):self.submit('summary',result)
        result=self.result('summary');result['data']['tracking_plan']['executor_status']='running'
        with self.assertRaisesRegex(WorkflowError,'cannot attest'):self.submit('summary',result)
        self.submit('summary')

    def test_no_findings_or_no_work_is_explicit_instead_of_fabricated(self):
        for role,fields in [('audit.data-compiler',['findings']),('audit.report-builder',['findings']),('strategy.roadmap-planner',['tasks']),('analytics.monthly-report-writer',['work_log'])]:
            with self.subTest(role=role):
                self.start('role:'+role);result=self.result('work')
                for field in fields:result['data'][field]=[]
                if role=='audit.report-builder':result['data']['roadmap']['tasks']=[]
                with self.assertRaisesRegex(WorkflowError,'substantive'):self.submit('work',result)
                result['data']['no_action_reason']='Synthetic reviewed scope: no actionable issues or released work.'
                self.assertEqual(self.submit('work',result)['status'],'completed')

    def test_no_action_reason_cannot_erase_accepted_audit_findings(self):
        self.start('full-seo-audit');self.advance('report');result=self.result('report')
        result['data'].update(findings=[],no_action_reason='No actions asserted incorrectly')
        result['data']['roadmap']['tasks']=[]
        with self.assertRaisesRegex(WorkflowError,'drops accepted'):self.submit('report',result)

    def test_malformed_nested_subject_data_is_a_reviewable_rejection(self):
        self.rejected_role('keywords.cluster-builder',lambda r:r['data']['clusters'][0].update(members=[{'bad':'type'}]),'Malformed subject')

    def test_task_dependencies_must_resolve_without_cycles(self):
        for dependencies in [['unknown'],['synthetic-title-task']]:
            with self.subTest(dependencies=dependencies):
                self.rejected_role('strategy.priority-matrix-builder',lambda r:r['data']['scored_tasks'][0].update(dependencies=dependencies),'dependency')

    def test_prepared_patch_cannot_invent_before_state(self):
        self.rejected_role('audit.fix-generator',lambda r:r['data']['patches'][0].update(before='invented'),'baseline contradicts')

    def test_roi_requires_matching_currency_attribution_and_period(self):
        self.rejected_role('analytics.roi-calculator',lambda r:r['data']['calculations'].update(currency='EUR'),'currency')

    def test_report_finding_requires_matching_evidence(self):
        self.rejected_role('audit.report-builder',lambda r:r['data']['findings'][0]['evidence'].update(value='invented'),'matching source')

    def test_release_does_not_prove_verified_work(self):
        self.rejected_role('analytics.monthly-report-writer',lambda r:r['data']['work_log'][0].update(status='verified'),'accepted verification')

    def test_intraday_release_requires_later_reporting_window(self):
        self.start('role:operations.measurement',register=False)
        path=self.inputs['manifests']['release'];manifest=json.loads(path.read_text())
        release=copy.deepcopy(self.inputs['release']);release['released_at']=release['released_at'].replace('T00:00','T12:00')
        raw=write(path.parent/'release.json',{'release':release});manifest['sha256']=digest(raw.read_bytes());write(path,manifest)
        for m in self.inputs['manifests'].values():p.add_source(self.root,self.state['project_id'],self.state['run_id'],m,CLOCK)
        with self.assertRaisesRegex(WorkflowError,'bracket'):self.submit('work')

    def test_analytics_manifest_signature_and_period_are_enforced(self):
        for modification in [{'analytics_signature':{'property_ref':'other','timezone':'Etc/UTC','definition_version':'organic-session-v1','filters_hash':'synthetic-filter-v1'}},{'period':{'start':'2026-11-01','end':'2026-11-03'}}]:
            with self.subTest(modification=modification):
                self.start('role:analytics.traffic-analyst',register=False)
                path=self.inputs['manifests']['analytics'];manifest=json.loads(path.read_text());manifest.update(modification)
                custom=write(path.parent/'analytics-custom.json',manifest)
                for kind,m in self.inputs['manifests'].items():p.add_source(self.root,self.state['project_id'],self.state['run_id'],custom if kind=='analytics' else m,CLOCK)
                with self.assertRaisesRegex(WorkflowError,'metadata|declared source period'):self.submit('work')
                self.inputs=fixture(self.base/'input',CLOCK)

    def test_quarterly_review_rejects_monthly_windows(self):
        self.start('quarterly-review')
        with self.assertRaisesRegex(WorkflowError,'quarterly scope'):self.submit('traffic')

    def test_legacy_snapshot_is_not_silently_recognized_as_reviewed(self):
        self.start('role:technical.site-crawler')
        con=p.connection(self.root)
        with con:
            record=p.run_record(con,self.state['project_id'],self.state['run_id']);snapshot=record['snapshot'];snapshot.pop('contract_version')
            con.execute('UPDATE process_runs SET snapshot=? WHERE run_id=?',(canonical(snapshot),self.state['run_id']))
        con.close()
        self.assertEqual(p.status(self.root,self.state['project_id'],self.state['run_id'])['status'],'legacy_unreviewed')
        with self.assertRaisesRegex(WorkflowError,'Legacy'):self.submit('work')

    def test_each_workflow_really_submits_and_persists_all_nodes(self):
        for workflow,spec in config('processes').items():
            with self.subTest(workflow=workflow),patch.object(p,'submit',wraps=p.submit) as submit:
                directory=self.base/workflow;status=run_fixture(directory,workflow,CLOCK)
                self.assertEqual(submit.call_count,len(spec['nodes']))
                con=p.connection(directory/'state')
                try:
                    self.assertEqual(con.execute('SELECT count(*) FROM process_products').fetchone()[0],len(spec['nodes']))
                    self.assertEqual(con.execute("SELECT count(*) FROM process_events WHERE event LIKE 'completed:%'").fetchone()[0],len(spec['nodes']))
                finally:con.close()
                self.assertEqual(status['status'],'completed')
                if workflow=='agency-cycle':self.assertEqual(len(spec['nodes']),30)
                if workflow=='quarterly-review':
                    from datetime import date
                    raw=json.loads((directory/'inputs/analytics.json').read_text())['records'][0]
                    self.assertEqual((date.fromisoformat(raw['end'])-date.fromisoformat(raw['start'])).days+1,90)
