# pipe2py modules package
# Author: Greg Gaughan

# Note: each module name must match the name used internally by Yahoo, preceded
# by pipe

from functools import partial
from itertools import imap, repeat
from twisted.internet.defer import maybeDeferred, inlineCallbacks, returnValue
from pipe2py.lib import utils
from pipe2py.lib.dotdict import DotDict
from pipe2py.twisted.utils import asyncReturn, asyncNone, asyncBroadcast

__all__ = [
    # Source Modules
    'pipecsv',
    'pipefeedautodiscovery',
    'pipefetch',
    'pipefetchdata',
    'pipefetchpage',
    'pipefetchsitefeed',
    'pipeforever',
    'pipeitembuilder',
    'piperssitembuilder',
    'pipexpathfetchpage',
    'pipeyql',

    # User Input Modules
    'pipenumberinput',
    'pipeprivateinput',
    'pipetextinput',
    'pipeurlinput',
    # 'pipedateinput',
    # 'pipelocationinput',
    # 'pipeprivateinput',

    # Operator Modules
    'pipecount',
    'pipecreaterss',
    'pipefilter',
    'pipeloop',
    'piperegex',
    'piperename',
    'pipereverse',
    'pipesort',
    'pipesplit',
    'pipesubelement',
    'pipetail',
    'pipetruncate',
    'pipeunion',
    'pipeuniq',
    # 'pipewebservice',
    # 'pipelocationextractor',

    # URL Modules
    'pipeurlbuilder',

    # String Modules
    'pipeexchangerate',
    'pipehash',
    'pipestrconcat',
    'pipestrregex',
    'pipestrreplace',
    'pipestringtokenizer',
    'pipestrtransform',
    'pipesubstr',
    # 'pipetermextractor',
    # 'pipetranslate',
    # 'pipeyahooshortcuts',
    # 'pipestrprivate',

    # Date Modules
    'pipedatebuilder',
    'pipedateformat',

    # Location Modules
    # 'pipelocationbuilder',

    # Number Modules
    'pipesimplemath',
    'pipecurrencyformat',

    # Output Modules
    'pipeoutput',
    # 'pipeoutputjson',
    # 'pipeoutputical',
    # 'pipeoutputkml',
    # 'pipeoutputcsv',
]


def _get_broadcast_funcs(pieces, ftype='with', **kwargs):
    test = kwargs.pop('pass_if', None)
    listize = kwargs.pop('listize', True)
    d_index = kwargs.pop('d_index', None)
    get_value = partial(utils.get_value, **kwargs)
    get_pass = partial(utils.get_pass, test=test)
    get_with = partial(utils.get_with, **kwargs)
    parse_conf = partial(utils.parse_conf, parse_func=get_value, **kwargs)

    if listize:
        defs = map(DotDict, utils.listize(pieces))
        piece_defs = map(lambda p: {d_index: p}, defs) if d_index else defs
        get_pieces = lambda i: imap(parse_conf, piece_defs, repeat(i))
    else:
        piece_defs = DotDict(pieces)
        get_pieces = partial(parse_conf, piece_defs)

    return (get_pieces, get_with, get_pass)


def get_async_broadcast_funcs(pieces, ftype='with', **kwargs):
    funcs = _get_broadcast_funcs(pieces, ftype, **kwargs)
    get_pieces, get_with, get_pass = funcs

    f = {
        'with': partial(maybeDeferred, get_with),
        'pass': asyncReturn,
        None: lambda item: asyncNone
    }

    asyncGetPieces = partial(maybeDeferred, get_pieces)
    asyncGetPass = partial(maybeDeferred, get_pass)
    return [asyncGetPieces, f[ftype], asyncGetPass]


def get_broadcast_funcs(pieces, ftype='with', **kwargs):
    funcs = _get_broadcast_funcs(pieces, ftype, **kwargs)
    get_pieces, get_with, get_pass = funcs
    f = {'with': get_with, 'pass': utils.passthrough, None: utils.passnone}
    return [get_pieces, f[ftype], get_pass]


def get_dispatch_funcs(ftype='word', first=utils.passthrough):
    f = {
        'word': utils.get_word,
        'num': utils.get_num,
        'pass': utils.passthrough,
        None: utils.passnone,
    }

    return [first, f[ftype], utils.passthrough]


def get_async_dispatch_funcs(ftype='word', first=asyncReturn):
    f = {
        'word': partial(maybeDeferred, utils.get_word),
        'num': partial(maybeDeferred, utils.get_num),
        'pass': asyncReturn,
        None: lambda item: asyncNone,
    }

    return [first, f[ftype], asyncReturn]


def get_splits(_INPUT, pieces, **kwargs):
    inputs = imap(DotDict, _INPUT) if _INPUT else None
    funcs = get_broadcast_funcs(pieces, **kwargs)
    return utils.broadcast(inputs, *funcs) if inputs else funcs


@inlineCallbacks
def asyncGetSplits(_INPUT, pieces, **kwargs):
    _input = yield _INPUT
    # asyncDict = partial(maybeDeferred, DotDict)
    # inputs = yield asyncCmap(asyncDict, _input)
    inputs = imap(DotDict, _input) if _input else None
    funcs = get_async_broadcast_funcs(pieces, **kwargs)

    if inputs:
        result = yield asyncBroadcast(inputs, *funcs)
    else:
        result = yield asyncReturn(funcs)

    returnValue(result)