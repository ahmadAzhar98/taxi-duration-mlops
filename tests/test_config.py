from taxi_mlops.config import settings


def test_train_and_replay_months_do_not_overlap():
    assert not set(settings.train_months) & set(settings.replay_months)


def test_data_dirs_live_under_data_dir():
    assert settings.raw_dir.parent == settings.data_dir
    assert settings.processed_dir.parent == settings.data_dir
