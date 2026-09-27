"""ID co san trong db/04_seed.sql ma test dua vao.

Tach khoi conftest.py: import tests.conftest se chay lai phan sinh khoa JWT o
dau file, token ky bang khoa moi se khong con khop voi app.
"""

# payments.staff_id co FK toi users, nen token thu thu phai mang id co that.
ADMIN_ID = 1
LIBRARIAN_ID = 2
READER_USER_ID = 4  # docgia01
READER_ID = 1  # ho so ban doc cua docgia01
# Ban doc khong co khoan phat nao trong seed - dung khi can dem/tong chinh xac.
CLEAN_READER_ID = 9
