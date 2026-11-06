"""Persistent coordination of Codex-executed procedures; never calls external services."""
from __future__ import annotations
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .core import WorkflowError, canonical, check_project, config, digest, now, read_json, timestamp, validate, MAX_BYTES, parse_json

STATES = {'pending', 'completed', 'partial', 'blocked_input', 'blocked_permission', 'not_applicable'}
DDL = '''
CREATE TABLE IF NOT EXISTS process_runs(project_id TEXT,run_id TEXT,workflow TEXT,profile TEXT,snapshot TEXT,synthetic INTEGER,created_at TEXT, PRIMARY KEY(project_id,run_id));
CREATE TABLE IF NOT EXISTS process_nodes(project_id TEXT,run_id TEXT,node_id TEXT,status TEXT,reason TEXT,artifact_id TEXT, PRIMARY KEY(project_id,run_id,node_id));
CREATE TABLE IF NOT EXISTS process_sources(project_id TEXT,run_id TEXT,source_id TEXT,manifest TEXT,logical_path TEXT, PRIMARY KEY(project_id,run_id,source_id));
CREATE TABLE IF NOT EXISTS process_products(project_id TEXT,run_id TEXT,artifact_id TEXT,node_id TEXT,sha256 TEXT,logical_path TEXT,parents TEXT, PRIMARY KEY(project_id,run_id,artifact_id));
CREATE TABLE IF NOT EXISTS process_events(project_id TEXT,run_id TEXT,node_id TEXT,at TEXT,event TEXT);
'''


def catalog():
    return {**config('roles'), **config('operations')}


def plan(workflow):
    workflows = config('processes')
    roles = catalog()
    if workflow.startswith('role:') and workflow[5:] in roles:
        role = roles[workflow[5:]]
        workflows[workflow] = {'id': workflow, 'source': role['source'], 'purpose': role['purpose'],
            'trigger': role['trigger'], 'prerequisites': role['required_evidence_kinds'],
            'nodes': [{'id': 'work', 'role': role['id'], 'depends_on': [], 'accept_partial_inputs': False, 'optional': False, 'phase': 'selected_task'}],
            'completion': role['completion'], 'errors': role['errors']}
    elif workflow.startswith('team:') and workflow[5:] in config('teams'):
        workflows[workflow] = config('teams')[workflow[5:]]
    if workflow not in workflows:
        raise WorkflowError('Unknown process workflow')
    spec = workflows[workflow]
    seen = set()
    for node in spec['nodes']:
        if node['id'] in seen or node['role'] not in roles or not set(node['depends_on']) <= seen:
            raise WorkflowError('Invalid process DAG or unknown role')
        seen.add(node['id'])
    return {'workflow': spec, 'execution': 'Codex performs analysis; coordinator validates and records supplied work products',
            'roles': {n['role']: roles[n['role']] for n in spec['nodes']}, 'external_actions': 'none'}


def connection(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    con = sqlite3.connect(root / 'process-state.sqlite3', timeout=1)
    con.row_factory = sqlite3.Row
    con.executescript(DDL)
    return con


def run_record(con, project, run):
    row = con.execute('SELECT * FROM process_runs WHERE project_id=? AND run_id=?', (project, run)).fetchone()
    if not row:
        raise WorkflowError('Process not found in project/run scope')
    return {**dict(row), 'profile': json.loads(row['profile']), 'snapshot': json.loads(row['snapshot'])}


def safe_file(root, logical):
    root = Path(root).resolve()
    path = (root / logical).resolve()
    if not path.is_relative_to(root):
        raise WorkflowError('Registry path escaped workspace')
    return path


def write_immutable(root, logical, data):
    path = safe_file(root, logical)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('xb') as handle:
        handle.write(data)
    path.chmod(0o600)
    return path


def event(con, project, run, node, detail, clock=None):
    con.execute('INSERT INTO process_events VALUES(?,?,?,?,?)', (project, run, node, (clock or now()).isoformat(), detail))


def start(profile_path, workflow, root, synthetic=False, clock=None):
    profile = read_json(profile_path)
    check_project(profile)
    frozen = plan(workflow)
    run = 'process-' + uuid.uuid4().hex[:20]
    project = profile['project_id']
    con = connection(root)
    try:
        with con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('INSERT INTO process_runs VALUES(?,?,?,?,?,?,?)',
                        (project, run, workflow, canonical(profile), canonical(frozen), int(synthetic), (clock or now()).isoformat()))
            for node in frozen['workflow']['nodes']:
                con.execute('INSERT INTO process_nodes VALUES(?,?,?,?,?,?)', (project, run, node['id'], 'pending', '', None))
            event(con, project, run, '', 'started:synthetic' if synthetic else 'started:client', clock)
            write_immutable(root, f'projects/{project}/processes/{run}/frozen.json', canonical({'profile': profile, 'plan': frozen, 'synthetic': synthetic}).encode())
    finally:
        con.close()
    return status(root, project, run)


def node_rows(con, project, run):
    return {r['node_id']: dict(r) for r in con.execute('SELECT * FROM process_nodes WHERE project_id=? AND run_id=?', (project, run))}


def status(root, project, run):
    con = connection(root)
    try:
        record = run_record(con, project, run)
        rows = node_rows(con, project, run)
        specs = record['snapshot']['workflow']['nodes']
        output = []
        for node in specs:
            row = rows[node['id']]
            missing = [d for d in node['depends_on'] if rows[d]['status'] not in {'completed', 'not_applicable'} and not (node['accept_partial_inputs'] and rows[d]['status'] == 'partial')]
            output.append({**node, **{k: row[k] for k in ('status', 'reason', 'artifact_id')}, 'ready': row['status'] == 'pending' and not missing, 'waiting_for': missing})
        statuses = {r['status'] for r in rows.values()}
        if statuses <= {'completed', 'not_applicable'}:
            overall = 'completed'
        elif statuses <= {'completed', 'not_applicable', 'partial'}:
            overall = 'partial'
        elif statuses & {'blocked_input', 'blocked_permission'}:
            overall = 'blocked'
        else:
            overall = 'in_progress'
        return {'project_id': project, 'run_id': run, 'workflow': record['workflow'], 'status': overall,
                'synthetic': bool(record['synthetic']), 'nodes': output, 'external_actions_performed': False}
    finally:
        con.close()


def source_bytes(con, root, project, run, source_id):
    row = con.execute('SELECT * FROM process_sources WHERE project_id=? AND run_id=? AND source_id=?', (project, run, source_id)).fetchone()
    if not row:
        raise WorkflowError('Evidence source not found in project/run scope')
    manifest = json.loads(row['manifest'])
    raw = safe_file(root, row['logical_path']).read_bytes()
    if digest(raw) != manifest['sha256']:
        raise WorkflowError('Evidence source checksum changed')
    if 'original' in manifest:
        original = safe_file(root, row['logical_path'] + '.original').read_bytes()
        if digest(original) != manifest['original']['sha256']:
            raise WorkflowError('Original evidence checksum changed')
    return manifest, parse_json(raw)


def source_fresh(manifest, clock=None):
    current = clock or now()
    generated = timestamp(manifest['source_generated_at'])
    collected = timestamp(manifest['collected_at'])
    if generated > collected or collected > current:
        raise WorkflowError('Invalid evidence source chronology')
    days = config('freshness').get(manifest['kind'], 30)
    if (current - generated).total_seconds() > days * 86400:
        raise WorkflowError('Evidence source is stale')


def add_source(root, project, run, manifest_path, clock=None):
    manifest = read_json(manifest_path)
    validate('process-source', manifest)
    con = connection(root)
    try:
        with con:
            con.execute('BEGIN IMMEDIATE')
            record = run_record(con, project, run)
            if manifest['project_id'] != project or manifest['host'] not in record['profile']['allowed_hosts']:
                raise WorkflowError('Evidence project/host scope mismatch')
            market = record['profile']['market']
            for key in ('region', 'language'):
                if manifest['scope'][key] is not None and manifest['scope'][key] != market[key]:
                    raise WorkflowError('Evidence market scope mismatch')
            for key, collection in [('engine', 'engines'), ('device', 'devices')]:
                if manifest['scope'][key] is not None and manifest['scope'][key] not in market[collection]:
                    raise WorkflowError('Evidence market scope mismatch')
            if manifest['purpose'] == 'current' and manifest['kind'] in {'pages', 'indexation', 'performance', 'internal_links'} and manifest['site_revision'] != record['profile']['site_revision']:
                raise WorkflowError('Current evidence site revision mismatch')
            if (manifest['classification'] == 'synthetic') != bool(record['synthetic']):
                raise WorkflowError('Synthetic and client evidence cannot be mixed')
            if not record['synthetic'] and 'original' not in manifest:
                raise WorkflowError('Client evidence requires original bytes and normalization provenance')
            source_fresh(manifest, clock)
            source = (Path(manifest_path).resolve().parent / manifest['file']).resolve()
            if source.stat().st_size > MAX_BYTES:
                raise WorkflowError('Evidence exceeds 20 MiB')
            raw = source.read_bytes()
            if digest(raw) != manifest['sha256']:
                raise WorkflowError('Evidence checksum mismatch')
            parse_json(raw)  # normalized JSON evidence only; retain raw export separately
            original_raw = None
            if 'original' in manifest:
                original = (Path(manifest_path).resolve().parent / manifest['original']['file']).resolve()
                if original.stat().st_size > MAX_BYTES:
                    raise WorkflowError('Original evidence exceeds 20 MiB')
                original_raw = original.read_bytes()
                if digest(original_raw) != manifest['original']['sha256']:
                    raise WorkflowError('Original evidence checksum mismatch')
            if con.execute('SELECT 1 FROM process_sources WHERE project_id=? AND run_id=? AND source_id=?', (project, run, manifest['source_id'])).fetchone():
                raise WorkflowError('Evidence ID already registered; create a new version ID')
            logical = f"projects/{project}/processes/{run}/sources/{manifest['source_id']}.json"
            con.execute('INSERT INTO process_sources VALUES(?,?,?,?,?)', (project, run, manifest['source_id'], canonical(manifest), logical))
            write_immutable(root, logical, raw)
            if original_raw is not None:
                write_immutable(root, logical + '.original', original_raw)
            event(con, project, run, '', 'source:' + manifest['source_id'], clock)
    finally:
        con.close()
    return {'source_id': manifest['source_id'], 'status': 'local_validated', 'external_access_verified': False}


def pointer(document, path):
    if path == '':
        return document
    if not path.startswith('/'):
        raise WorkflowError('Evidence locator must be a JSON pointer')
    try:
        current = document
        for part in path[1:].split('/'):
            if re.search(r'~(?:[^01]|$)', part):
                raise WorkflowError('Invalid JSON pointer escape')
            part = part.replace('~1', '/').replace('~0', '~')
            if isinstance(current, list):
                if not re.fullmatch(r'0|[1-9][0-9]*', part):
                    raise WorkflowError('Invalid JSON pointer array index')
                current = current[int(part)]
            else:
                current = current[part]
        return current
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise WorkflowError('Evidence pointer does not resolve') from exc


def product(con, root, project, run, node):
    row = con.execute('SELECT p.* FROM process_products p JOIN process_nodes n ON p.project_id=n.project_id AND p.run_id=n.run_id AND p.artifact_id=n.artifact_id WHERE p.project_id=? AND p.run_id=? AND n.node_id=?', (project, run, node)).fetchone()
    if not row:
        raise WorkflowError('Required work product not registered')
    raw = safe_file(root, row['logical_path']).read_bytes()
    if digest(raw) != row['sha256']:
        raise WorkflowError('Work product checksum changed')
    return json.loads(raw), row['artifact_id']


def validate_comparison(comparison, clock=None, sources=None):
    validate('comparison', comparison)
    a, b = comparison['baseline'], comparison['current']
    if sources is not None:
        for measurement in (a, b):
            ref = measurement['evidence']
            if ref['source_id'] not in sources or sources[ref['source_id']][0]['kind'] != 'analytics' or pointer(sources[ref['source_id']][1], ref['pointer']) != measurement['value']:
                raise WorkflowError('Measurement value is not supported by analytics evidence')
            manifest, document = sources[ref['source_id']]
            source_record = pointer(document, ref['pointer'].rsplit('/', 1)[0])
            if not isinstance(source_record, dict) or any(source_record.get(key) != measurement[key] for key in ['metric', 'unit', 'start', 'end', 'scope']):
                raise WorkflowError('Measurement definitions/periods contradict source record')
            if measurement['scope']['host'] != manifest['host'] or any(manifest['scope'][key] is not None and measurement['scope'][key] != manifest['scope'][key] for key in ['region', 'engine', 'device']):
                raise WorkflowError('Measurement scope contradicts source manifest')
    if (a['scope'] != b['scope'] or a['metric'] != b['metric'] or a['unit'] != b['unit']):
        raise WorkflowError('Measurement scope/metric/unit mismatch')
    a0, a1 = datetime.fromisoformat(a['start']), datetime.fromisoformat(a['end'])
    b0, b1 = datetime.fromisoformat(b['start']), datetime.fromisoformat(b['end'])
    if a1 < a0 or b1 < b0 or (a1-a0) != (b1-b0) or a1 >= b0:
        raise WorkflowError('Measurement periods overlap or are not comparable')
    if b1.date() >= (clock or now()).date():
        raise WorkflowError('Measurement period is not closed; awaiting_measurement')
    absolute = b['value'] - a['value'] if a['value'] is not None and b['value'] is not None else None
    percent = 100 * absolute / a['value'] if absolute is not None and a['value'] else None
    if comparison['absolute_change'] != absolute or (percent is None and comparison['percent_change'] is not None) or (percent is not None and (comparison['percent_change'] is None or abs(comparison['percent_change']-percent)>1e-8)):
        raise WorkflowError('Measurement calculation contradicts supplied values')


def check_release_scope(release, profile, clock=None):
    from .core import check_url
    validate('release-record', release)
    if timestamp(release['released_at']) > (clock or now()):
        raise WorkflowError('Release cannot be in the future')
    for url in release['urls']:
        check_url(url, profile['allowed_hosts'])


def submit(root, project, run, node_id, result_path, clock=None):
    result = read_json(result_path)
    validate('work-product', result)
    con = connection(root)
    try:
        with con:
            con.execute('BEGIN IMMEDIATE')
            record = run_record(con, project, run)
            specs = {n['id']: n for n in record['snapshot']['workflow']['nodes']}
            if node_id not in specs:
                raise WorkflowError('Unknown process node')
            spec = specs[node_id]
            rows = node_rows(con, project, run)
            if rows[node_id]['status'] != 'pending':
                raise WorkflowError('Node is not pending; accepted products are immutable')
            if result['project_id'] != project or result['run_id'] != run or result['node_id'] != node_id or result['role'] != spec['role']:
                raise WorkflowError('Work product scope/role mismatch')
            role = record['snapshot']['roles'][spec['role']]
            missing = set(role['sections']) - result['data'].keys()
            if missing:
                raise WorkflowError('Required output sections missing: ' + ','.join(sorted(missing)))
            for value in result['data'].values():
                if value is None or value == '' or value == [] or value == {}:
                    raise WorkflowError('Work product sections must be substantive or explicitly unavailable')
            if re.search(r'\bTODO\b|REPLACE_WITH|\{\{', canonical(result['data'])):
                raise WorkflowError('Unfilled template in submitted work product')
            parents = []
            inherited_partial = False
            for dependency in spec['depends_on']:
                dep = rows[dependency]
                if dep['status'] == 'not_applicable':
                    continue
                if dep['status'] != 'completed' and not (spec['accept_partial_inputs'] and dep['status'] == 'partial'):
                    raise WorkflowError('Required dependency has not passed its gate: ' + dependency)
                _, aid = product(con, root, project, run, dependency)
                parents.append(aid)
                inherited_partial |= dep['status'] == 'partial'
            if set(result['input_artifact_ids']) != set(parents):
                raise WorkflowError('Input artifact IDs do not match frozen dependencies')
            if inherited_partial and result['coverage']['complete']:
                raise WorkflowError('Partial dependencies cannot become complete downstream')
            sources = {}
            for sid in result['source_ids']:
                manifest, data = source_bytes(con, root, project, run, sid)
                source_fresh(manifest, clock)
                sources[sid] = (manifest, data)
                if not manifest['coverage']['complete'] and result['coverage']['complete']:
                    raise WorkflowError('Incomplete evidence requires partial coverage')
            required_missing = set(role['required_evidence_kinds']) - {m['kind'] for m, _ in sources.values()}
            if required_missing and result['coverage']['complete']:
                raise WorkflowError('Required evidence kinds missing: ' + ','.join(sorted(required_missing)))
            for claim in result['claims']:
                if claim['classification'] in {'fact', 'inference'} and not claim['evidence']:
                    raise WorkflowError('Factual/inferred claim lacks evidence')
                for ev in claim['evidence']:
                    if ev['source_id'] not in sources:
                        raise WorkflowError('Claim source not declared')
                    if canonical(pointer(sources[ev['source_id']][1], ev['pointer'])) != canonical(ev['value']):
                        raise WorkflowError('Claim contradicts source evidence')
            required_qa = {'scope', 'evidence', 'domain_procedure', 'currentness', 'permissions', 'completeness'}
            checks = {q['id']: q for q in result['qa']}
            if len(checks) != len(result['qa']) or not required_qa <= checks.keys() or any(not checks[q]['passed'] for q in required_qa):
                raise WorkflowError('Critical work-product QA failed or missing')
            # These are evidence records, never authorization to perform an external action.
            if spec['role'] == 'operations.onboard' and result['coverage']['complete']:
                profile = result['data']['profile']
                check_project(profile)
                if canonical(profile) != canonical(record['profile']):
                    raise WorkflowError('Onboarding profile differs from the frozen project profile')
                if not {'business_profile', 'competitors', 'brand_voice', 'resources', 'conversion_definitions', 'source_bindings'} <= profile.keys():
                    raise WorkflowError('Complete onboarding needs the full business/brand/resource/source profile')
            if spec['role'] == 'operations.release-record' and result['coverage']['complete']:
                release = result['data']['release']
                check_release_scope(release, record['profile'], clock)
                if not any(m['kind'] == 'release' and d.get('release') == release for m, d in sources.values() if isinstance(d, dict)):
                    raise WorkflowError('Release record is not supported by release evidence')
                for dependency in spec['depends_on']:
                    if specs[dependency]['role'] == 'audit.fix-generator':
                        prepared = product(con, root, project, run, dependency)[0]['data']
                        patches = prepared['patches']
                        if not isinstance(patches, list) or not patches or any(not isinstance(patch, dict) for patch in patches):
                            raise WorkflowError('Release needs concrete prepared patches')
                        if not set(release['task_ids']) <= {patch.get('task_id') for patch in patches} or not set(release['urls']) <= {patch.get('url') for patch in patches}:
                            raise WorkflowError('Release task/URL scope differs from prepared changes')
                        if not isinstance(prepared['baseline'], dict) or prepared['baseline'].get('revision') != release['baseline_revision']:
                            raise WorkflowError('Release baseline differs from prepared revision')
            if spec['role'] == 'operations.production-verify' and result['coverage']['complete']:
                release_products = [product(con, root, project, run, d)[0] for d in spec['depends_on'] if specs[d]['role'] == 'operations.release-record']
                if release_products:
                    release = release_products[0]['data']['release']
                else:
                    candidates = [d.get('release') for m, d in sources.values() if m['kind'] == 'release' and isinstance(d, dict)]
                    if len(candidates) != 1:
                        raise WorkflowError('Standalone verification needs one explicitly selected release source')
                    release = candidates[0]
                check_release_scope(release, record['profile'], clock)
                verification_sources = [m for m, _ in sources.values() if m['kind'] == 'verification']
                if not verification_sources or any(timestamp(m['source_generated_at']) <= timestamp(release['released_at']) or m['site_revision'] != release['target_revision'] for m in verification_sources):
                    raise WorkflowError('Verification must be new and target the released revision')
                checks_data = result['data']['checks']
                if not isinstance(checks_data, list) or not checks_data or any(c.get('expected') != c.get('actual') for c in checks_data):
                    raise WorkflowError('Production verification failed: expected/actual mismatch')
                for check in checks_data:
                    ref = check.get('evidence', {})
                    if ref.get('source_id') not in sources or sources[ref['source_id']][0]['kind'] != 'verification':
                        raise WorkflowError('Verification check lacks fresh source evidence')
                    document = sources[ref['source_id']][1]
                    actual = pointer(document, ref.get('pointer', ''))
                    parent = pointer(document, ref.get('pointer', '').rsplit('/', 1)[0])
                    if actual != check['actual'] or not isinstance(parent, dict) or parent.get('url') != check.get('url'):
                        raise WorkflowError('Verification check contradicts URL evidence')
                if set(release['urls']) - {c.get('url') for c in checks_data}:
                    raise WorkflowError('Production verification does not cover released URLs')
            if spec['phase'] == 'verify' and spec['role'] != 'operations.production-verify' and result['coverage']['complete']:
                releases = [product(con, root, project, run, n['id'])[0]['data']['release'] for n in specs.values() if n['role'] == 'operations.release-record' and rows[n['id']]['status'] == 'completed']
                if not releases or not any(m['kind'] == 'pages' and m['purpose'] == 'post_release' and m['site_revision'] == releases[-1]['target_revision'] and timestamp(m['source_generated_at']) > timestamp(releases[-1]['released_at']) for m, _ in sources.values()):
                    raise WorkflowError('Post-release audit needs new pages at the released revision')
            if spec['role'] == 'operations.measurement' and result['coverage']['complete']:
                validate_comparison(result['data']['comparison'], clock, sources)
                decision = result['data']['decision']
                if not isinstance(decision, dict) or decision.get('status') not in {'measured', 'inconclusive'}:
                    raise WorkflowError('Measurement decision must be measured or inconclusive')
                if any(result['data']['comparison'][period]['value'] is None for period in ['baseline', 'current']) and decision['status'] != 'inconclusive':
                    raise WorkflowError('Unknown measurement values require inconclusive status')
                ancestors = set(spec['depends_on'])
                queue = list(ancestors)
                while queue:
                    for dependency in specs[queue.pop()]['depends_on']:
                        if dependency not in ancestors:
                            ancestors.add(dependency)
                            queue.append(dependency)
                releases = []
                for ancestor in ancestors:
                    if specs[ancestor]['role'] == 'operations.release-record':
                        releases.append(product(con, root, project, run, ancestor)[0]['data']['release'])
                if not releases:
                    releases = [d.get('release') for m, d in sources.values() if m['kind'] == 'release' and isinstance(d, dict)]
                    if len(releases) != 1:
                        raise WorkflowError('Standalone measurement needs one explicitly selected release source')
                for release in releases:
                    check_release_scope(release, record['profile'], clock)
                    comparison = result['data']['comparison']
                    if datetime.fromisoformat(comparison['current']['start']).date() < timestamp(release['released_at']).date() or datetime.fromisoformat(comparison['baseline']['end']).date() >= timestamp(release['released_at']).date():
                        raise WorkflowError('Measurement baseline/current windows do not bracket the release')
            state = 'completed' if result['coverage']['complete'] else 'partial'
            if state == 'partial' and not result['coverage']['limitations']:
                raise WorkflowError('Partial result requires limitations')
            artifact_id = 'product-' + uuid.uuid4().hex[:20]
            logical = f'projects/{project}/processes/{run}/products/{artifact_id}.json'
            raw = canonical(result).encode()
            con.execute('INSERT INTO process_products VALUES(?,?,?,?,?,?,?)', (project, run, artifact_id, node_id, digest(raw), logical, canonical(parents)))
            con.execute('UPDATE process_nodes SET status=?,artifact_id=?,reason=? WHERE project_id=? AND run_id=? AND node_id=?', (state, artifact_id, '; '.join(result['coverage']['limitations']), project, run, node_id))
            write_immutable(root, logical, raw)
            event(con, project, run, node_id, state + ':' + artifact_id, clock)
    finally:
        con.close()
    return {'node_id': node_id, 'status': state, 'artifact_id': artifact_id, 'external_actions_performed': False}


def mark(root, project, run, node_id, state, reason, clock=None):
    if state not in {'pending', 'blocked_input', 'blocked_permission', 'not_applicable'} or not reason.strip():
        raise WorkflowError('Invalid transition or missing reason')
    con = connection(root)
    try:
        with con:
            con.execute('BEGIN IMMEDIATE')
            record = run_record(con, project, run)
            specs = {n['id']: n for n in record['snapshot']['workflow']['nodes']}
            if node_id not in specs:
                raise WorkflowError('Unknown process node')
            row = node_rows(con, project, run)[node_id]
            if row['status'] in {'completed', 'partial', 'not_applicable'}:
                raise WorkflowError('Accepted result is immutable; create a new process run')
            if state == 'not_applicable' and not specs[node_id]['optional']:
                raise WorkflowError('Required node cannot be skipped')
            con.execute('UPDATE process_nodes SET status=?,reason=? WHERE project_id=? AND run_id=? AND node_id=?', (state, reason, project, run, node_id))
            event(con, project, run, node_id, state + ':' + reason, clock)
    finally:
        con.close()
    return status(root, project, run)


def template(root, project, run, node_id):
    con = connection(root)
    try:
        record = run_record(con, project, run)
        specs = {n['id']: n for n in record['snapshot']['workflow']['nodes']}
        if node_id not in specs:
            raise WorkflowError('Unknown process node')
        node = specs[node_id]
        rows = node_rows(con, project, run)
        role = record['snapshot']['roles'][node['role']]
        return {'schema_version': 1, 'project_id': project, 'run_id': run, 'node_id': node_id, 'role': node['role'],
                'input_artifact_ids': [rows[d]['artifact_id'] for d in node['depends_on'] if rows[d]['artifact_id']],
                'source_ids': [], 'data': {section: None for section in role['sections']}, 'claims': [],
                'coverage': {'complete': False, 'limitations': ['Unfilled template; not a work product']},
                'qa': [{'id': key, 'passed': False, 'note': 'Review required'} for key in ['scope', 'evidence', 'domain_procedure', 'currentness', 'permissions', 'completeness']]}
    finally:
        con.close()
