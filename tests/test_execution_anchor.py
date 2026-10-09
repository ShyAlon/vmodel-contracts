import json,os
from dataclasses import replace
import pytest
from vmodel_contracts.execution_anchor import ExecutionAnchor,read_execution_anchor


def setup(tmp_path):
    anchor=ExecutionAnchor('00000000-0000-0000-0000-000000000001','task','execution2','semantic',2,'a'*64,'installation')
    root=tmp_path/'tenants'/anchor.owner_id/'sessions'/anchor.execution_session_id;root.mkdir(parents=True)
    path=root/'execution-generation.json';path.write_text(json.dumps(anchor.document()))
    return anchor,root,path


def test_reads_exact_binding_without_mutation(tmp_path):
    anchor,root,path=setup(tmp_path);before=path.read_bytes()
    assert read_execution_anchor(root,expected=anchor)['anchor']==anchor and path.read_bytes()==before


@pytest.mark.parametrize('key,value',[('generation',1),('generation',True),('execution_session_id','semantic'),('lineage_sha256','bad'),('owner_id','owner')])
def test_invalid_anchor_binding_rejected(tmp_path,key,value):
    anchor,root,path=setup(tmp_path)
    with pytest.raises(ValueError):replace(anchor,**{key:value})


@pytest.mark.parametrize('key,value',[('generation',3),('task_id','foreign'),('semantic_session_id','different'),('installation_id','different')])
def test_file_cannot_change_installed_binding(tmp_path,key,value):
    anchor,root,path=setup(tmp_path);path.write_text(json.dumps(anchor.document()|{key:value}))
    with pytest.raises(ValueError,match='installed binding'):read_execution_anchor(root,expected=anchor)


@pytest.mark.parametrize('unsafe',['missing','file-symlink','directory-symlink','directory-file'])
def test_no_missing_fallback_or_symlink_anchor(tmp_path,unsafe):
    anchor,root,path=setup(tmp_path)
    if unsafe=='missing':path.unlink()
    elif unsafe=='file-symlink':path.rename(tmp_path/'outside');path.symlink_to(tmp_path/'outside')
    elif unsafe=='directory-file':path.unlink();path.mkdir()
    else:root.rename(tmp_path/'outside');root.symlink_to(tmp_path/'outside',target_is_directory=True)
    with pytest.raises((OSError,ValueError)):read_execution_anchor(root,expected=anchor)


def test_root_swap_is_detected(tmp_path,monkeypatch):
    import vmodel_contracts.execution_anchor as module
    anchor,root,path=setup(tmp_path);original=os.open;changed=[]
    def opened(name,flags,*args,**kwargs):
        fd=original(name,flags,*args,**kwargs)
        if name=='execution-generation.json' and not changed:
            root.rename(tmp_path/'old');root.mkdir();changed.append(True)
        return fd
    monkeypatch.setattr(module.os,'open',opened)
    with pytest.raises(ValueError,match='root namespace changed'):read_execution_anchor(root,expected=anchor)
