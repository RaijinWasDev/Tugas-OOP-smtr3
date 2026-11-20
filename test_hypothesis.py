from hypothesis import given, settings, strategies as st
from test_workflow import check_choices

@settings(max_examples=1000,deadline=None)
@given(st.lists(st.tuples(st.integers(1,4),st.integers(1,5),st.integers(8,17),st.integers(1,3)),max_size=36))
def test_valid_krs(choices):
    check_choices(choices)
