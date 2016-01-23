# Created by nibo at 2015-04-30
Feature: Process definition management API
  This tests the Optimal BPM process definition management API

  Scenario: A new process definition is created
    Given a new process definition is saved
    Then loading a process definition should return the same definition
    And a matching repository should be created

  Scenario: An existing process definition is saved
    Given a process definition is changed
    Then loading a process definition should return the same definition

  Scenario: An existing process definition is deleted
    Given a process definition is deleted
    Then the process definition should not exist
    And the repository should be deleted

  Scenario: A main process file is created
    Given A main process file is created
    Then A main process file must be found

  Scenario: A main process file is edited
    Given A main process file is edited
    Then A main process file must be changed