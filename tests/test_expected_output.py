import importlib
from pathlib import Path
import filecmp
import os
import shutil
import sys

import pytest

from freezeyt import freeze


FIXTURES_PATH = Path(__file__).parent / 'fixtures'
DIRS_SAME_FIXTURES = Path(__file__).parent / 'fixtures' / 'dirs_same'

DIRS_SAME_CASES = [p.name for p in DIRS_SAME_FIXTURES.iterdir()]
APP_NAMES = [
    p.name
    for p in FIXTURES_PATH.iterdir()
    if (p / 'app.py').exists()
]

@pytest.mark.parametrize('app_name', APP_NAMES)
def test_output_dict(tmp_path, monkeypatch, app_name):
    app_path = FIXTURES_PATH / app_name
    error_path = app_path / 'error.txt'

    # Add FIXTURES_PATH to sys.path, the list of directories that `import`
    # looks in
    monkeypatch.syspath_prepend(str(app_path))
    sys.modules.pop('app', None)
    try:
        module = importlib.import_module('app')
        app = module.app

        freeze_config = getattr(module, 'freeze_config', {})
        freeze_config['output'] = 'dict'

        if error_path.exists():
            with pytest.raises(ValueError):
                freeze(app, freeze_config)
        else:
            result = freeze(app, freeze_config)
            expected_dict = getattr(module, 'expected_dict', None)

            if expected_dict is None:
                pytest.skip('No expected_dict')

            assert result == expected_dict

    finally:
        sys.modules.pop('app', None)


@pytest.mark.parametrize('app_name', APP_NAMES)
def test_output(tmp_path, monkeypatch, app_name):
    app_path = FIXTURES_PATH / app_name
    error_path = app_path / 'error.txt'

    # Add FIXTURES_PATH to sys.path, the list of directories that `import`
    # looks in
    monkeypatch.syspath_prepend(str(app_path))
    sys.modules.pop('app', None)
    try:
        module = importlib.import_module('app')
        app = module.app

        if getattr(module, 'no_expected_directory', False):
            pytest.skip('No directory with expected output')

        freeze_config = getattr(module, 'freeze_config', {})
        freeze_config['output'] = {'type': 'dir', 'dir': tmp_path}

        expected = app_path / 'test_expected_output'

        if error_path.exists():
            with pytest.raises(ValueError):
                freeze(app, freeze_config)
        else:
            freeze(app, freeze_config)
            expected_dict = getattr(module, 'expected_dict', None)

            if not expected.exists():
                if 'TEST_CREATE_EXPECTED_OUTPUT' in os.environ:
                    shutil.copytree(tmp_path, expected)
                elif expected_dict is not None:
                    pytest.skip('Tested by expected_dict')
                else:
                    raise AssertionError(
                        f'Expected output directory ({expected}) does not exist. '
                        + 'To test files diff - run with '
                        + 'TEST_CREATE_EXPECTED_OUTPUT=1 to create it'
                    )

            assert_dirs_same(tmp_path, expected)

    finally:
        sys.modules.pop('app', None)


def assert_dirs_same(got: Path, expected: Path):
    cmp = filecmp.dircmp(got, expected, ignore=[])
    cmp.report_full_closure()
    assert_cmp_same(cmp)


def assert_cmp_same(cmp):
    print('assert_cmp_same', cmp.left, cmp.right)

    if cmp.left_only:
        raise AssertionError(f'Extra files frozen: {cmp.left_only}')

    if cmp.right_only:
        raise AssertionError(f'Files not frozen: {cmp.right_only}')

    if cmp.common_funny:
        raise AssertionError(f'Funny differences: {cmp.common_funny}')

    # dircmp does "shallow comparison"; it only looks at file size and
    # similar attributes. So, files in "same_files" might actually
    # be different, and we need to check their contents.
    # Files in "diff_files" are checked first, so failures are reported
    # early.
    for filename in list(cmp.diff_files) + list(cmp.same_files):
        path1 = Path(cmp.left) / filename
        path2 = Path(cmp.right) / filename
        content1 = path1.read_bytes()
        content2 = path2.read_bytes()
        assert content1 == content2

    if cmp.diff_files:
        raise AssertionError(f'Files do not have expected content: {cmp.diff_files}')

    for subcmp in cmp.subdirs.values():
        assert_cmp_same(subcmp)


@pytest.mark.parametrize('dir_name', DIRS_SAME_CASES)
def test_assert_dirs_same(dir_name):
    path = DIRS_SAME_FIXTURES / dir_name

    if path.name in ('testdir', 'same'):
        assert_dirs_same(path, DIRS_SAME_FIXTURES / 'testdir')
    else:
        with pytest.raises(AssertionError):
            assert_dirs_same(path, DIRS_SAME_FIXTURES / 'testdir')


def test_files_with_same_signature(tmp_path):
    dir1 = tmp_path / 'dir1'
    dir2 = tmp_path / 'dir2'

    dir1.mkdir()
    dir2.mkdir()

    path1 = dir1 / 'file.txt'
    path2 = dir2 / 'file.txt'

    path1.write_text('A')
    path2.write_text('B')

    with pytest.raises(AssertionError):
        assert_dirs_same(dir1, dir2)
