# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/03_sync.ipynb (unless otherwise specified).

__all__ = ['nb2dict', 'write_nb', 'absolute_import', 'update_lib']

# Cell
from .imports import *
from .read import *
from .maker import *
from .export import *

from fastcore.script import *
from fastcore.xtras import *

import ast,tempfile,json

# Cell
def nb2dict(d, k=None):
    "Convert parsed notebook to `dict`"
    if k in ('source',): return d.splitlines(keepends=True)
    if isinstance(d, (L,list)): return list(L(d).map(nb2dict))
    if not isinstance(d, dict): return d
    return dict(**{k:nb2dict(v,k) for k,v in d.items() if k[-1] != '_'})

# Cell
def write_nb(nb, path):
    "Write `nb` to `path`"
    if isinstance(nb, (AttrDict,L)): nb = nb2dict(nb)
    with maybe_open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(nb, sort_keys=True, indent=1, ensure_ascii=False))
        f.write("\n")

# Cell
def absolute_import(name, fname, level):
    "Unwarps a relative import in `name` according to `fname`"
    if not level: return name
    mods = fname.split(os.path.sep)
    if not name: return '.'.join(mods)
    return '.'.join(mods[:len(mods)-level+1]) + f".{name}"

# Cell
_re_import = re.compile("from\s+\S+\s+import\s+\S")

# Cell
def _to_absolute(code, lib_name):
    if not _re_import.search(code): return code
    res = update_import(code, ast.parse(code).body, lib_name, absolute_import)
    return ''.join(res) if res else code

def _update_lib(nbname, nb_locs, lib_name=None):
    if lib_name is None: lib_name = get_config().lib_name
    # Too avoid overwriting the comments
    nbp = NBProcessor(nbname, ExportModuleProc())
    nb = nbp.nb
    nbp.process()

    for name,idx,code in nb_locs:
        assert name==nbname
        cell = nb.cells[int(idx)-1]
        lines = cell.source.splitlines(True)
        source = ''.join(cell.source.splitlines(True)[:len(cell._comments)])
        cell.source = source + _to_absolute(code, lib_name)
    write_nb(nb, nbname)

def _get_call(s):
    top,*rest = s.splitlines()
    return *top.split(),'\n'.join(rest)

# Cell
@call_parse
def update_lib(fname:str): # A python file name to convert
    "Propagates any change in the modules matching `fname` to the notebooks that created them"
    if os.environ.get('IN_TEST',0): return
    code_cells = Path(fname).read_text().split("\n# %% ")[1:]
    locs = L(_get_call(s) for s in code_cells if not s.startswith('auto '))
    for nbname,nb_locs in groupby(locs, 0).items(): _update_lib(nbname, nb_locs)