import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from examples.process_fixture import fixture, result_for, run_fixture, write
from seo_system import processes as p
from seo_system.core import WorkflowError, config, digest

CLOCK=datetime(2026,11,6,18,tzinfo=timezone.utc)

class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.inputs=fixture(self.base/'input',CLOCK)
        self.root=self.base/'state'

    def start(self,workflow='agency-cycle',synthetic=True,register=True):
        if not synthetic:
            from tests.governance_fixtures import launch
            launch(self.root,self.inputs['profile'],p.plan(workflow)['workflow']['nodes'][0]['role'],CLOCK)
        self.state=p.start(self.inputs['profile'],workflow,self.root,synthetic,CLOCK)
        if register:
            for manifest in self.inputs['manifests'].values():p.add_source(self.root,self.state['project_id'],self.state['run_id'],manifest,CLOCK)
        return self.state

    def result(self,node):
        spec=next(n for n in self.state['nodes'] if n['id']==node)
        return result_for(self.root,self.state,spec,self.inputs)

    def submit(self,node,result=None):
        path=write(self.base/'result.json',result or self.result(node))
        return p.submit(self.root,self.state['project_id'],self.state['run_id'],node,path,CLOCK)

    def advance(self,target):
        for node in self.state['nodes']:
            if node['id']==target:return
            self.submit(node['id'])

    def test_all_eleven_original_workflows_and_cycle(self):
        for workflow in config('processes'):
            with self.subTest(workflow=workflow):
                result=run_fixture(self.base/workflow,workflow,CLOCK)
                self.assertEqual(result['status'],'completed')
                self.assertTrue(result['synthetic'])
                self.assertFalse(result['external_actions_performed'])
                self.assertTrue(all(n['status']=='completed' for n in result['nodes']))

    def test_role_and_team_selectors_cover_catalog(self):
        self.assertEqual(len(config('roles')),75)
        self.assertEqual(len(config('teams')),12)
        for rid in p.catalog():self.assertEqual(p.plan('role:'+rid)['workflow']['nodes'][0]['role'],rid)
        for team in config('teams'):self.assertTrue(p.plan('team:'+team)['workflow']['nodes'])

    def test_standalone_verify_and_measure_use_explicit_release_source(self):
        for role in ['operations.production-verify','operations.measurement']:
            with self.subTest(role=role):
                self.start('role:'+role)
                self.submit('work')
                self.assertEqual(p.status(self.root,self.state['project_id'],self.state['run_id'])['status'],'completed')

    def test_standalone_release_evidence_must_stay_in_project_scope(self):
        release=copy.deepcopy(self.inputs['release']);release['urls']=['https://other.example/']
        profile=json.loads(self.inputs['profile'].read_text())
        with self.assertRaisesRegex(WorkflowError,'scope'):p.check_release_scope(release,profile,CLOCK)

    def test_keyword_mapping_reaches_registered_product(self):
        self.start('keyword-strategy');self.advance('roadmap');self.submit('roadmap')
        con=p.connection(self.root)
        try:
            clusters,aid=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'clusters')
            self.assertEqual(clusters['data']['url_mapping'][0]['existing_url'],'https://example.com/')
            content,_=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'content-strategy')
            self.assertIn(aid,content['input_artifact_ids'])
        finally:con.close()

    def test_cycle_carries_release_verify_measurement_and_refresh(self):
        self.start();self.advance('next-roadmap');self.submit('next-roadmap')
        con=p.connection(self.root)
        try:
            measurement,_=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'measure')
            self.assertEqual(measurement['data']['comparison']['percent_change'],20)
            refresh,_=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'refresh')
            self.assertEqual(refresh['data']['next_backlog'][0]['task_id'],'synthetic-follow-up')
            compiled,_=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'compile')
            prepared,_=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'prepare')
            release,_=p.product(con,self.root,self.state['project_id'],self.state['run_id'],'release')
            self.assertEqual(compiled['data']['findings'][0]['finding_id'],prepared['data']['patches'][0]['finding_ids'][0])
            self.assertEqual(release['data']['release']['task_ids'],[prepared['data']['patches'][0]['task_id']])
        finally:con.close()

    def test_dependency_gate_not_bypassed(self):
        self.start('keyword-strategy')
        with self.assertRaisesRegex(WorkflowError,'dependency'):self.submit('clusters')

    def test_missing_required_source_blocks_complete(self):
        self.start('role:technical.site-crawler',register=False)
        business=self.inputs['manifests']['business']
        p.add_source(self.root,self.state['project_id'],self.state['run_id'],business,CLOCK)
        result=self.result('work');result['source_ids']=['src-business']
        with self.assertRaisesRegex(WorkflowError,'evidence kinds'):self.submit('work',result)

    def test_partial_propagates_into_summary(self):
        self.start('full-seo-audit')
        for node in self.state['nodes']:
            result=self.result(node['id'])
            if node['id'] in {'backlinks','compile','recommendations','priority','roadmap','report','summary'}:
                result['coverage']={'complete':False,'limitations':['Synthetic missing backlink completeness']}
            if node['id']=='compile':
                full=copy.deepcopy(result);full['coverage']={'complete':True,'limitations':[]}
                with self.assertRaisesRegex(WorkflowError,'Partial dependencies'):self.submit('compile',full)
            self.submit(node['id'],result)
        self.assertEqual(p.status(self.root,self.state['project_id'],self.state['run_id'])['status'],'partial')

    def test_required_node_cannot_be_skipped(self):
        self.start('keyword-strategy')
        with self.assertRaisesRegex(WorkflowError,'cannot be skipped'):
            p.mark(self.root,self.state['project_id'],self.state['run_id'],'discovery','not_applicable','missing data',CLOCK)

    def test_blocked_branch_does_not_hide_independent_work(self):
        self.start('monthly-reporting')
        result=p.mark(self.root,self.state['project_id'],self.state['run_id'],'rankings','blocked_input','No permitted rank snapshot',CLOCK)
        self.assertTrue(next(n for n in result['nodes'] if n['id']=='traffic')['ready'])
        self.submit('traffic')
        resumed=p.mark(self.root,self.state['project_id'],self.state['run_id'],'rankings','pending','Source now available',CLOCK)
        self.assertTrue(next(n for n in resumed['nodes'] if n['id']=='rankings')['ready'])

    def test_unfilled_template_and_critical_qa_fail(self):
        self.start('role:research.market-researcher')
        with self.assertRaisesRegex(WorkflowError,'substantive'):self.submit('work',p.template(self.root,self.state['project_id'],self.state['run_id'],'work'))
        result=self.result('work');result['qa'][0]['passed']=False
        with self.assertRaisesRegex(WorkflowError,'QA'):self.submit('work',result)

    def test_claim_value_cannot_be_fabricated(self):
        self.start('role:research.market-researcher');result=self.result('work')
        result['claims'][0]['evidence'][0]['value']='invented value'
        with self.assertRaisesRegex(WorkflowError,'contradicts'):self.submit('work',result)

    def test_product_scope_cannot_be_changed(self):
        self.start('role:research.market-researcher');result=self.result('work');result['project_id']='other'
        with self.assertRaisesRegex(WorkflowError,'scope'):self.submit('work',result)

    def test_source_wrong_scope_and_missing_connection_are_not_simulated(self):
        self.start(register=False)
        path=self.inputs['manifests']['business'];manifest=json.loads(path.read_text());manifest['scope']['region']='other-region'
        bad=write(self.base/'bad.json',manifest)
        with self.assertRaisesRegex(WorkflowError,'market scope'):p.add_source(self.root,self.state['project_id'],self.state['run_id'],bad,CLOCK)

    def test_synthetic_evidence_cannot_enter_client_run(self):
        self.start(synthetic=False,register=False)
        with self.assertRaisesRegex(WorkflowError,'cannot be mixed'):
            p.add_source(self.root,self.state['project_id'],self.state['run_id'],self.inputs['manifests']['business'],CLOCK)

    def test_client_format_requires_preserved_original_and_checks_hash(self):
        self.start(synthetic=False,register=False)
        path=self.inputs['manifests']['business'];manifest=json.loads(path.read_text());manifest['classification']='client_confidential'
        adapted=write(self.base/'input'/'client.manifest.json',manifest)
        with self.assertRaisesRegex(WorkflowError,'requires original bytes'):
            p.add_source(self.root,self.state['project_id'],self.state['run_id'],adapted,CLOCK)
        manifest['original']={'file':'business.json','sha256':manifest['sha256'],'format':'json','normalization':'Unchanged source JSON for a test of the client-format protocol; no real client data'}
        write(adapted,manifest)
        p.add_source(self.root,self.state['project_id'],self.state['run_id'],adapted,CLOCK)
        con=p.connection(self.root)
        try:
            logical=con.execute('SELECT logical_path FROM process_sources').fetchone()[0]
            (self.root/(logical+'.original')).write_text('changed')
            with self.assertRaisesRegex(WorkflowError,'Original evidence checksum changed'):
                p.source_bytes(con,self.root,self.state['project_id'],self.state['run_id'],'src-business')
        finally:con.close()

    def test_source_freshness_and_immutability(self):
        self.start(register=False)
        path=self.inputs['manifests']['pages'];manifest=json.loads(path.read_text());manifest['source_generated_at']=(CLOCK-timedelta(days=15)).isoformat()
        bad=write(self.base/'input'/'stale.manifest.json',manifest)
        with self.assertRaisesRegex(WorkflowError,'stale'):p.add_source(self.root,self.state['project_id'],self.state['run_id'],bad,CLOCK)
        p.add_source(self.root,self.state['project_id'],self.state['run_id'],path,CLOCK)
        with self.assertRaisesRegex(WorkflowError,'already registered'):p.add_source(self.root,self.state['project_id'],self.state['run_id'],path,CLOCK)

    def test_accepted_product_and_dependency_hash_are_immutable(self):
        self.start();self.submit('onboard')
        with self.assertRaisesRegex(WorkflowError,'immutable'):self.submit('onboard')
        con=p.connection(self.root)
        try:
            path=con.execute('SELECT logical_path FROM process_products').fetchone()[0]
            (self.root/path).write_text('{}')
        finally:con.close()
        with self.assertRaisesRegex(WorkflowError,'checksum changed'):self.submit('market')

    def test_release_requires_source_evidence(self):
        self.start();self.advance('release');result=self.result('release');result['data']['release']['release_id']='fabricated-id'
        with self.assertRaisesRegex(WorkflowError,'release evidence'):self.submit('release',result)

    def test_verification_rejects_mismatched_and_unsupported_actual(self):
        self.start();self.advance('verify');result=self.result('verify')
        result['data']['checks'][0]['actual']='wrong title'
        with self.assertRaisesRegex(WorkflowError,'verification failed'):self.submit('verify',result)
        result['data']['checks'][0]['expected']='wrong title'
        with self.assertRaisesRegex(WorkflowError,'contradicts URL evidence'):self.submit('verify',result)

    def test_post_migration_audit_cannot_reuse_pre_release_pages(self):
        self.start('site-migration');self.advance('post-audit');result=self.result('post-audit')
        result['source_ids']=['src-pages' if x=='src-pages-post' else x for x in result['source_ids']]
        with self.assertRaisesRegex(WorkflowError,'new pages'):self.submit('post-audit',result)

    def test_measurement_rejects_invented_delta(self):
        self.start();self.advance('measure');result=self.result('measure');result['data']['comparison']['percent_change']=999
        with self.assertRaisesRegex(WorkflowError,'calculation'):self.submit('measure',result)

    def test_measurement_periods_and_zero_denominator(self):
        self.start();comparison=self.result('measure')['data']['comparison']
        changed=copy.deepcopy(comparison);changed['current']['scope']['device']='mobile'
        with self.assertRaisesRegex(WorkflowError,'scope'):p.validate_comparison(changed,CLOCK)
        changed=copy.deepcopy(comparison);changed['current']['start']=changed['baseline']['start'];changed['current']['end']=changed['baseline']['end']
        with self.assertRaisesRegex(WorkflowError,'overlap'):p.validate_comparison(changed,CLOCK)
        changed=copy.deepcopy(comparison);changed['baseline']['value']=0;changed['absolute_change']=120;changed['percent_change']=None
        p.validate_comparison(changed,CLOCK)
        changed['percent_change']=100
        with self.assertRaisesRegex(WorkflowError,'calculation'):p.validate_comparison(changed,CLOCK)

    def test_json_pointer_does_not_accept_negative_indexes(self):
        with self.assertRaises(WorkflowError):p.pointer([1,2],'/-1')
        self.assertEqual(p.pointer({'a/b':{'~key':7}},'/a~1b/~0key'),7)

    def test_duplicate_qa_id_cannot_hide_failure(self):
        self.start('role:research.market-researcher');result=self.result('work')
        failed=copy.deepcopy(result['qa'][0]);failed['passed']=False
        result['qa'].insert(0,failed)
        with self.assertRaisesRegex(WorkflowError,'QA'):self.submit('work',result)

    def test_non_finite_json_is_not_accepted(self):
        from seo_system.core import read_json
        path=self.base/'bad.json';path.write_text('{"value":NaN}')
        with self.assertRaisesRegex(WorkflowError,'Non-finite'):read_json(path)

    def test_open_measurement_period_does_not_pass(self):
        self.start();comparison=self.result('measure')['data']['comparison']
        comparison['current']['end']=CLOCK.date().isoformat()
        comparison['current']['start']=(CLOCK.date()-timedelta(days=27)).isoformat()
        with self.assertRaisesRegex(WorkflowError,'not closed'):p.validate_comparison(comparison,CLOCK)

    def test_observation_before_release_cannot_verify_production(self):
        self.start();self.advance('release')
        release_result=self.result('release')
        release=release_result['data']['release'];release['released_at']=(CLOCK-timedelta(minutes=30)).isoformat()
        raw=write(self.base/'input'/'new-release.json',{'release':release})
        manifest=json.loads(self.inputs['manifests']['release'].read_text())
        manifest.update(source_id='src-new-release',file=raw.name,sha256=digest(raw.read_bytes()))
        path=write(self.base/'input'/'new-release.manifest.json',manifest)
        p.add_source(self.root,self.state['project_id'],self.state['run_id'],path,CLOCK)
        release_result['source_ids']=['src-new-release' if sid=='src-release' else sid for sid in release_result['source_ids']]
        self.submit('release',release_result)
        manifest=json.loads(self.inputs['manifests']['verification'].read_text())
        manifest.update(source_id='src-old-verification',source_generated_at=(CLOCK-timedelta(hours=1)).isoformat())
        path=write(self.base/'input'/'old-verification.manifest.json',manifest)
        p.add_source(self.root,self.state['project_id'],self.state['run_id'],path,CLOCK)
        result=self.result('verify')
        result['source_ids']=['src-old-verification' if sid=='src-verification' else sid for sid in result['source_ids']]
        result['data']['checks'][0]['evidence']['source_id']='src-old-verification'
        with self.assertRaisesRegex(WorkflowError,'Verification must be new'):self.submit('verify',result)

if __name__=='__main__':unittest.main()
