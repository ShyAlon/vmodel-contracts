"""Private read-only execution lineage anchor, separate from contract session ids.

The expected binding must come from authenticated installed control-plane state.
A file cannot create that authority. This reader never initializes a namespace.
"""
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
import hashlib,json,os,re,stat


@dataclass(frozen=True)
class ExecutionAnchor:
    owner_id:str
    task_id:str
    execution_session_id:str
    semantic_session_id:str
    generation:int
    lineage_sha256:str
    installation_id:str

    def __post_init__(self):
        try:canonical=str(UUID(self.owner_id))
        except (ValueError,TypeError,AttributeError) as exc:raise ValueError('canonical anchor owner required') from exc
        if canonical!=self.owner_id:raise ValueError('canonical anchor owner required')
        for value in (self.execution_session_id,self.semantic_session_id):
            if not isinstance(value,str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}',value):
                raise ValueError('canonical anchor session identity required')
        for value in (self.task_id,self.installation_id):
            if not isinstance(value,str) or not 1<=len(value)<=200:raise ValueError('bounded exact anchor binding required')
        if type(self.generation) is not int or self.generation<2:raise ValueError('explicit later execution generation required')
        if self.execution_session_id==self.semantic_session_id:raise ValueError('fresh execution identity required')
        if not isinstance(self.lineage_sha256,str) or not re.fullmatch('[a-f0-9]{64}',self.lineage_sha256):
            raise ValueError('exact immutable lineage digest required')

    def document(self):return {'kind':'installed_execution_generation_anchor','version':1,**self.__dict__}


def _directory(path):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts:raise ValueError('canonical absolute execution root required')
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child
        return fd
    except BaseException:os.close(fd);raise


def _stamp(info):return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns


def read_execution_anchor(root,*,expected):
    """Require exact installed DB binding and contained immutable anchor bytes.

    No missing-file fallback for later generations. Installation permission and
    authenticity of expected are caller obligations, not supplied by this file.
    """
    if not isinstance(expected,ExecutionAnchor):raise ValueError('typed trusted installed binding required')
    root=Path(root)
    if root.parts[-4:]!=('tenants',expected.owner_id,'sessions',expected.execution_session_id):
        raise ValueError('anchor belongs to another execution namespace')
    directory=_directory(root);fd=None
    try:
        fd=os.open('execution-generation.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>16384:raise ValueError('bounded regular execution anchor required')
        with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(16385)
        if len(raw)>16384 or _stamp(os.fstat(fd))!=_stamp(before):raise ValueError('execution anchor changed during read')
        if json.loads(raw)!=expected.document():raise ValueError('execution anchor differs from installed binding')
        if _stamp(os.stat('execution-generation.json',dir_fd=directory,follow_symlinks=False))!=_stamp(before):
            raise ValueError('execution anchor namespace changed')
        current=_directory(root)
        try:
            if _stamp(os.fstat(current))[:2]!=_stamp(os.fstat(directory))[:2]:raise ValueError('execution root namespace changed')
        finally:os.close(current)
        return {'anchor':expected,'document_sha256':hashlib.sha256(raw).hexdigest()}
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)
