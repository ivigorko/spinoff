"""Fictional authenticated-source boundary for tests, never a Nina integration."""
import json
import uuid
from pathlib import Path
from seo_system import governance as g
from seo_system.core import digest


def record(root, profile, phase, kind, clock, actor=None, **fields):
    if isinstance(profile, (str, Path)): profile=json.loads(Path(profile).read_text())
    event_id='fictional-'+uuid.uuid4().hex
    decision={'event_id':event_id,'project_id':profile['project_id'],'profile_hash':g.profile_hash(profile),'phase':phase,'kind':kind,**fields}
    locator='test-only:authenticated-source/'+event_id
    source=g.VerifiedRead(actor or ('nina' if kind=='review' else 'igor'),locator,clock.isoformat(),digest(b'Fictional source, not real user/agent acceptance'),decision,True)
    g.record_from_reader(root,profile,locator,reader=lambda _:source,clock=clock)
    return decision


def launch(root, profile, role, clock, **fields):
    return record(root,profile,g.phase_for(role),'launch',clock,roles=[role],**fields)
