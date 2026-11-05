import py
from py._path.svnurl import InfoSvnCommand
import datetime
import time
from svntestbase import CommonSvnTests

def pytest_funcarg__path1(request):
    repo, repourl, wc = request.getfuncargvalue("repowc1")
    return py.path.svnurl(repourl)

class TestSvnURLCommandPath(CommonSvnTests):
    @py.test.mark.xfail
    def test_load(self, path1):
        super(TestSvnURLCommandPath, self).test_load(path1)

    # the following two work on jython but not in local/svnwc
    def test_listdir(self, path1):
        super(TestSvnURLCommandPath, self).test_listdir(path1)
    def test_visit_ignore(self, path1):
        super(TestSvnURLCommandPath, self).test_visit_ignore(path1)

    def test_svnurl_needs_arg(self, path1):
        py.test.raises(TypeError, "py.path.svnurl()")

    def test_svnurl_does_not_accept_None_either(self, path1):
        py.test.raises(Exception, "py.path.svnurl(None)")

    def test_svnurl_characters_simple(self, path1):
        py.path.svnurl("svn+ssh://hello/world")

    def test_svnurl_characters_at_user(self, path1):
        py.path.svnurl("http://user@host.com/some/dir")

    def test_svnurl_characters_at_path(self, path1):
        py.test.raises(ValueError, 'py.path.svnurl("http://host.com/foo@bar")')

    def test_svnurl_characters_colon_port(self, path1):
        py.path.svnurl("http://host.com:8080/some/dir")

    def test_svnurl_characters_tilde_end(self, path1):
        py.path.svnurl("http://host.com/some/file~")

    @py.test.mark.xfail("sys.platform == 'win32'")
    def test_svnurl_characters_colon_path(self, path1):
        # colons are allowed on win32, because they're part of the drive
        # part of an absolute path... however, they shouldn't be allowed in
        # other parts, I think
        py.test.raises(ValueError, 'py.path.svnurl("http://host.com/foo:bar")')

    def test_export(self, path1, tmpdir):
        tmpdir = tmpdir.join("empty")
        p = path1.export(tmpdir)
        assert p == tmpdir # XXX should return None
        n1 = [x.basename for x in tmpdir.listdir()]
        n2 = [x.basename for x in path1.listdir()]
        n1.sort()
        n2.sort()
        assert n1 == n2
        assert not p.join('.svn').check()
        rev = path1.mkdir("newdir")
        tmpdir.remove()
        assert not tmpdir.check()
        path1.new(rev=1).export(tmpdir)
        for p in tmpdir.listdir():
            assert p.basename in n2

class TestSvnInfoCommand:

    def test_svn_1_2(self):
        line = "   2256      hpk        165 Nov 24 17:55 __init__.py"
        info = InfoSvnCommand(line)
        now = datetime.datetime.now()
        assert info.last_author == 'hpk'
        assert info.created_rev == 2256
        assert info.kind == 'file'
        # we don't check for the year (2006), because that depends
        # on the clock correctly being setup
        assert time.gmtime(info.mtime)[1:6] == (11, 24, 17, 55, 0)
        assert info.size ==  165
        assert info.time == info.mtime * 1000000

    def test_svn_1_3(self):
        line ="    4784 hpk                 2 Jun 01  2004 __init__.py"
        info = InfoSvnCommand(line)
        assert info.last_author == 'hpk'
        assert info.kind == 'file'

    def test_svn_1_3_b(self):
        line ="     74 autoadmi              Oct 06 23:59 plonesolutions.com/"
        info = InfoSvnCommand(line)
        assert info.last_author == 'autoadmi'
        assert info.kind == 'dir'

    def test_svn_1_4_locked_and_spaced_author(self):
        # svn >= 1.4: "%7ld %-8.8s %c %10s %12s %s"; win32 user names may
        # contain spaces
        line = "     12 john doe O          7 Jan 02 03:04 locked file.txt"
        info = InfoSvnCommand(line)
        assert info.created_rev == 12
        assert info.last_author == 'john doe O'
        assert info.size == 7
        assert info._name == 'locked file.txt'
        line = "     12 john doe            0 Jan 02 03:04 empty"
        info = InfoSvnCommand(line)
        assert info.last_author == 'john doe'
        assert info.size == 0
        line = "     12 jd          85058137 Jan 02  2004 big/"
        info = InfoSvnCommand(line)
        assert info.last_author == 'jd'
        assert info.size == 85058137
        assert info.kind == 'dir'

    def test_lspattern_redos(self):
        # CVE-2022-42969: a non-matching line with a long run of spaces
        # used to backtrack cubically (~1s for 500 spaces, minutes for a
        # few thousand).
        line = '1 a' + ' ' * 20000 + '!'
        start = time.time()
        assert InfoSvnCommand.lspattern.match(line) is None
        assert time.time() - start < 1.0

def test_badchars():
    py.test.raises(ValueError, "py.path.svnurl('http://host/tmp/@@@:')")
