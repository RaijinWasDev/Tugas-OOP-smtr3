from hypothesis import given, settings, strategies as st
from test_workflow import check_choices

@settings(max_examples=1000,deadline=None)
@given(st.lists(st.tuples(st.integers(1,4),st.integers(1,5),st.integers(8,17),st.integers(1,3)),max_size=36))
def test_valid_krs(choices):
    check_choices(choices)
from hypothesis import given, strategies as st
from test_nilai import nilai
from tugas.minggu_09_nilai.gpa import hitung


@given(st.lists(st.tuples(st.integers(0,4),st.integers(0,4),st.integers(1,4))))
def test_properti_nilai(records):
    rows=[nilai(str(k),b,1+k%4,s) for k,b,s in records]
    _, ipk=hitung(rows,4)
    assert 0<=ipk<=4
    assert hitung(rows+[nilai("baru",4)],4)[1]>=ipk
    assert hitung(list(reversed(rows)),4)[1]==ipk
