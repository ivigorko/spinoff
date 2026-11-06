"""Check inventory, preserved sources, active contracts and procedure coverage."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from jsonschema import Draft202012Validator
from seo_system import processes
from seo_system.core import config


def check():
    problems=[]
    source_map=json.loads((ROOT/'provenance/source-map.json').read_text())
    entries=source_map['entries']
    if len(entries)!=144 or len({e['source'] for e in entries})!=144:problems.append('Expected exactly 144 unique upstream source entries')
    for entry in entries:
        path=ROOT/entry['preserved_path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:problems.append('Preserved source mismatch: '+entry['source'])
        for name in entry['adapted_paths']:
            if not (ROOT/name).is_file():problems.append('Missing adaptation: '+name)
    roles=config('roles');teams=config('teams');workflows=config('processes')
    originals={e['source'] for e in entries if e['source'].startswith('agents/') and not e['source'].startswith('agents/_base/') and not e['source'].endswith('/_lead.md')}
    if len(roles)!=75 or {r['source'] for r in roles.values()}!=originals:problems.append('Specialist role/source coverage mismatch')
    if len(teams)!=12:problems.append('Missing team leaders')
    originals_w={Path(e['source']).stem for e in entries if e['source'].startswith('workflows/')}
    if not originals_w <= workflows.keys() or len(originals_w)!=11:problems.append('Missing original workflow')
    for rid,role in processes.catalog().items():
        required={'purpose','trigger','required_evidence_kinds','optional_evidence_kinds','actions','sections','completion','qa','errors','execution_mode'}
        if not required <= role.keys() or len(role['actions'])<4 or len(role['sections'])<3 or len(role['qa'])<3 or not role['errors']:problems.append('Incomplete subject procedure: '+rid)
        team,name=rid.split('.')
        if not (ROOT/f'procedures/roles/{team}/{name}.md').is_file():problems.append('Missing role procedure: '+rid)
        processes.plan('role:'+rid)
    for team in teams:
        processes.plan('team:'+team)
        if not (ROOT/f'procedures/leads/{team}.md').is_file():problems.append('Missing leader: '+team)
    for wid in workflows:processes.plan(wid)
    for path in (ROOT/'seo_system/schemas').glob('*.json'):Draft202012Validator.check_schema(json.loads(path.read_text()))
    if (ROOT/'LICENSE').read_bytes()!=(ROOT/'vendor/seo-agency-in-a-box/LICENSE').read_bytes():problems.append('MIT notice changed')
    for path in (ROOT/'.agents/skills').rglob('SKILL.md'):
        text=path.read_text()
        if not text.startswith('---\nname:') or 'description:' not in text:problems.append('Invalid skill frontmatter: '+str(path))
    if problems:raise ValueError('\n'.join(problems))
    return {'preserved_sources':len(entries),'specialists':len(roles),'team_leaders':len(teams),'original_workflows':len(originals_w),'additional_cycle':'agency-cycle','skills':len(list((ROOT/'.agents/skills').rglob('SKILL.md'))),'execution':'Codex subject work + structural coordinator; external adapters not implied'}

if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False,indent=2))
