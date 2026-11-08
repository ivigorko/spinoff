"""Exercise actual coordinator entry points with a fictional trusted reader.

No test result is a real Nina/Igor approval, connection or client deliverable.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from examples.process_fixture import fixture, result_for, write
from seo_system import governance as g, processes as p
from seo_system.core import WorkflowError, canonical, digest, execute
from tests.governance_fixtures import record, launch
from tests.test_processes import CLOCK


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.base=Path(temp.name);self.root=self.base/'state';self.inputs=fixture(self.base/'input',CLOCK)
        self.profile=json.loads(self.inputs['profile'].read_text());self.profile['project_id']='protocol-client'
        write(self.inputs['profile'],self.profile)
        # Fictional client-format protocol data, never real client evidence.
        for f in self.inputs['manifests'].values():
            m=json.loads(f.read_text());m['project_id']=self.profile['project_id'];m['classification']='client_confidential'
            m['original']={'file':m['file'],'sha256':m['sha256'],'format':'json','normalization':'Fictional test data, unchanged; not an actual client or review'}
            write(f,m)
        self.allow('onboard')
        self.state=p.start(self.inputs['profile'],'agency-cycle',self.root,False,CLOCK)
        for m in self.inputs['manifests'].values():p.add_source(self.root,self.profile['project_id'],self.state['run_id'],m,CLOCK)

    def allow(self,phase,**kwargs):
        roles=sorted({n['role'] for n in p.plan('agency-cycle')['workflow']['nodes'] if g.phase_for(n['role'])==phase})
        return record(self.root,self.profile,phase,'launch',CLOCK,roles=roles,**kwargs)

    def submit(self,node,mutate=None):
        spec=next(n for n in self.state['nodes'] if n['id']==node)
        result=result_for(self.root,self.state,spec,self.inputs)
        if mutate:mutate(result)
        return p.submit(self.root,self.profile['project_id'],self.state['run_id'],node,write(self.base/'product.json',result),CLOCK)

    def subjects(self,phase):
        con=p.connection(self.root)
        try:
            out=[]
            for n in self.state['nodes']:
                if g.phase_for(n['role'])==phase:
                    row=con.execute('SELECT * FROM process_products WHERE project_id=? AND run_id=? AND node_id=?',(self.profile['project_id'],self.state['run_id'],n['id'])).fetchone()
                    if row:out.append({'run_id':self.state['run_id'],'artifact_id':row['artifact_id'],'sha256':row['sha256']})
            return out
        finally:con.close()

    def review(self,phase,**overrides):
        fields={'outcome':'accepted','quality_score':4,'blockers':[],'subjects':self.subjects(phase)}
        if phase=='onboard':
            con=p.connection(self.root)
            try:prod,_=p.product(con,self.root,self.profile['project_id'],self.state['run_id'],'onboard')
            finally:con.close()
            fields.update(card_files=prod['data']['card_files'],project_links=prod['data']['handoff'])
        fields.update(overrides)
        return record(self.root,self.profile,phase,'review',CLOCK,**fields)

    def advance(self,target):
        """Traverse real submit/registry gates, inserting fictional external reviews between phases."""
        phase='onboard'
        for node in self.state['nodes']:
            nxt=g.phase_for(node['role'])
            if nxt!=phase:
                self.review(phase)
                if nxt=='execute':record(self.root,self.profile,'strategy','approve',CLOCK,subjects=self.subjects('strategy'))
                self.allow(nxt);phase=nxt
            if node['id']==target:return
            self.submit(node['id'])

    def test_machine_qa_does_not_close_card_or_open_any_selector(self):
        self.submit('onboard');self.allow('research');self.allow('audit');self.allow('strategy')
        for selector in ['role:research.market-researcher','role:technical.site-crawler','role:strategy.seo-strategist','team:research','team:technical','full-seo-audit','keyword-strategy']:
            with self.subTest(selector=selector),self.assertRaisesRegex(WorkflowError,'Nina acceptance'):
                p.start(self.inputs['profile'],selector,self.root,False,CLOCK)
        with self.assertRaisesRegex(WorkflowError,'Nina acceptance'):self.submit('market')
        st=p.status(self.root,self.profile['project_id'],self.state['run_id'])
        self.assertFalse(next(n for n in st['nodes'] if n['id']=='market')['ready'])
        self.assertEqual(next(n for n in st['nodes'] if n['id']=='onboard')['nina_acceptance'],'awaiting_nina_review')

    def test_default_reader_and_json_or_qa_approval_fail_closed(self):
        with self.assertRaisesRegex(WorkflowError,'No authenticated decision reader'):
            g.record_from_reader(self.root,self.profile,'drive:review')
        with self.assertRaisesRegex(WorkflowError,'trusted authenticated'):
            g.record_from_reader(self.root,self.profile,'drive:review',reader=lambda _: {'actor':'nina','authenticated_source':True,'approved':True})
        with self.assertRaisesRegex(WorkflowError,'actual Nina'):
            record(self.root,self.profile,'onboard','review',CLOCK,actor='codex',outcome='accepted',quality_score=5,blockers=[])

    def test_five_distinct_files_handoff_and_exact_binding_required(self):
        with self.assertRaisesRegex(WorkflowError,'five distinct'):
            self.submit('onboard',lambda r:r['data'].update(card_files={'profile':{'locator':'profile.json','sha256':'a'*64}}))
        self.submit('onboard')
        with self.assertRaisesRegex(WorkflowError,'five distinct'):self.review('onboard',card_files={})
        with self.assertRaisesRegex(WorkflowError,'exact submitted'):
            bad={k:{'locator':'other:'+k,'sha256':'b'*64} for k in g.CARD_FILES};self.review('onboard',card_files=bad)
        self.review('onboard');self.allow('research')
        self.submit('market')
        self.assertEqual(next(n for n in p.status(self.root,self.profile['project_id'],self.state['run_id'])['nodes'] if n['id']=='onboard')['nina_acceptance'],'accepted_by_nina')

    def test_launch_and_acceptance_are_separate_and_open_blockers_do_not_pass(self):
        self.submit('onboard')
        for overrides in [{'quality_score':2},{'blockers':['Missing source']},{'outcome':'rejected'}]:
            if overrides.get('outcome')=='rejected':self.review('onboard',**overrides)
            else:
                with self.assertRaisesRegex(WorkflowError,'Score below'):self.review('onboard',**overrides)
        with self.assertRaisesRegex(WorkflowError,'Igor launch'):p.start(self.inputs['profile'],'role:research.market-researcher',self.root,False,CLOCK)
        self.allow('research')
        with self.assertRaisesRegex(WorkflowError,'Nina acceptance'):self.submit('market')
        self.review('onboard');self.submit('market')

    def test_partial_card_cannot_become_phase_acceptance(self):
        self.submit('onboard',lambda r:r.update(coverage={'complete':False,'limitations':['Missing goals']}))
        with self.assertRaisesRegex(WorkflowError,'complete non-synthetic'):self.review('onboard')

    def test_standalone_cannot_skip_phase_internal_order(self):
        self.submit('onboard');self.review('onboard');self.allow('research')
        for rid in ['research.algorithm-monitor','competitor.competitor-site-crawler','keywords.keyword-discovery']:
            with self.subTest(role=rid),self.assertRaisesRegex(WorkflowError,'phase-internal prerequisite'):
                p.start(self.inputs['profile'],'role:'+rid,self.root,False,CLOCK)
        self.submit('market');self.submit('algorithms');self.submit('competitors');self.submit('keyword-discovery')

    def test_research_review_needs_all_substantive_outputs(self):
        self.submit('onboard');self.review('onboard');self.allow('research');self.submit('market')
        with self.assertRaisesRegex(WorkflowError,'substantive outputs'):self.review('research')

    def test_positive_audit_parallelism_after_real_gate_boundary(self):
        self.advance('cwv')  # fictional source reviews onboarding/research, then crawl/indexation
        st=p.status(self.root,self.profile['project_id'],self.state['run_id'])
        for node in ['cwv','schema','mobile','backlinks']:
            self.assertTrue(next(n for n in st['nodes'] if n['id']==node)['ready'],node)
        self.submit('schema');self.submit('cwv')  # independent ready branches may be submitted either way
        st=p.status(self.root,self.profile['project_id'],self.state['run_id'])
        self.assertFalse(next(n for n in st['nodes'] if n['id']=='strategy')['ready'])

    def test_explicit_hold_survives_new_role_run_and_generic_command(self):
        self.submit('onboard');self.review('onboard');self.allow('research')
        hold=record(self.root,self.profile,'research','hold',CLOCK,reason='No research until separate explicit command')
        self.allow('research')
        with self.assertRaisesRegex(WorkflowError,'explicit project hold'):self.submit('market')
        with self.assertRaisesRegex(WorkflowError,'explicit project hold'):p.start(self.inputs['profile'],'role:research.market-researcher',self.root,False,CLOCK)
        self.allow('research',lifts_hold_id=hold['event_id']);self.submit('market')

    def test_old_snapshot_and_source_registration_do_not_open_gate(self):
        self.submit('onboard');self.allow('research')
        with self.assertRaisesRegex(WorkflowError,'Nina acceptance'):self.submit('market')
        con=p.connection(self.root)
        try:
            rec=p.run_record(con,self.profile['project_id'],self.state['run_id']);rec['snapshot']['contract_version']=3
            con.execute('UPDATE process_runs SET snapshot=? WHERE run_id=?',(canonical(rec['snapshot']),self.state['run_id']));con.commit()
        finally:con.close()
        with self.assertRaisesRegex(WorkflowError,'Legacy process'):
            p.add_source(self.root,self.profile['project_id'],self.state['run_id'],self.inputs['manifests']['business'],CLOCK)
        self.assertEqual(p.status(self.root,self.profile['project_id'],self.state['run_id'])['status'],'legacy_unreviewed')

    def test_legacy_execute_and_new_workspace_cannot_bypass(self):
        # Guard precedes format intake: no analysis artifacts can be emitted via legacy importer.
        with self.assertRaisesRegex(WorkflowError,'Igor launch'):
            execute(self.inputs['profile'],self.inputs['manifests']['pages'],self.base/'new-state',clock=CLOCK)
        self.assertFalse((self.base/'new-state').exists())
        self.allow('audit')
        with self.assertRaisesRegex(WorkflowError,'Nina acceptance'):
            execute(self.inputs['profile'],self.inputs['manifests']['pages'],self.root,clock=CLOCK)

    def test_real_host_cannot_use_synthetic_or_profile_policy_opt_out(self):
        profile=copy.deepcopy(self.profile);profile['domains']=profile['allowed_hosts']=['flowers.invalid']
        f=write(self.base/'not-demo.json',profile)
        with self.assertRaisesRegex(WorkflowError,'reserved example hosts'):p.start(f,'role:technical.site-crawler',self.root,True,CLOCK)
        self.allow('research')
        changed=copy.deepcopy(self.profile);changed['profile_version']=2;f=write(self.base/'v2.json',changed)
        with self.assertRaisesRegex(WorkflowError,'Igor launch'):p.start(f,'role:research.market-researcher',self.root,False,CLOCK)

    def test_strategy_approval_is_not_execution_launch(self):
        self.advance('prepare')
        # Remove the fictional execution launch, retain Nina review + Igor strategy approval.
        con=p.connection(self.root)
        try:con.execute("DELETE FROM governance_events WHERE phase='execute' AND kind='launch'");con.commit()
        finally:con.close()
        with self.assertRaisesRegex(WorkflowError,'Igor launch'):self.submit('prepare')
        self.allow('execute');self.submit('prepare')
        with self.assertRaisesRegex(WorkflowError,'Nina material review'):self.submit('release')
        self.review('execute')
        with self.assertRaisesRegex(WorkflowError,'scoped Igor ok'):self.submit('release')
        record(self.root,self.profile,'execute','deployment',CLOCK,subjects=self.subjects('execute'))
        self.submit('release')

    def test_content_route_never_grants_technical_publication(self):
        self.advance('release');self.review('execute',publication_route={'kind':'content','executor':'slava'})
        con=p.connection(self.root)
        try:
            release=copy.deepcopy(self.inputs['release'])
            with self.assertRaisesRegex(WorkflowError,'scoped Igor ok'):g.require_release(self.root,self.profile,release,con)
            release.update(change_kind='content',executor='slava');g.require_release(self.root,self.profile,release,con)
            release['executor']='other'
            with self.assertRaisesRegex(WorkflowError,'Slava'):g.require_release(self.root,self.profile,release,con)
        finally:con.close()

    def test_gate_rejects_tampered_receipt_and_wrong_review_artifact_hash(self):
        self.submit('onboard')
        bad=copy.deepcopy(self.subjects('onboard'));bad[0]['sha256']='0'*64
        with self.assertRaisesRegex(WorkflowError,'checksum'):self.review('onboard',subjects=bad)
        con=p.connection(self.root)
        try:con.execute("UPDATE governance_events SET payload='{}'");con.commit()
        finally:con.close()
        with self.assertRaisesRegex(WorkflowError,'checksum'):self.submit('market')

    def test_full_client_format_cycle_requires_external_reviews_not_just_fixtures(self):
        self.advance('prepare');self.submit('prepare');self.review('execute')
        record(self.root,self.profile,'execute','deployment',CLOCK,subjects=self.subjects('execute'))
        self.submit('release');self.review('execute');self.allow('verify');self.submit('verify')
        with self.assertRaisesRegex(WorkflowError,'Nina second verification'):self.submit('measure')
        self.review('verify');self.submit('measure');self.review('verify')
        self.allow('report');self.submit('report')
        with self.assertRaisesRegex(WorkflowError,'Nina report acceptance'):self.submit('refresh')
        self.review('report');self.allow('strategy');self.submit('refresh');self.submit('next-roadmap')
        self.review('strategy')
        status=p.status(self.root,self.profile['project_id'],self.state['run_id'])
        self.assertEqual(status['status'],'completed')
        self.assertTrue(all(n['nina_acceptance']=='accepted_by_nina' for n in status['nodes']))
        self.assertFalse(status['external_actions_performed'])

    def test_new_hold_stops_existing_adapter_source_and_optional_skip(self):
        record(self.root,self.profile,'onboard','hold',CLOCK,reason='Stop this project stage')
        with self.assertRaisesRegex(WorkflowError,'explicit project hold'):
            p.add_source(self.root,self.profile['project_id'],self.state['run_id'],self.inputs['manifests']['business'],CLOCK)
        with self.assertRaisesRegex(WorkflowError,'explicit project hold'):
            p.mark(self.root,self.profile['project_id'],self.state['run_id'],'onboard','not_applicable','skip',CLOCK)

    def test_reader_truthy_flags_and_cross_project_decisions_are_rejected(self):
        decision={'event_id':'wrong','project_id':'another','profile_hash':g.profile_hash(self.profile),'phase':'research','kind':'launch','roles':['research.market-researcher']}
        for flag,pattern in [('false','trusted authenticated'),(True,'scope mismatch')]:
            read=g.VerifiedRead('igor','test:wrong',CLOCK.isoformat(),'a'*64,decision,flag)
            with self.assertRaisesRegex(WorkflowError,pattern):g.record_from_reader(self.root,self.profile,'test:wrong',reader=lambda _:read,clock=CLOCK)


if __name__=='__main__':unittest.main()
