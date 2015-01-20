# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:expandtab
"""
    pipe2py.modules.piperegex
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Provides methods for modifying fields in a feed using regular
    expressions, a powerful type of pattern matching.
    Think of it as search-and-replace on steroids.
    You can define multiple Regex rules.

    http://pipes.yahoo.com/pipes/docs?doc=operators#Regex
"""

from functools import partial
from itertools import starmap
from twisted.internet.defer import inlineCallbacks, returnValue, maybeDeferred
from . import (
    get_dispatch_funcs, get_async_dispatch_funcs, get_splits, asyncGetSplits)
from pipe2py.lib import utils
from pipe2py.twisted.utils import (
    asyncStarMap, asyncReduce, asyncDispatch, asyncReturn)

func = utils.substitute
convert_func = partial(utils.convert_rules, recompile=True)


# Common functions
def get_groups(rules, item):
    field_groups = utils.group_by(list(rules), 'field').items()
    groups = starmap(lambda f, r: (f, item.get(f) or '', r), field_groups)
    return groups


# Async functions
def asyncGetParsed(splits, funcs, convert=True):
    return asyncDispatch(splits, *funcs) if convert else asyncReturn(splits)


@inlineCallbacks
def asyncGetSubstitutions(field, word, rules):
    asyncSubstitute = partial(maybeDeferred, func)
    replacement = yield asyncReduce(asyncSubstitute, rules, word)
    result = (field, replacement)
    returnValue(result)


@inlineCallbacks
def asyncParseResult(rules, item, _pass):
    if not _pass:
        groups = get_groups(rules, item)
        substitutions = yield asyncStarMap(asyncGetSubstitutions, groups)
        list(starmap(item.set, substitutions))

    returnValue(item)


@inlineCallbacks
def asyncPipeRegex(context=None, _INPUT=None, conf=None, **kwargs):
    """An operator that asynchronously replaces text in items using regexes.
    Each has the general format: "In [field] replace [match] with [replace]".
    Not loopable.

    Parameters
    ----------
    context : pipe2py.Context object
    _INPUT : asyncPipe like object (twisted Deferred iterable of items)
    conf : {
        'RULE': [
            {
                'field': {'value': <'search field'>},
                'match': {'value': <'regex'>},
                'replace': {'value': <'replacement'>},
                'globalmatch': {'value': '1'},
                'singlelinematch': {'value': '2'},
                'multilinematch': {'value': '4'},
                'casematch': {'value': '8'}
            }
        ]
    }

    Returns
    -------
    _OUTPUT : twisted.internet.defer.Deferred generator of items
    """
    pkwargs = utils.combine_dicts(kwargs, {'parse': False, 'ftype': 'pass'})
    splits = yield asyncGetSplits(_INPUT, conf['RULE'], **pkwargs)
    asyncConvert = partial(maybeDeferred, convert_func)
    asyncFuncs = get_async_dispatch_funcs('pass', asyncConvert)
    parsed = yield asyncGetParsed(splits, asyncFuncs, convert=True)
    _OUTPUT = yield asyncStarMap(asyncParseResult, parsed)
    returnValue(iter(_OUTPUT))


# Synchronous functions
def get_substitutions(field, word, rules):
    replacement = reduce(func, rules, word)
    return (field, replacement)


def parse_result(rules, item, _pass):
    if not _pass:
        groups = get_groups(rules, item)
        substitutions = starmap(get_substitutions, groups)
        list(starmap(item.set, substitutions))

    return item


def get_parsed(splits, funcs, convert=True):
    return utils.dispatch(splits, *funcs) if convert else splits


def pipe_regex(context=None, _INPUT=None, conf=None, **kwargs):
    """An operator that replaces text in items using regexes. Each has the
    general format: "In [field] replace [match] with [replace]". Not loopable.

    Parameters
    ----------
    context : pipe2py.Context object
    _INPUT : pipe2py.modules pipe like object (iterable of items)
    conf : {
        'RULE': [
            {
                'field': {'value': <'search field'>},
                'match': {'value': <'regex'>},
                'replace': {'value': <'replacement'>},
                'globalmatch': {'value': '1'},
                'singlelinematch': {'value': '2'},
                'multilinematch': {'value': '4'},
                'casematch': {'value': '8'}
            }
        ]
    }

    Returns
    -------
    _OUTPUT : generator of items
    """
    pkwargs = utils.combine_dicts(kwargs, {'parse': False, 'ftype': 'pass'})
    splits = get_splits(_INPUT, conf['RULE'], **pkwargs)
    parsed = get_parsed(splits, get_dispatch_funcs('pass', convert_func))
    _OUTPUT = starmap(parse_result, parsed)
    return _OUTPUT