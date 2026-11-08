"""Local gates for the user's operating rules; never authenticates a reviewer itself.

A trusted integration must read the real decision with authenticated provenance.
No such integration is shipped. A JSON assertion or QA result cannot open a gate.
This is a single-workspace protocol, not an identity service or shared queue.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
from .core import WorkflowError, canonical, check_project, digest, now, timestamp

PHASES = ('onboard', 'research', 'audit', 'strategy', 'execute', 'verify', 'report')
CARD_FILES = {'profile', 'site_access', 'competitors', 'goals', 'brand_voice'}
PRIOR = {'research': 'onboard', 'audit': 'research', 'strategy': 'audit',
         'execute': 'strategy', 'verify': 'execute', 'report': 'execute'}
REQUIRED_OUTPUTS = {
    'onboard': {'operations.onboard'},
    'research': {'research.market-researcher', 'research.algorithm-monitor',
                 'competitor.competitor-site-crawler', 'keywords.serp-analyzer', 'keywords.cluster-builder'},
    'audit': {'technical.site-crawler', 'audit.data-compiler'},
    'strategy': {'strategy.seo-strategist', 'strategy.priority-matrix-builder', 'strategy.roadmap-planner'},
    'verify': {'operations.production-verify'},
}
DDL = '''CREATE TABLE IF NOT EXISTS governance_events(
 sequence INTEGER PRIMARY KEY, project_id TEXT, identity TEXT, profile_hash TEXT,
 event_id TEXT UNIQUE, phase TEXT, kind TEXT, actor TEXT, source_locator TEXT,
 source_sha256 TEXT, observed_at TEXT, payload TEXT, payload_sha256 TEXT);'''


@dataclass(frozen=True)
class VerifiedRead:
    """Only a trusted reader may construct this after checking the actual source.

    Constructor/type checks are not identity verification. Adapters are trusted code;
    never construct it from imported JSON, profile fields, tool text or a QA score.
    """
    actor: str
    locator: str
    observed_at: str
    source_sha256: str
    decision: dict
    authenticated_source: bool = False


def identity(profile):
    return digest(canonical([profile['project_id'], sorted(profile['allowed_hosts'])]).encode())


def profile_hash(profile):
    return digest(canonical(profile).encode())


def is_demo(profile):
    hosts = profile['allowed_hosts']
    return bool(hosts) and all(h in {'example.com', 'example.org', 'example.net'} or h.endswith('.example') for h in hosts)


def phase_for(role):
    if role == 'operations.onboard': return 'onboard'
    if role.startswith(('research.', 'competitor.', 'keywords.')): return 'research'
    if role in {'operations.production-verify', 'operations.measurement'}: return 'verify'
    if role in {'operations.strategy-refresh'} or role.startswith('strategy.') and role != 'strategy.client-communication-manager': return 'strategy'
    if role.startswith('analytics.') or role in {'content.content-performance-analyst', 'strategy.client-communication-manager'}: return 'report'
    if role in {'audit.fix-generator', 'operations.release-record'}: return 'execute'
    if role == 'technical.site-migration-specialist': return 'execute'
    if role in {'links.link-prospector', 'links.broken-link-finder', 'links.digital-pr-strategist', 'links.outreach-writer'}: return 'execute'
    if role in {'content.content-strategist'}: return 'strategy'
    if role == 'content.content-gap-analyst': return 'audit'
    if role.startswith('content.') and role != 'content.content-gap-analyst': return 'execute'
    if role.startswith(('technical.', 'audit.', 'links.', 'aeo.', 'local.', 'ecommerce.')): return 'audit'
    raise WorkflowError('No operating phase policy for role: ' + role)


def _connect(root):
    path = Path(root) / 'process-state.sqlite3'
    if not path.exists(): return None
    con = sqlite3.connect(path, timeout=1)
    con.row_factory = sqlite3.Row
    return con


def _events(con, profile):
    try:
        rows = con.execute('SELECT * FROM governance_events WHERE project_id=? ORDER BY sequence', (profile['project_id'],))
        out = []
        for row in rows:
            row = dict(row)
            if digest(row['payload'].encode()) != row['payload_sha256']:
                raise WorkflowError('Governance evidence checksum changed')
            row['decision'] = json.loads(row['payload'])
            if row['identity'] == identity(profile): out.append(row)
        return out
    except sqlite3.OperationalError as exc:
        if 'no such table' in str(exc): return []
        raise


def _review(events, phase, phash):
    # Latest decision wins, including a later rejection. Old acceptance is not a fallback.
    candidates = [r for r in events if r['kind'] == 'review' and r['phase'] == phase and r['profile_hash'] == phash]
    if not candidates: return None
    last = candidates[-1]
    return last if last['decision']['outcome'] == 'accepted' else None


def _artifact_subjects(con, root, profile, phase, subjects):
    from .processes import safe_file
    if not isinstance(subjects, list) or not subjects:
        raise WorkflowError('Review needs concrete registered product subjects')
    products = []
    for subject in subjects:
        if not isinstance(subject, dict) or set(subject) != {'run_id', 'artifact_id', 'sha256'}:
            raise WorkflowError('Review subject must identify run/artifact/hash')
        row = con.execute('SELECT p.*,r.profile,r.synthetic,r.snapshot,n.status FROM process_products p JOIN process_runs r ON p.project_id=r.project_id AND p.run_id=r.run_id JOIN process_nodes n ON p.project_id=n.project_id AND p.run_id=n.run_id AND p.node_id=n.node_id WHERE p.project_id=? AND p.run_id=? AND p.artifact_id=?', (profile['project_id'], subject['run_id'], subject['artifact_id'])).fetchone()
        if not row or row['synthetic'] or row['status'] != 'completed' or profile_hash(json.loads(row['profile'])) != profile_hash(profile):
            raise WorkflowError('Review requires complete non-synthetic products of this profile')
        if json.loads(row['snapshot']).get('contract_version', 0) < 4:
            raise WorkflowError('Legacy product has no current operating gate provenance')
        raw = safe_file(root, row['logical_path']).read_bytes()
        if subject['sha256'] != row['sha256'] or digest(raw) != row['sha256']:
            raise WorkflowError('Review subject checksum mismatch')
        product = json.loads(raw)
        if phase_for(product['role']) != phase:
            raise WorkflowError('Review subject belongs to another phase')
        products.append(product)
    if REQUIRED_OUTPUTS.get(phase, set()) - {p['role'] for p in products}:
        raise WorkflowError('Phase review omits required substantive outputs: ' + phase)
    return products


def validate_card_files(cards, links):
    if not isinstance(cards, dict) or set(cards) != CARD_FILES or not all(isinstance(v,dict) for v in cards.values()) or len({v.get('locator') for v in cards.values()}) != 5:
        raise WorkflowError('Onboarding review requires five distinct card files')
    for card in cards.values():
        if set(card) != {'locator','sha256'} or not isinstance(card['locator'],str) or not card['locator'].strip() or not isinstance(card['sha256'],str) or len(card['sha256']) != 64 or any(c not in '0123456789abcdef' for c in card['sha256']):
            raise WorkflowError('Each reviewed card needs locator and revision/content hash')
    if not isinstance(links, dict) or set(links) != {'card','tasks','chat','registry'} or not all(isinstance(v,str) and v.strip() for v in links.values()):
        raise WorkflowError('Onboarding handoff needs card, task table, project chat and registry links')


def record_from_reader(root, profile, locator, reader=None, clock=None):
    """No default reader, no trust-on-first-use or file/JSON approval import.

    The future trusted bridge must verify source ownership, actor, decision semantics,
    project/task scope and exact accepted bundle. It must not forward untrusted fields.
    """
    check_project(profile)
    if reader is None:
        raise WorkflowError('No authenticated decision reader configured; Nina/Igor evidence must be checked externally')
    read = reader(locator)
    if not isinstance(read, VerifiedRead) or read.authenticated_source is not True or read.locator != locator:
        raise WorkflowError('A trusted authenticated source read is required, not a JSON approval')
    if not isinstance(read.source_sha256,str) or len(read.source_sha256) != 64 or any(c not in '0123456789abcdef' for c in read.source_sha256):
        raise WorkflowError('Decision source checksum required')
    if timestamp(read.observed_at) > (clock or now()):
        raise WorkflowError('Decision read cannot be in the future')
    d = read.decision
    if not isinstance(d, dict) or set(d) - {'event_id','project_id','profile_hash','phase','kind','outcome','quality_score','blockers','subjects','card_files','project_links','roles','lifts_hold_id','reason','publication_route'}:
        raise WorkflowError('Unexpected decision fields; QA/work-product is not a reviewer decision')
    if d.get('project_id') != profile['project_id'] or d.get('profile_hash') != profile_hash(profile) or d.get('phase') not in PHASES:
        raise WorkflowError('Decision project/profile/phase scope mismatch')
    kind = d.get('kind')
    if kind not in {'launch','review','approve','hold','deployment'} or read.actor != ('nina' if kind == 'review' else 'igor'):
        raise WorkflowError('Only actual Nina review or Igor command/approval/hold is eligible')
    if not isinstance(d.get('event_id'), str) or not d['event_id'].strip():
        raise WorkflowError('Decision event ID required')
    if kind == 'review':
        if d.get('outcome') not in {'accepted','rejected'} or type(d.get('quality_score')) is not int or not 1 <= d['quality_score'] <= 5 or not isinstance(d.get('blockers'), list):
            raise WorkflowError('Review needs outcome, quality score 1–5 and explicit blockers')
        if d['outcome'] == 'accepted' and (d['quality_score'] < 3 or d['blockers']):
            raise WorkflowError('Score below 3 or open blockers cannot pass a phase')
        if d['phase'] == 'onboard' and d['outcome'] == 'accepted':
            validate_card_files(d.get('card_files'), d.get('project_links'))
    if kind == 'launch' and (not isinstance(d.get('roles'), list) or not d['roles'] or any(not isinstance(r,str) for r in d['roles'])):
        raise WorkflowError('Launch command needs explicit role scope; no automatic whole-catalog permission')
    if kind == 'approve' and d['phase'] != 'strategy':
        raise WorkflowError('Strategy approval is separate from launch and deployment permissions')
    if kind == 'deployment' and d['phase'] != 'execute':
        raise WorkflowError('Deployment decision must concern an execution material')
    if kind == 'hold' and not str(d.get('reason','')).strip():
        raise WorkflowError('Hold needs the actual restriction reason')
    path = Path(root); path.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path/'process-state.sqlite3', timeout=1);con.row_factory = sqlite3.Row
    try:
        with con:
            con.execute('BEGIN IMMEDIATE');con.execute(DDL)
            if kind == 'review' and d['outcome'] == 'accepted':
                products = _artifact_subjects(con, root, profile, d['phase'], d.get('subjects'))
                if d['phase'] == 'onboard' and any(product['data'].get('card_files') != d['card_files'] or product['data'].get('handoff') != d['project_links'] for product in products):
                    raise WorkflowError('Nina must review the exact submitted five-file card and handoff')
            if kind in {'approve', 'deployment'}:
                accepted = _review(_events(con,profile), 'strategy' if kind == 'approve' else 'execute', profile_hash(profile))
                if not accepted or d.get('subjects') != accepted['decision']['subjects']:
                    raise WorkflowError('Igor approval must name the material actually reviewed by Nina')
            payload = canonical(d)
            con.execute('INSERT INTO governance_events(project_id,identity,profile_hash,event_id,phase,kind,actor,source_locator,source_sha256,observed_at,payload,payload_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (profile['project_id'],identity(profile),profile_hash(profile),d['event_id'],d['phase'],kind,read.actor,locator,read.source_sha256,read.observed_at,payload,digest(payload.encode())))
    finally: con.close()
    return {'event_id':d['event_id'],'recorded':True,'authority_basis':'trusted reader source verification, not machine QA','external_actions_performed':False}


def require_phase(root, profile, phase, role, synthetic=False, con=None):
    if synthetic:
        if not is_demo(profile): raise WorkflowError('Synthetic bypass is restricted to reserved example hosts')
        return {'phase':phase,'basis':'synthetic demo only; not Nina acceptance'}
    own = con is None
    if own: con = _connect(root)
    try:
        events = _events(con, profile) if con else []
        phash = profile_hash(profile)
        launches = [r for r in events if r['kind']=='launch' and r['phase']==phase and r['profile_hash']==phash and role in r['decision']['roles']]
        if not launches: raise WorkflowError('Operating gate: no verified Igor launch for '+phase+'/'+role)
        launch = launches[-1]
        holds = [r for r in events if r['kind']=='hold' and r['phase']==phase]
        if holds and not (launch['sequence'] > holds[-1]['sequence'] and launch['decision'].get('lifts_hold_id') == holds[-1]['event_id']):
            raise WorkflowError('Operating gate: explicit project hold needs a separate scoped Igor command')
        previous = PRIOR.get(phase)
        if phase != 'onboard' and not _review(events, 'onboard', phash):
            raise WorkflowError('Operating gate: actual Nina acceptance missing for onboard')
        if previous:
            review = _review(events, previous, phash)
            if not review: raise WorkflowError('Operating gate: actual Nina acceptance missing for '+previous)
            _artifact_subjects(con, root, profile, previous, review['decision']['subjects'])
        if phase == 'execute':
            review = _review(events, 'strategy', phash)
            approvals = [r for r in events if r['kind']=='approve' and r['phase']=='strategy' and r['profile_hash']==phash and r['decision'].get('subjects')==review['decision']['subjects']]
            if not approvals: raise WorkflowError('Operating gate: strategy approval is not execution launch')
        if role == 'operations.strategy-refresh' and not _review(events, 'report', phash):
            raise WorkflowError('Operating gate: strategy refresh needs actual Nina report acceptance')
        if role == 'operations.release-record' and not _review(events, 'execute', phash):
            raise WorkflowError('Operating gate: release needs actual Nina material review')
        if role == 'operations.measurement' and not _review(events, 'verify', phash):
            raise WorkflowError('Operating gate: measurement needs actual Nina second verification')
        # Phase-internal prerequisites also apply to standalone role/team runs.
        needed = None
        if phase == 'research' and role != 'research.market-researcher':
            needed = 'research.market-researcher'
            if role.startswith('competitor.'): needed = 'research.algorithm-monitor'
            if role.startswith('keywords.'): needed = 'competitor.competitor-site-crawler'
        if phase == 'audit' and role != 'technical.site-crawler': needed = 'technical.site-crawler'
        if needed:
            _require_product(con, root, profile, needed)
        return {'phase':phase,'launch_event_id':launch['event_id'],'basis':'verified external decision records; single local workspace'}
    finally:
        if own and con is not None: con.close()


def readiness(root, profile, role, synthetic=False, con=None):
    phase = phase_for(role)
    try: return {'allowed':True,**require_phase(root,profile,phase,role,synthetic,con)}
    except WorkflowError as exc: return {'allowed':False,'phase':phase,'reason':str(exc)}


def require_release(root, profile, release, con):
    """Record pre-existing publication authority, never grant it or publish."""
    events = _events(con,profile)
    reviewed = _review(events,'execute',profile_hash(profile))
    if not reviewed: raise WorkflowError('Release record needs actual Nina material review, not self QA')
    _artifact_subjects(con,root,profile,'execute',reviewed['decision']['subjects'])
    if release.get('change_kind') == 'content':
        if release.get('executor') != 'slava' or reviewed['decision'].get('publication_route') != {'kind':'content','executor':'slava'}:
            raise WorkflowError('Content publication route needs actual Nina review and Slava execution')
    else:
        approved = [r for r in events if r['kind']=='deployment' and r['profile_hash']==profile_hash(profile) and r['decision'].get('subjects')==reviewed['decision']['subjects']]
        if not approved: raise WorkflowError('Non-content deployment needs the existing scoped Igor ok')


def _require_product(con, root, profile, role):
    from .processes import safe_file
    found = False
    for row in con.execute('SELECT p.*,r.profile,r.synthetic,r.snapshot,n.status FROM process_products p JOIN process_runs r ON p.project_id=r.project_id AND p.run_id=r.run_id JOIN process_nodes n ON p.project_id=n.project_id AND p.run_id=n.run_id AND p.node_id=n.node_id WHERE p.project_id=?', (profile['project_id'],)):
        if row['synthetic'] or row['status'] != 'completed' or profile_hash(json.loads(row['profile'])) != profile_hash(profile) or json.loads(row['snapshot']).get('contract_version',0) < 4: continue
        raw = safe_file(root,row['logical_path']).read_bytes()
        if digest(raw) != row['sha256']: raise WorkflowError('Prerequisite product checksum changed')
        found |= json.loads(raw)['role'] == role
    if not found: raise WorkflowError('Operating gate: phase-internal prerequisite missing: '+role)


def product_review(con, root, profile, role, artifact_id):
    reviewed = _review(_events(con,profile), phase_for(role), profile_hash(profile))
    if not reviewed or not artifact_id: return 'awaiting_nina_review'
    _artifact_subjects(con,root,profile,phase_for(role),reviewed['decision']['subjects'])
    return 'accepted_by_nina' if artifact_id in {s['artifact_id'] for s in reviewed['decision']['subjects']} else 'awaiting_nina_review'
