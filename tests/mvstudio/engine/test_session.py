from mvstudio.engines.mv.session import Session, get


def test_explicit_sessions_do_not_share_paths_or_caches(tmp_path):
    left = Session(tmp_path / "left-assets", tmp_path / "left-tex", tmp_path / "left-gen")
    right = Session(tmp_path / "right-assets", tmp_path / "right-tex", tmp_path / "right-gen")
    left._tex["key"] = object()

    assert get(left) is left
    assert get(right) is right
    assert left.assets_dir != right.assets_dir
    assert "key" not in right._tex
