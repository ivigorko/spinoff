"""Whole calendar months are accepted only with evidenced continuous observation."""
import calendar
import copy
import json
import tempfile
import unittest
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from examples.process_fixture import fixture,result_for,write
from seo_system import processes as p
from seo_system.core import WorkflowError,digest
from tests.test_processes import CLOCK


class CalendarMonthTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.base=Path(temp.name)
        self.inputs=fixture(self.base/'inputs',CLOCK);self.root=self.base/'state'
        self.prepare()

    def prepare(self,months=((2026,9),(2026,10)),zone='Etc/UTC',values=(100,120)):
        self.manifest=json.loads(self.inputs['manifests']['analytics'].read_text())
        self.scope=copy.deepcopy(self.inputs['metrics'][0]['scope']);self.scope['timezone']=zone
        self.manifest['analytics_signature']['timezone']=zone
        self.records=[];coverage=[];tz=ZoneInfo(zone)
        for (year,month),value in zip(months,values):
            start=date(year,month,1);end=date(year,month,calendar.monthrange(year,month)[1]);next_day=end+timedelta(days=1)
            record={'start':str(start),'end':str(end),'scope':copy.deepcopy(self.scope),'metric':'organic_sessions','unit':'sessions','value':value}
            self.records.append(record)
            coverage.append({k:copy.deepcopy(record[k]) for k in ['start','end','scope','metric','unit']})
            coverage[-1].update(aggregation='sum',coverage_status='confirmed_complete',coverage_basis='Explicit synthetic property lifecycle and continuity evidence; not inferred from daily zeroes',observation_start=datetime.combine(start,datetime.min.time(),tzinfo=tz).isoformat(),observation_end=datetime.combine(next_day,datetime.min.time(),tzinfo=tz).isoformat(),known_gaps=[],daily_values=[{'date':str(start+timedelta(days=i)),'value':value if i==0 else 0} for i in range(end.day)])
        self.document={'records':copy.deepcopy(self.records),'observation_coverage':coverage}
        self.manifest['period']={'start':self.records[0]['start'],'end':self.records[1]['end']}
        periods=[]
        for i,record in enumerate(self.records):periods.append({**copy.deepcopy(record),'evidence':{'source_id':'src-analytics','pointer':f'/records/{i}/value'},'coverage_evidence':{'source_id':'src-analytics','pointer':f'/observation_coverage/{i}'}})
        a,b=values;self.comparison={'mode':'calendar_month','baseline':periods[0],'current':periods[1],'absolute_change':b-a,'percent_change':100*(b-a)/a if a else None}

    def validate(self,comparison=None,sources=True):
        p.validate_comparison(comparison or self.comparison,CLOCK,{'src-analytics':(self.manifest,self.document)} if sources else None)

    def reject(self,message,mutation):
        mutation()
        with self.assertRaisesRegex(WorkflowError,message):self.validate()

    def register(self):
        raw=write(self.base/'inputs/analytics.json',self.document);self.manifest['sha256']=digest(raw.read_bytes())
        manifest=write(self.base/'inputs/analytics.manifest.json',self.manifest)
        state=p.start(self.inputs['profile'],'role:analytics.traffic-analyst',self.root,True,CLOCK)
        p.add_source(self.root,state['project_id'],state['run_id'],manifest,CLOCK)
        result=result_for(self.root,state,state['nodes'][0],self.inputs)
        result['source_ids']=['src-analytics'];result['claims']=[];result['data']['changes']=copy.deepcopy(self.comparison)
        return state,result

    def test_explicit_complete_september_october_is_accepted(self):self.validate()

    def test_leap_and_nonleap_february_complete_months(self):
        for year,expected in [(2024,29),(2025,28)]:
            with self.subTest(year=year):
                self.prepare(((year,1),(year,2)))
                self.assertEqual(len(self.document['observation_coverage'][1]['daily_values']),expected)
                self.validate()

    def test_default_and_explicit_equal_duration_still_reject_unequal_windows(self):
        for mode in [None,'equal_duration']:
            with self.subTest(mode=mode):
                value=copy.deepcopy(self.comparison)
                if mode is None:value.pop('mode')
                else:value['mode']=mode
                with self.assertRaisesRegex(WorkflowError,'not comparable'):self.validate(value)

    def test_arbitrary_equal_length_fragments_are_not_calendar_months(self):
        value=copy.deepcopy(self.comparison);value['current']['end']='2026-10-30';self.document['records'][1]['end']='2026-10-30'
        with self.assertRaisesRegex(WorkflowError,'whole calendar months'):self.validate(value)
        self.prepare();value=copy.deepcopy(self.comparison);value['baseline']['start']='2026-09-02';self.document['records'][0]['start']='2026-09-02'
        with self.assertRaisesRegex(WorkflowError,'whole calendar months'):self.validate(value)

    def test_multi_month_window_is_not_one_calendar_month(self):
        self.comparison['baseline']['start']='2026-08-01'
        self.manifest['period']['start']='2026-08-01';self.document['records'][0]['start']='2026-08-01'
        with self.assertRaisesRegex(WorkflowError,'whole calendar months'):self.validate()

    def test_calendar_mode_cannot_be_validated_without_sources(self):
        with self.assertRaisesRegex(WorkflowError,'registered analytics'):self.validate(sources=False)

    def test_missing_or_nonexistent_coverage_reference_is_rejected(self):
        value=copy.deepcopy(self.comparison);value['baseline'].pop('coverage_evidence')
        with self.assertRaises(WorkflowError):self.validate(value)
        self.comparison['baseline']['coverage_evidence']['pointer']='/not-present'
        with self.assertRaisesRegex(WorkflowError,'pointer'):self.validate()

    def test_daily_rows_alone_do_not_establish_tracking_completeness(self):
        self.reject('unknown tracking',lambda:self.document['observation_coverage'][0].update(coverage_status='unknown'))

    def test_counter_started_mid_month_is_rejected_even_with_all_daily_rows(self):
        self.reject('full observation history',lambda:self.document['observation_coverage'][0].update(observation_start='2026-09-15T08:28:00Z'))

    def test_tracking_end_before_month_end_is_rejected(self):
        self.reject('full observation history',lambda:self.document['observation_coverage'][1].update(observation_end='2026-10-31T12:00:00Z'))

    def test_declared_instrumentation_gap_is_rejected(self):
        self.reject('incomplete or unknown',lambda:self.document['observation_coverage'][0]['known_gaps'].append({'start':'2026-09-20T00:00:00Z','end':'2026-09-20T03:00:00Z','reason':'Tracking outage'}))

    def test_missing_duplicate_or_out_of_month_daily_row_is_rejected(self):
        for operation in ['missing','duplicate','outside']:
            with self.subTest(operation=operation):
                self.prepare();daily=self.document['observation_coverage'][0]['daily_values']
                if operation=='missing':daily.pop()
                elif operation=='duplicate':daily[-1]['date']=daily[0]['date']
                else:daily[-1]['date']='2026-10-01'
                with self.assertRaisesRegex(WorkflowError,'daily coverage'):self.validate()

    def test_unknown_negative_or_nonadditive_daily_values_are_rejected(self):
        for value in [None,-1]:
            with self.subTest(value=value):
                self.prepare();self.document['observation_coverage'][0]['daily_values'][0]['value']=value
                with self.assertRaises(WorkflowError):self.validate()
        self.prepare();self.document['observation_coverage'][0]['aggregation']='mean'
        with self.assertRaises(WorkflowError):self.validate()

    def test_daily_total_must_reconcile(self):
        self.reject('do not reconcile',lambda:self.document['observation_coverage'][0]['daily_values'][0].update(value=99))

    def test_coverage_scope_period_and_signature_must_match(self):
        for field in ['scope','period','signature']:
            with self.subTest(field=field):
                self.prepare()
                if field=='scope':self.document['observation_coverage'][0]['scope']['property_ref']='other'
                elif field=='period':self.document['observation_coverage'][0]['end']='2026-09-29'
                else:self.manifest['analytics_signature']['filters_hash']='other'
                with self.assertRaises(WorkflowError):self.validate()

    def test_coverage_metadata_cannot_claim_observations_after_export(self):
        self.reject('exceeds its evidence',lambda:self.document['observation_coverage'][1].update(observation_end='2026-12-01T00:00:00Z'))

    def test_timezone_month_boundaries_are_exact(self):
        self.prepare(zone='Europe/Moscow')
        self.document['observation_coverage'][0]['observation_start']='2026-08-31T21:00:00Z'
        self.validate()
        self.document['observation_coverage'][0]['observation_start']='2026-08-31T21:00:01Z'
        with self.assertRaisesRegex(WorkflowError,'full observation history'):self.validate()

    def test_open_current_calendar_month_is_rejected(self):
        self.prepare(((2026,10),(2026,11)))
        with self.assertRaisesRegex(WorkflowError,'not closed'):self.validate()

    def test_blank_coverage_basis_is_not_a_confirmation(self):
        self.reject('explicit source-backed basis',lambda:self.document['observation_coverage'][0].update(coverage_basis='   '))

    def test_null_aggregate_cannot_establish_a_complete_calendar_total(self):
        self.comparison['baseline']['value']=None;self.document['records'][0]['value']=None
        self.comparison['absolute_change']=None;self.comparison['percent_change']=None
        with self.assertRaisesRegex(WorkflowError,'known and finite'):self.validate()

    def test_zero_baseline_retains_unknown_percent(self):
        self.prepare(values=(0,120));self.validate()
        self.comparison['percent_change']=100
        with self.assertRaisesRegex(WorkflowError,'calculation'):self.validate()

    def test_coordinator_accepts_complete_calendar_month_product(self):
        state,result=self.register();accepted=p.submit(self.root,state['project_id'],state['run_id'],'work',write(self.base/'result.json',result),CLOCK)
        self.assertEqual(accepted['status'],'completed')
        con=p.connection(self.root)
        try:
            saved,_=p.product(con,self.root,state['project_id'],state['run_id'],'work')
            self.assertEqual(saved['data']['changes']['mode'],'calendar_month')
        finally:con.close()

    def test_coordinator_rejects_incomplete_tracking_without_persisting_product(self):
        self.document['observation_coverage'][0]['observation_start']='2026-09-15T08:28:00Z'
        state,result=self.register()
        with self.assertRaisesRegex(WorkflowError,'full observation history'):p.submit(self.root,state['project_id'],state['run_id'],'work',write(self.base/'result.json',result),CLOCK)
        con=p.connection(self.root)
        try:self.assertEqual(con.execute('SELECT count(*) FROM process_products').fetchone()[0],0)
        finally:con.close()

if __name__=='__main__':unittest.main()
