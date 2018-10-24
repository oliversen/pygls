##########################################################################
# Original work Copyright 2017 Palantir Technologies, Inc.               #
# Original work licensed under the MIT License.                          #
# See ThirdPartyNotices.txt in the project root for license information. #
# All modifications Copyright (c) Open Law Library. All rights reserved. #
##########################################################################
import os
import sys
from threading import Thread

import pytest
from mock import Mock

from pygls import features, uris
from pygls.feature_manager import FeatureManager
from pygls.server import LanguageServer
from pygls.workspace import Workspace, Document
from tests.ls_setup import setup_ls_features


CALL_TIMEOUT = 2

DOC = """document
for
testing
"""
DOC_URI = uris.from_fs_path(__file__)


@pytest.fixture
def client_server():
    """ A fixture to setup a client/server """

    # Client to Server pipe
    csr, csw = os.pipe()
    # Server to client pipe
    scr, scw = os.pipe()

    # Setup server
    server = LanguageServer()
    setup_ls_features(server)

    server_thread = Thread(target=server.start_io, args=(
        os.fdopen(csr, 'rb'), os.fdopen(scw, 'wb')
    ))

    server_thread.daemon = True
    server_thread.start()

    # Add thread id to the server (just for testing)
    server.thread_id = server_thread.ident

    # Setup client
    client = LanguageServer()

    client_thread = Thread(target=client.start_io, args=(
        os.fdopen(scr, 'rb'), os.fdopen(csw, 'wb')))

    client_thread.daemon = True
    client_thread.start()

    yield client, server

    shutdown_response = client.lsp._send_request(
        features.SHUTDOWN).result(timeout=CALL_TIMEOUT)
    assert shutdown_response is None
    client.lsp.notify(features.EXIT)


@pytest.fixture
def doc():
    return Document(DOC_URI, DOC)


@pytest.fixture
def feature_manager():
    """ Return a feature manager """
    return FeatureManager()


@pytest.fixture
def workspace(tmpdir):
    """Return a workspace."""
    return Workspace(uris.from_fs_path(str(tmpdir)), Mock())
