import json
import pytest
CLAIM='The Cedar demo release supports CSV export.'
CONTEXT='Synthetic software release notes, Cedar version 1. No real product.'
TEXT='Cedar version 1 includes CSV export.'
def vote(relation='SUPPORTS',claim=CLAIM,evidence=TEXT):return {'relation':relation,'claim_quote':claim,'evidence_quote':evidence}
@pytest.fixture
def registry(direct_vm,direct_deploy,direct_alice):
    direct_vm.sender=direct_alice
    return direct_deploy('contracts/evidence_registry.py',CLAIM,CONTEXT,sdk_version='v0.3.0-rc7')
def add(c,id='a',source='release',text=TEXT):c.add_evidence(id,source,text,'synthetic fixture, not a fetched URL')
def review(c,vm,id='a',relation='SUPPORTS',text=TEXT):
    vm.clear_mocks();vm.mock_llm('.*EVIDENCE RELATION.*',json.dumps(vote(relation,evidence=text)))
    c.review(id,json.loads(c.get_state())['revision'])
def snap(c):
    c.snapshot('snapshot',json.loads(c.get_state())['revision']);return json.loads(c.get_snapshot('snapshot'))
@pytest.mark.parametrize('relation,status',[('SUPPORTS','SUPPORTED_BY_SUBMITTED_TEXT'),('CONTRADICTS','CONTRADICTED'),('INSUFFICIENT','INSUFFICIENT')])
def test_relations(registry,direct_vm,relation,status):
    add(registry);review(registry,direct_vm,relation=relation);assert snap(registry)['status']==status

def test_conflict_not_majority_vote(registry,direct_vm):
    for i,relation in enumerate(['SUPPORTS','SUPPORTS','CONTRADICTS','INSUFFICIENT']):
        text=f'Synthetic report number {i}';add(registry,str(i),str(i),text);review(registry,direct_vm,str(i),relation,text)
    r=snap(registry);assert r['status']=='CONFLICT';assert r['contradicting']==['2'];assert r['supporting']==['0','1']

def test_incomplete_and_stale(registry,direct_vm):
    with pytest.raises(Exception,match='Incomplete'):registry.snapshot('empty',0)
    add(registry)
    with pytest.raises(Exception,match='Stale'):registry.review('a',0)
    with pytest.raises(Exception,match='Incomplete'):registry.snapshot('partial',1)
    review(registry,direct_vm)
    with pytest.raises(Exception,match='Stale'):registry.snapshot('stale',0)
    assert registry.get_snapshot('partial')=='{}'

def test_immutable_snapshots_survive_new_evidence(registry,direct_vm):
    add(registry);review(registry,direct_vm);old=snap(registry)
    add(registry,'b','other','Cedar does not support CSV export.')
    assert json.loads(registry.get_snapshot('snapshot'))==old
    with pytest.raises(Exception,match='Immutable snapshot'):registry.snapshot('snapshot',2)
    with pytest.raises(Exception,match='Incomplete'):registry.snapshot('next',2)

def test_duplicates_and_immutability(registry,direct_vm):
    add(registry)
    with pytest.raises(Exception,match='Duplicate excerpt'):add(registry,'b','other','  CEDAR version 1 includes CSV export.  ')
    with pytest.raises(Exception,match='Source already'):add(registry,'b','release','Different content')
    with pytest.raises(Exception,match='Immutable evidence'):add(registry,'a','new','Different content')
    review(registry,direct_vm)
    with pytest.raises(Exception,match='Immutable decision'):registry.review('a',1)
    assert json.loads(registry.get_state())['revision']==1

@pytest.mark.parametrize('bad',['','A B','../x','x'*65])
def test_bad_ids(registry,bad):
    with pytest.raises(Exception,match='Invalid identifier'):add(registry,bad)
    with pytest.raises(Exception,match='Invalid identifier'):add(registry,source=bad)
@pytest.mark.parametrize('bad',['',' '*4,'a'*4001])
def test_bad_excerpt(registry,bad):
    with pytest.raises(Exception,match='Invalid text'):add(registry,text=bad)
@pytest.mark.parametrize('bad',['',' '*4,'a'*501])
def test_bad_citation(registry,bad):
    with pytest.raises(Exception,match='Invalid text'):registry.add_evidence('a','source',TEXT,bad)

def test_capacity(registry):
    for i in range(8):add(registry,str(i),str(i),'Excerpt '+str(i))
    with pytest.raises(Exception,match='capacity'):add(registry,'overflow','overflow','More evidence')
    assert json.loads(registry.get_state())['revision']==8

def test_owner(registry,direct_vm,direct_bob):
    direct_vm.sender=direct_bob
    with pytest.raises(Exception,match='Curator only'):add(registry)
    with pytest.raises(Exception,match='Curator only'):registry.review('a',0)
    with pytest.raises(Exception,match='Curator only'):registry.snapshot('a',0)

def test_unknown(registry):
    with pytest.raises(Exception,match='Unknown evidence'):registry.review('missing',0)
    assert registry.get_evidence('missing')=='{}'
    assert registry.get_decision('missing')=='{}'

@pytest.mark.parametrize('bad',[{},vote('ACCEPT'),vote(claim='invented'),vote(evidence='invented'),dict(vote(),extra=True),vote(evidence='')])
def test_malformed_model_no_decision(registry,direct_vm,bad):
    add(registry);direct_vm.mock_llm('.*EVIDENCE RELATION.*',json.dumps(bad))
    with pytest.raises(Exception):registry.review('a',1)
    assert registry.get_decision('a')=='{}'
    assert json.loads(registry.get_state())['reviewed']==0

def test_independent_validation(registry,direct_vm):
    add(registry);review(registry,direct_vm)
    assert direct_vm.run_validator() is True
    direct_vm.clear_mocks();direct_vm.mock_llm('.*EVIDENCE RELATION.*',json.dumps(vote('CONTRADICTS')))
    assert direct_vm.run_validator() is False
    assert direct_vm.run_validator(leader_error=Exception('failed')) is False

@pytest.mark.parametrize('forged',[{},vote('PAY'),vote(claim='made up'),vote(evidence=''),dict(vote(),extra=True)])
def test_forged_leader(registry,direct_vm,forged):
    add(registry);review(registry,direct_vm)
    assert direct_vm.run_validator(leader_result=forged) is False

def test_valid_alternate_anchors(registry,direct_vm):
    add(registry);review(registry,direct_vm)
    assert direct_vm.run_validator(leader_result=vote(claim='CSV export',evidence='CSV export')) is True
@pytest.mark.parametrize('claim,context',[('',CONTEXT),(CLAIM,''),('a'*1001,CONTEXT),(CLAIM,'a'*1001)])
def test_constructor_bounds(direct_deploy,claim,context):
    with pytest.raises(Exception,match='Invalid text'):direct_deploy('contracts/evidence_registry.py',claim,context,sdk_version='v0.3.0-rc7')
