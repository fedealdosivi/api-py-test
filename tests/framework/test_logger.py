import logging

from utilities.logger import setup_logging


def test_logs_are_written_to_file(tmp_path):
    log_file = tmp_path / "run.log"
    setup_logging(log_file)

    logging.getLogger("framework.test").info("hello log")

    assert "hello log" in log_file.read_text()
