import pytest

pytest.importorskip('graphviz')

import ibis  # noqa: E402
import ibis.expr.types as ir  # noqa: E402
import ibis.expr.visualize as viz  # noqa: E402

from ibis.expr import rules  # noqa: E402


@pytest.fixture
def t():
    return ibis.table(
        [('a', 'int64'), ('b', 'double'), ('c', 'string')], name='t'
    )


@pytest.mark.parametrize(
    'expr_func',
    [
        lambda t: t.a,
        lambda t: t.a + t.b,
        lambda t: t.a + t.b > 3 ** t.a,
        lambda t: t[(t.a + t.b * 2 * t.b / t.b ** 3 > 4) & (t.b > 5)],
        lambda t: t[(t.a + t.b * 2 * t.b / t.b ** 3 > 4) & (t.b > 5)].group_by(
            'c'
        ).aggregate(
            amean=lambda f: f.a.mean(),
            bsum=lambda f: f.b.sum(),
        )
    ]
)
def test_exprs(t, expr_func):
    expr = expr_func(t)
    graph = viz.to_graph(expr)
    assert str(hash(repr(t.op()))) in graph.source
    assert str(hash(repr(expr.op()))) in graph.source


def test_custom_expr():
    class MyExpr(ir.Expr):
        pass

    class MyExprNode(ir.Node):

        input_type = [
            rules.string(name='foo'),
            rules.number(name='bar'),
        ]

        def output_type(self):
            return MyExpr

    op = MyExprNode(['Hello!', 42.3])
    expr = op.to_expr()
    graph = viz.to_graph(expr)
    assert str(hash(repr(op))) in graph.source


@pytest.mark.parametrize(
    'how',
    [
        'inner',
        'left',
        pytest.mark.xfail('right', raises=KeyError, reason='NYI'),
        'outer',
    ]
)
def test_join(how):
    left = ibis.table([('a', 'int64'), ('b', 'string')])
    right = ibis.table([('b', 'string'), ('c', 'int64')])
    joined = left.join(right, left.b == right.b, how=how)
    result = joined[left.a, right.c]
    graph = viz.to_graph(result)
    assert str(hash(repr(result.op()))) in graph.source
