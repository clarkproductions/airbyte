#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#
import json
from unittest import mock

import freezegun
import pytest
import responses
from source_iterable.source import SourceIterable


@responses.activate
@freezegun.freeze_time("2021-01-01")
@pytest.mark.parametrize("catalog", (["email_send"]), indirect=True)
def test_email_stream(catalog):
    record_js = {"createdAt": "2020"}
    resp_body = "\n".join([json.dumps(record_js)])
    responses.add("GET", "https://api.iterable.com/api/export/data.json", body=resp_body)
    TEST_START_DATE = "2020"
    source = SourceIterable()
    records = []
    for record in source.read(
        mock.MagicMock(),
        {"start_date": TEST_START_DATE, "api_key": "api_key"},
        catalog,
        None,
    ):
        records.append(record)
    assert records
