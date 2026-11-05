#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests the localplaso processor."""

import os
import unittest
import re
import mock
import docker

from dftimewolf.lib import errors
from dftimewolf.lib.processors import localplaso
from dftimewolf.lib.containers import containers
from tests.lib import modules_test_base


class LocalPlasoTest(modules_test_base.ModuleTestBase):
  """Tests for the local Plaso processor."""

  _module: localplaso.LocalPlasoProcessor  # pyrefly: ignore[bad-override-mutable-attribute]

  def setUp(self):
    self._InitModule(localplaso.LocalPlasoProcessor)
    super().setUp()

  # pylint: disable=invalid-name
  @mock.patch('os.path.getsize')
  @mock.patch('os.path.isfile')
  @mock.patch('subprocess.Popen')
  @mock.patch('docker.from_env')
  def testProcessing(self, mock_docker, mock_Popen, mock_exists, mock_getsize):
    """Tests that the correct number of containers is added."""
    mock_popen_object = mock.Mock()
    mock_popen_object.communicate.return_value = (None, None)
    mock_popen_object.wait.return_value = False
    mock_Popen.return_value = mock_popen_object
    mock_exists.return_value = True
    mock_getsize.return_value = 1
    mock_docker().images.get.side_effect = docker.errors.ImageNotFound(
        message="")

    self._module.StoreContainer(
        containers.File(name='test', path='/notexist/test'))
    self._module.SetUp(timezone='', use_docker=False)
    self._ProcessModule()
    mock_Popen.assert_called_once()
    args = mock_Popen.call_args[0][0]  # Get positional arguments of first call
    self.assertEqual(args[10], '/notexist/test')
    plaso_path = args[9]  # Dynamically generated path to the plaso file
    self.assertEqual(
        self._module.GetContainers(containers.File)[0].path,
        plaso_path)

  @mock.patch('os.path.getsize')
  @mock.patch('os.path.isfile')
  @mock.patch('docker.from_env')
  def testProcessingDockerized(self, mock_docker, mock_exists, mock_getsize):
    """Tests that plaso processing is called using Docker."""
    mock_docker.return_value = mock.Mock()
    mock_exists.return_value = True
    mock_getsize.return_value = 1
    self._module.StoreContainer(
        containers.File(name='test', path='/notexist/test'))
    self._module.SetUp(timezone='', use_docker=True)
    self._ProcessModule()
    mock_docker().containers.run.assert_called_once()
    args = mock_docker().containers.run.call_args[1]
    command = args['command']
    # In-container paths must use forward slashes even on Windows hosts.
    self.assertNotIn('\\', command)
    self.assertRegex(command, r'--logfile /data/output/plaso\.log')
    self.assertRegex(
        command, r'--storage-file /data/output/[a-z0-9]+\.plaso /data/input')
    # Get the plaso output file name, which was dynamically generated
    match = re.match(r".*/([a-z0-9]+\.plaso).*", command)
    self.assertIsNotNone(match)
    self.assertRegex(
        self._module.GetContainers(containers.File)[0].path,
        rf".*[\\/]{match.group(1)}$")

  @mock.patch('os.path.getsize')
  @mock.patch('os.path.isfile')
  @mock.patch('docker.from_env')
  def testProcessingDockerizedMissingOutput(
      self, mock_docker, mock_exists, mock_getsize):
    """Tests that missing Plaso output raises a critical error."""
    mock_docker.return_value = mock.Mock()
    # Image exists for SetUp; storage file is missing after the container run.
    mock_exists.side_effect = lambda path: not path.endswith('.plaso')
    mock_getsize.return_value = 0
    self._module.StoreContainer(
        containers.File(name='test', path='/notexist/test'))
    self._module.SetUp(timezone='', use_docker=True)
    with self.assertRaises(errors.DFTimewolfError) as error:
      self._ProcessModule()
    self.assertIn('Plaso storage file was not created', error.exception.message)
    self.assertIn('plaso.log', error.exception.message)

  @mock.patch.dict(
      'os.environ',
      {'PATH': os.pathsep.join(['/fake/path', '/fake/path/2'])})
  @mock.patch('os.path.isfile')
  def testPlasoCheck(self, mock_exists):
    """Tests that a plaso executable is correctly located."""
    mock_exists.return_value = True
    # We're testing module internals here.
    # pylint: disable=protected-access
    self._module._DeterminePlasoPath()
    self.assertEqual(
        self._module._plaso_path,
        os.path.join('/fake/path', 'log2timeline.py'))

  @mock.patch('os.path.isfile')
  @mock.patch('docker.from_env')
  def testPlasoCheckFail(self, mock_docker, mock_exists):
    """Tests that SetUp fails when no plaso executable is found."""
    mock_exists.return_value = False
    mock_docker().images.get.side_effect = docker.errors.ImageNotFound(
        message="")
    with self.assertRaises(errors.DFTimewolfError) as error:
      self._module.SetUp(timezone='', use_docker=False)
    self.assertEqual((
        'Could not run log2timeline.py from PATH or a local Docker image. '
        'To fix: \n'
        '  "apt install plaso-tools" or '
        '"docker pull log2timeline/plaso:latest"'),
                     error.exception.message)

if __name__ == '__main__':
  unittest.main()
