# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_export.ipynb (unless otherwise specified).

__all__ = ['extract_comments', 'NBProcessor', 'ExportModuleProc', 'rm_comments_proc', 'create_modules', 'nb_export',
           'nbs_export']

# Cell
from .read import *
from .maker import *
from .imports import *

from fastcore.script import *
from fastcore.imports import *
from fastcore.xtras import *

from collections import defaultdict
from pprint import pformat
from inspect import signature,Parameter
import ast,contextlib,copy

# Cell
def extract_comments(ss):
    "Take leading comments from lines of code in `ss`, remove `#`, and split"
    ss = ss.splitlines()
    first_code = first(i for i,o in enumerate(ss) if not o.strip() or re.match('\s*[^#\s]', o))
    return L((s.strip()[1:]).strip().split() for s in ss[:first_code]).filter()

# Cell
@functools.lru_cache(maxsize=None)
def _param_count(f):
    "Number of parameters accepted by function `f`"
    params = list(signature(f).parameters.values())
    # If there's a `*args` then `f` can take as many params as needed
    if first(params, lambda o: o.kind==Parameter.VAR_POSITIONAL): return 99
    return len([o for o in params if o.kind in (Parameter.POSITIONAL_ONLY,Parameter.POSITIONAL_OR_KEYWORD)])

# Cell
class NBProcessor:
    "Process cells and nbdev comments in a notebook"
    def __init__(self, path=None, procs=None, nb=None, debug=False):
        self.nb = read_nb(path) if nb is None else nb
        self.procs,self.debug = L(procs),debug

    def _process_cell(self, cell):
        self.cell = cell
        cell._comments = extract_comments(cell.source)
        for proc in self.procs:
            if callable(proc): proc(cell)
            if cell.cell_type=='code': cell._comments.map(self._process_comment,proc)

    def _process_comment(self, proc, comment):
        cmd,*args = comment
        f = getattr(proc, f'_{cmd}_', None)
        if not f or _param_count(f)-1<len(args): return True
        if self.debug: print(cmd, args, f)
        return f(self, *args)

    def process(self):
        "Process all cells with `process_cell`"
        for i in range_of(self.nb.cells): self._process_cell(self.nb.cells[i])
        self.nb.cells = [c for c in self.nb.cells if c.source is not None]

# Cell
class ExportModuleProc:
    "A processor which exports code to a module"
    def __init__(self): self.modules,self.in_all = defaultdict(L),defaultdict(L)
    def _default_exp_(self, nbp, exp_to): self.default_exp = exp_to
    def _exporti_(self, nbp, exp_to=None): self.modules[ifnone(exp_to, '#')].append(nbp.cell)
    def _export_(self, nbp, exp_to=None):
        self._exporti_(nbp, exp_to)
        self.in_all[ifnone(exp_to, '#')].append(nbp.cell)

# Cell
def rm_comments_proc(cell):
    "A proc that removes comments from each NB cell source"
    cell.source = ''.join(cell.source.splitlines(True)[len(cell._comments):])

# Cell
def create_modules(path, dest, procs=None, debug=False, mod_maker=ModuleMaker):
    "Create module(s) from notebook"
    exp = ExportModuleProc()
    nb = NBProcessor(path, [exp,rm_comments_proc]+L(procs), debug=debug)
    nb.process()
    for mod,cells in exp.modules.items():
        all_cells = exp.in_all[mod]
        name = exp.default_exp if mod=='#' else mod
        mm = mod_maker(dest=dest, name=name, nb_path=path, is_new=mod=='#')
        mm.make(cells, all_cells)

# Cell
def nb_export(nbname, lib_name=None):
    if lib_name is None: lib_name = get_config().lib_name
    create_modules(nbname, lib_name)

# Cell
@call_parse
def nbs_export(
    path:str='.', # path or filename
    recursive:bool=True, # search subfolders
    symlinks:bool=True, # follow symlinks?
    file_glob:str='*.ipynb', # Only include files matching glob
    file_re:str=None, # Only include files matching regex
    folder_re:str=None, # Only enter folders matching regex
    skip_file_glob:str=None, # Skip files matching glob
    skip_file_re:str=None, # Skip files matching regex
    skip_folder_re:str='^[_.]' # Skip folders matching regex
):
    if os.environ.get('IN_TEST',0): return
    if not recursive: skip_folder_re='.'
    files = globtastic(path, symlinks=symlinks, file_glob=file_glob, file_re=file_re,
        folder_re=folder_re, skip_file_glob=skip_file_glob, skip_file_re=skip_file_re, skip_folder_re=skip_folder_re)
    files.map(nb_export)