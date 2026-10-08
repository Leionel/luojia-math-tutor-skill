import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from fastapi import FastAPI,Depends
from fastapi.testclient import TestClient
from app.config import Settings
from app.auth import get_principal,issue_token,decode_claims,require_role,hash_password
from app.main_deps import get_app_settings,get_repository
from app.memory.repository import Repository
from app.api import routes_auth


@pytest.fixture
def auth(tmp_path):
    settings=Settings(database_url=f"sqlite:///{tmp_path/'auth.db'}",auth_required=True,auth_token_secret='offline-test-secret-01234567890123456789')
    repo=Repository(settings);app=FastAPI();app.include_router(routes_auth.router)
    app.dependency_overrides[get_app_settings]=lambda:settings
    app.dependency_overrides[get_repository]=lambda:repo
    @app.get('/teacher')
    def teacher(principal=Depends(get_principal)):
        require_role(principal,('teacher','admin'),settings);return {'allowed':True}
    return TestClient(app,raise_server_exceptions=False),repo,settings


def register(client,user='alice'):
    response=client.post('/api/auth/register',json={'user_id':user,'password':'synthetic-passphrase-123'})
    assert response.status_code==201
    return response.json()['access_token']


def headers(token):return {'Authorization':'Bearer '+token}


def test_missing_issuer_does_not_leave_account(auth):
    client,repo,settings=auth;settings.auth_token_secret=''
    response=client.post('/api/auth/register',json={'user_id':'alice','password':'synthetic-passphrase-123'})
    assert response.status_code==503 and repo.get_auth_user('alice') is None
    with repo.connect() as conn:assert conn.execute('select count(*) from auth_sessions').fetchone()[0]==0


def test_client_cannot_supply_role_or_session_authority(auth):
    client,repo,_=auth
    response=client.post('/api/auth/register',json={'user_id':'alice','password':'synthetic-passphrase-123','role':'admin','sid':'a'*32})
    assert response.status_code==422 and repo.get_auth_user('alice') is None


def test_registration_session_is_atomic_on_db_failure(auth):
    client,repo,_=auth
    with repo.connect() as conn:conn.execute("create trigger fail_session before insert on auth_sessions begin select raise(abort,'fixture'); end")
    response=client.post('/api/auth/register',json={'user_id':'alice','password':'synthetic-passphrase-123'})
    assert response.status_code==500 and repo.get_auth_user('alice') is None


@pytest.mark.parametrize('ttl',[0,-1,32*86400,True])
def test_invalid_ttl_cannot_create_an_immediately_invalid_login(auth,ttl):
    client,repo,settings=auth;settings.auth_token_ttl_seconds=ttl
    response=client.post('/api/auth/register',json={'user_id':'alice','password':'synthetic-passphrase-123'})
    assert response.status_code==503 and repo.get_auth_user('alice') is None


def test_concurrent_registration_creates_exactly_one_account_and_session(auth):
    client,repo,_=auth
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:client.post('/api/auth/register',json={'user_id':'alice','password':'synthetic-passphrase-123'}).status_code,range(2)))
    assert sorted(results)==[201,409]
    with repo.connect() as conn:
        assert conn.execute("select count(*) from users where id='alice'").fetchone()[0]==1
        assert conn.execute("select count(*) from auth_sessions where user_id='alice'").fetchone()[0]==1


def test_logout_is_idempotent_and_revokes_only_current_session(auth):
    client,repo,settings=auth;one=register(client)
    two=client.post('/api/auth/login',json={'user_id':'alice','password':'synthetic-passphrase-123'}).json()['access_token']
    assert one!=two and decode_claims(one,settings)['v']==2
    for _ in range(2):assert client.post('/api/auth/logout',headers=headers(one)).json()=={'revoked':True,'scope':'current_session'}
    assert client.get('/api/auth/me',headers=headers(one)).status_code==401
    assert client.get('/api/auth/me',headers=headers(two)).json()['access_mode']=='account'
    assert repo.get_auth_user('alice') is not None


@pytest.mark.parametrize('case',['legacy','unknown_sid','expired','tampered','wrong_owner','wrong_expiry'])
def test_invalid_or_unbacked_session_cannot_authorize(auth,case):
    client,repo,settings=auth;token=register(client);claims=decode_claims(token,settings)
    if case=='legacy':token=issue_token('alice',settings)
    if case=='unknown_sid':token=issue_token('alice',settings,sid=uuid4().hex)
    if case=='expired':token=issue_token('alice',settings,sid=claims['sid'],expires_at=int(time.time())-1)
    if case=='tampered':token=token[:-3]+'xxx'
    if case=='wrong_owner':token=issue_token('bob',settings,sid=claims['sid'],expires_at=claims['exp'])
    if case=='wrong_expiry':token=issue_token('alice',settings,sid=claims['sid'],expires_at=claims['exp']+1)
    assert client.get('/api/auth/me',headers=headers(token)).status_code==401


def test_role_is_resolved_from_current_server_configuration(auth):
    client,_,settings=auth
    settings.teacher_user_ids='alice'
    token=register(client)
    assert client.get('/teacher',headers=headers(token)).status_code==200
    settings.teacher_user_ids=''
    assert client.get('/teacher',headers=headers(token)).status_code==403
    assert client.get('/api/auth/me',headers=headers(token)).json()['role']=='student'


def test_demo_me_and_credentialless_logout_are_distinct(auth):
    client,_,settings=auth;settings.auth_required=False
    assert client.get('/api/auth/me').json()['access_mode']=='demo'
    assert client.post('/api/auth/logout').status_code==401


def test_additive_migration_and_synthetic_backup_restore_preserve_history(tmp_path):
    settings=Settings(database_url=f"sqlite:///{tmp_path/'before.db'}")
    repo=Repository(settings);pw,salt=hash_password('synthetic-passphrase-123')
    repo.create_auth_user('alice','Alice',pw,salt)
    session=repo.create_session('alice','calculus')['session_id'];repo.add_message(session,'user','synthetic history')
    with repo.connect() as conn:
        conn.execute('drop table auth_sessions');conn.execute('delete from schema_migrations where version=7')
    backup=tmp_path/'backup.db'
    with sqlite3.connect(repo.db_path) as source,sqlite3.connect(backup) as target:source.backup(target)
    migrated=Repository(settings)
    assert migrated.get_auth_user('alice')['password_hash']==pw and migrated.list_messages(session)[0]['content']=='synthetic history'
    with migrated.connect() as conn:assert conn.execute('pragma integrity_check').fetchone()[0]=='ok'
    restored=tmp_path/'restored.db'
    with sqlite3.connect(backup) as source,sqlite3.connect(restored) as target:source.backup(target)
    recovered=Repository(Settings(database_url=f"sqlite:///{restored}"))
    assert recovered.list_messages(session)[0]['content']=='synthetic history'
    with recovered.connect() as conn:assert conn.execute('pragma integrity_check').fetchone()[0]=='ok'


def test_failed_auth_migration_rolls_back_without_deleting_old_accounts(auth,monkeypatch):
    import app.memory.migrations as migrations
    _,repo,settings=auth
    pw,salt=hash_password('synthetic-passphrase-123');repo.create_auth_user('alice','Alice',pw,salt)
    with repo.connect() as conn:conn.execute('drop table auth_sessions');conn.execute('delete from schema_migrations where version=7')
    original=migrations.MIGRATIONS
    def fail(conn):next(migrate for version, _, migrate in original if version==7)(conn);raise sqlite3.OperationalError('synthetic migration failure')
    monkeypatch.setattr(migrations,'MIGRATIONS',tuple(item if item[0]!=7 else (7,'auth_sessions',fail) for item in original))
    with pytest.raises(sqlite3.OperationalError):Repository(settings)
    with sqlite3.connect(repo.db_path) as conn:
        assert conn.execute("select password_hash from users where id='alice'").fetchone()[0]==pw
        assert conn.execute("select count(*) from sqlite_master where name='auth_sessions'").fetchone()[0]==0
        assert conn.execute('pragma integrity_check').fetchone()[0]=='ok'
